"""
app/api/routes/health.py
=========================
Health and version endpoints for infrastructure monitoring and deployment checks.
"""
from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.models.schemas import HealthResponse

router = APIRouter()
settings = get_settings()

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check(request: Request):
    """
    Returns application health status.
    Used by Docker, Render, and load balancers for readiness checks.
    """
    retriever = getattr(request.app.state, "retriever", None)
    bm25 = getattr(retriever, "_bm25", None) if retriever else None

    # Return 503 if BM25 is not ready — signals Render/load balancers to stop routing
    if not bm25 or not bm25.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retrieval system not ready. Run etl_pipeline.py first.",
        )

    chunks_loaded = bm25.chunk_count
    qdrant_ready = getattr(retriever, "_qdrant", None) is not None

    retrieval_mode = "Hybrid (BM25 + Semantic)" if qdrant_ready else "BM25-only"

    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        retrieval_mode=retrieval_mode,
        chunks_loaded=chunks_loaded,
    )

@router.get("/version", tags=["System"])
async def version():
    """Returns the API version string."""
    return {"name": settings.APP_NAME, "version": settings.APP_VERSION, "env": settings.APP_ENV}
