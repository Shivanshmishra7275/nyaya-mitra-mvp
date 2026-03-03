"""
models/response_models.py
==========================
Nyaya Mitra — Pydantic Response Schemas
"""

from typing import Optional
from pydantic import BaseModel, Field


class LegalQueryResponse(BaseModel):
    """
    Response schema for POST /api/v1/legal-query.
    
    explanation         : Plain-language legal explanation grounded in corpus.
    citations           : List of cited sources, e.g. "BNS — Section 303, Page 87".
    suggested_next_steps: Actionable advice for the user.
    disclaimer          : Mandatory legal disclaimer.
    latency_ms          : Total server-side processing time in milliseconds.
    """
    explanation: str = Field(
        ...,
        description="Plain-language legal explanation",
    )
    citations: list[str] = Field(
        default_factory=list,
        description="List of law citations used in the response",
    )
    suggested_next_steps: list[str] = Field(
        default_factory=list,
        description="Actionable next steps for the user",
    )
    disclaimer: str = Field(
        ...,
        description="Mandatory legal information disclaimer",
    )
    latency_ms: Optional[int] = Field(
        default=None,
        description="Total server-side latency in milliseconds",
    )


class DraftDocumentResponse(BaseModel):
    """
    Response schema for POST /api/v1/draft-document.
    """
    document_type: str = Field(..., description="Type of document generated")
    accused_name: Optional[str] = None
    court: Optional[str] = None
    draft_content: str = Field(..., description="Complete generated legal document text")
    citations_used: list[str] = Field(
        default_factory=list,
        description="Legal sections cited in the draft",
    )
    disclaimer: str = Field(..., description="Mandatory draft disclaimer")
    latency_ms: Optional[int] = None


class HealthResponse(BaseModel):
    """Response schema for GET /health."""
    status: str
    vector_store: str              # "loaded" | "not_loaded"
    chunks_indexed: int
    embedding_model: str
    version: str


class CorpusStatsResponse(BaseModel):
    """Response schema for GET /api/v1/corpus-stats."""
    total_chunks: int
    sources: dict[str, int]        # {"bns.pdf": 423, ...}
    embedding_model: str
    embedding_dimensions: int
    last_updated: Optional[str]
