"""
app/main.py
============
Nyaya Mitra — FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload                 (development)
    uvicorn app.main:app --host 0.0.0.0 --port 8000  (production)
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.routes import health as health_router
from app.api.routes import query as query_router
from app.api.routes import admin as admin_router
from app.core.config import get_settings
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever

# ---------------------------------------------------------------------------
# Rate limiter — shared singleton, mounted on app.state so routes can use it
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
import structlog
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup: load retrieval indexes.
    Shutdown: nothing to clean up for BM25 (in-memory).
    """
    logger.info("=== Nyaya Mitra API starting up (env=%s) ===", settings.APP_ENV)

    # Initialise BM25 retriever (always)
    bm25 = BM25Retriever(store_path=settings.VECTOR_STORE_PATH)
    ok = bm25.load()
    if not ok:
        logger.warning(
            "BM25 index NOT loaded. The /legal-query endpoint will return 503 "
            "until you run: python etl_pipeline.py"
        )

    # Optionally initialise Qdrant semantic retriever
    qdrant = None
    if settings.QDRANT_ENABLED:
        try:
            from app.retrieval.qdrant_retriever import QdrantRetriever
            qdrant = QdrantRetriever(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                collection=settings.QDRANT_COLLECTION,
            )
            ok = qdrant.load()
            if ok:
                logger.info("Qdrant semantic retriever loaded — hybrid mode active.")
            else:
                logger.warning(
                    "Qdrant retriever loaded but collection missing. "
                    "Run: python etl_pipeline.py --qdrant"
                )
                qdrant = None
        except Exception as exc:
            logger.warning("Qdrant init failed — using BM25-only: %s", exc)
            qdrant = None

    # Wire the hybrid retriever into app.state so routes can access it
    app.state.retriever = HybridRetriever(bm25=bm25, qdrant_retriever=qdrant)
    # Wire the rate limiter into app.state so the @limiter.limit decorator works
    app.state.limiter = limiter

    logger.info("=== Nyaya Mitra API ready ===")
    yield

    logger.info("=== Nyaya Mitra API shutting down ===")

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Nyaya Mitra — AI-powered legal assistant for Indian law. "
            "Covers BNS, BNSS, BSA, and the Constitution of India."
        ),
        lifespan=lifespan,
        docs_url="/docs" if settings.APP_ENV != "production" else None,
        redoc_url="/redoc" if settings.APP_ENV != "production" else None,
    )

    # ── Rate limiting ─────────────────────────────────────────────────────────
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── CORS ─────────────────────────────────────────────────────────────────
    # In development: allow all origins for convenience.
    # In production: restrict to specific frontend URLs via ALLOWED_ORIGINS env var.
    cors_origins = settings.cors_origins
    # NOTE: allow_credentials=True is NOT compatible with allow_origins=["*"]
    # per browser CORS spec. We handle this correctly here.
    use_credentials = cors_origins != ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=use_credentials,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    )

    # Trust X-Forwarded-For headers from the proxy (e.g., Render)
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

    # ── Routes ───────────────────────────────────────────────────────────────
    app.include_router(health_router.router, prefix="")
    app.include_router(query_router.router, prefix="/api/v1")
    app.include_router(admin_router.router, prefix="/api/v1/admin")

    return app

app = create_app()
