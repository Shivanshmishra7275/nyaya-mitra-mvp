"""
main.py
========
Nyaya Mitra — FastAPI Application Factory
-------------------------------------------
Responsibilities:
  • Creates the FastAPI app instance with metadata and lifespan management.
  • Registers the CORS middleware (open in dev, restricted in production).
  • Registers all routers (health, legal-query, document-draft).
  • Handles startup/shutdown: initializes ChromaDB and SQLite.

Usage (development):
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Usage (production with Gunicorn):
    gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import (
    APP_DESCRIPTION,
    APP_TITLE,
    APP_VERSION,
    CORS_ORIGINS,
    LOG_LEVEL,
    FASTAPI_ENV,
)
from db.chroma_client import ChromaDBClient
from db.sqlite_client import initialize_db
from routers import health, legal_query, document_draft

# ── Logging configuration ────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════════════════
# LIFESPAN MANAGER
# ════════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.

    STARTUP:
      1. Initialize SQLite (creates tables if not exist).
      2. Initialize ChromaDB client and load the legal corpus collection.

    SHUTDOWN:
      ChromaDB PersistentClient handles its own cleanup.
    """
    logger.info("=" * 60)
    logger.info("Nyaya Mitra API v%s starting up (%s)", APP_VERSION, FASTAPI_ENV)
    logger.info("=" * 60)

    # Initialize SQLite session/query log database
    initialize_db()

    # Initialize ChromaDB — non-fatal if corpus not yet populated
    try:
        ChromaDBClient.initialize()
        chunk_count = ChromaDBClient.get_chunk_count()
        if chunk_count == 0:
            logger.warning(
                "ChromaDB collection is empty. "
                "Run `python etl_pipeline.py` to ingest the legal PDF corpus."
            )
        else:
            logger.info("Vector store ready — %d legal chunks indexed.", chunk_count)
    except Exception as exc:
        logger.error(
            "ChromaDB initialization failed: %s. "
            "API will start in degraded mode — run etl_pipeline.py first.",
            exc,
        )

    logger.info("Nyaya Mitra API ready.")
    yield

    logger.info("Nyaya Mitra API shutting down.")


# ════════════════════════════════════════════════════════════════════════════
# APP FACTORY
# ════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS Middleware ──────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Router registration ───────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(legal_query.router)
app.include_router(document_draft.router)


@app.get("/", include_in_schema=False)
async def root():
    """Simple root endpoint used as a human-readable liveness check.

    Returns basic service metadata and helpful links for new developers.
    No database or vector-store calls are made here, so this path is safe
    for lightweight uptime checks and does not have side effects.
    """
    return {
        "service": "Nyaya Mitra API",
        "version": APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }