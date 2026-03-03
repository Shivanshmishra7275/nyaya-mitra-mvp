"""
routers/health.py
==================
Nyaya Mitra — Health Check and Corpus Stats Endpoints
"""

import logging

from fastapi import APIRouter

from config import APP_VERSION, EMBEDDING_MODEL, EMBEDDING_DIMENSIONS, CHROMA_COLLECTION_NAME
from db.chroma_client import ChromaDBClient
from models.response_models import HealthResponse, CorpusStatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
)
async def health_check() -> HealthResponse:
    """
    Returns service health status and vector store readiness.
    Used by load balancers, monitoring tools, and the mobile app startup check.
    """
    is_ready = ChromaDBClient.is_ready()
    chunk_count = ChromaDBClient.get_chunk_count()

    return HealthResponse(
        status="healthy" if is_ready else "degraded",
        vector_store="loaded" if is_ready else "not_loaded",
        chunks_indexed=chunk_count,
        embedding_model=EMBEDDING_MODEL,
        version=APP_VERSION,
    )


@router.get(
    "/api/v1/corpus-stats",
    response_model=CorpusStatsResponse,
    summary="Legal Corpus Statistics",
)
async def corpus_stats() -> CorpusStatsResponse:
    """
    Returns metadata about the loaded legal corpus.
    Displayed in the app's Settings screen and on the Corpus Info page.
    """
    collection = ChromaDBClient.get_collection() if ChromaDBClient.is_ready() else None

    if collection is None:
        return CorpusStatsResponse(
            total_chunks=0,
            sources={},
            embedding_model=EMBEDDING_MODEL,
            embedding_dimensions=EMBEDDING_DIMENSIONS,
            last_updated=None,
        )

    # Count chunks per source document
    source_counts: dict[str, int] = {}
    total = collection.count()

    # Sample up to 10,000 records to build source distribution
    # (For ~1700 chunks this is essentially all of them)
    if total > 0:
        sample_results = collection.get(
            limit=min(total, 10_000),
            include=["metadatas"],
        )
        for meta in sample_results.get("metadatas", []):
            if meta:
                src = meta.get("source", "unknown")
                source_counts[src] = source_counts.get(src, 0) + 1

    return CorpusStatsResponse(
        total_chunks=total,
        sources=source_counts,
        embedding_model=EMBEDDING_MODEL,
        embedding_dimensions=EMBEDDING_DIMENSIONS,
        last_updated=None,  # Phase 2: store ingestion timestamp in DB
    )
