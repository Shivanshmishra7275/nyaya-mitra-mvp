"""
app/api/routes/admin.py
========================
Admin and debug endpoints for verifying retrieval corpus readiness.
"""
import random
from fastapi import APIRouter, Request
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/debug/corpus", tags=["Admin"])
async def debug_corpus(request: Request):
    """
    Returns statistics about the currently loaded retrieval corpus.
    Provides a quick way to verify that PDFs were parsed and loaded correctly
    in the production environment.
    """
    retriever = getattr(request.app.state, "retriever", None)
    if not retriever:
        return {"error": "Retrieval system not initialized."}

    bm25 = getattr(retriever, "_bm25", None)
    if not bm25 or not bm25.is_ready:
        return {"error": "BM25 index not loaded. Run etl_pipeline.py"}

    chunk_count = bm25.chunk_count

    # Extract unique sources
    sources = set()
    sample_chunk = None
    if chunk_count > 0:
        sample_idx = random.randint(0, chunk_count - 1)
        sample_chunk = bm25._chunks[sample_idx]
        for chunk in bm25._chunks:
            source = chunk.get("metadata", {}).get("source")
            if source:
                sources.add(source)

    qdrant = getattr(retriever, "_qdrant", None)
    qdrant_status = "Not configured"
    if qdrant:
        qdrant_status = "Ready" if qdrant.is_ready else "Error/Not Loaded"

    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "retriever_mode": "Hybrid" if qdrant and qdrant.is_ready else "BM25-only",
        "corpus_stats": {
            "total_chunks": chunk_count,
            "unique_sources_detected": sorted(list(sources)),
        },
        "qdrant_status": qdrant_status,
        "sample_chunk_preview": {
            "text": sample_chunk["text"][:150] + "..." if sample_chunk else None,
            "metadata": sample_chunk["metadata"] if sample_chunk else None,
        },
    }


@router.get("/debug/config", tags=["Admin"])
async def debug_config():
    """
    Returns non-sensitive configuration values for debugging.
    Never exposes API keys or secrets.
    """
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "app_env": settings.APP_ENV,
        "gemini_model": settings.GEMINI_MODEL,
        "llm_temperature": settings.LLM_TEMPERATURE,
        "bm25_top_k": settings.BM25_TOP_K,
        "vector_store_path": settings.VECTOR_STORE_PATH,
        "qdrant_enabled": settings.QDRANT_ENABLED,
        "qdrant_host": settings.QDRANT_HOST if settings.QDRANT_ENABLED else "N/A",
        "qdrant_port": settings.QDRANT_PORT if settings.QDRANT_ENABLED else "N/A",
        "qdrant_collection": settings.QDRANT_COLLECTION if settings.QDRANT_ENABLED else "N/A",
        "cors_origins": settings.cors_origins,
        # Key presence only — never the actual key value
        "server_api_key_set": bool(settings.GEMINI_API_KEY),
    }
