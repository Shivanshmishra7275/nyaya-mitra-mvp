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

from app.api.routes import health as health_router
from app.api.routes import query as query_router
from app.core.config import get_settings
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)
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

    # ── Routes ───────────────────────────────────────────────────────────────
    app.include_router(health_router.router, prefix="")
    app.include_router(query_router.router, prefix="/api/v1")

    return app


app = create_app()
