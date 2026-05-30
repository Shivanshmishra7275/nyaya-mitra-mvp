"""
app/models/schemas.py
=====================
All Pydantic request and response models for the Nyaya Mitra API.
"""
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """Request body for the legal query endpoint."""

    user_query: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="The legal question from the user.",
        examples=["What is the punishment for theft under BNS?"],
    )

    @field_validator("user_query")
    @classmethod
    def strip_and_validate(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty or whitespace only.")
        return v


class Citation(BaseModel):
    """A single citation/source reference."""
    source: str = Field(description="Source document name, e.g. 'BNS'")
    page: Optional[int] = Field(None, description="Page number, 0-indexed")
    snippet: Optional[str] = Field(None, description="Short text snippet from the source")


class QueryResponse(BaseModel):
    """Structured response from the legal query endpoint."""
    explanation: str = Field(description="Plain-language explanation of the law.")
    citations: list[str] = Field(
        default_factory=list,
        description="List of cited source references.",
    )
    suggested_next_steps: list[str] = Field(
        default_factory=list,
        description="Actionable next steps for the user.",
    )
    retrieval_note: Optional[str] = Field(
        None,
        description="Note about retrieval quality (e.g., BM25-only vs hybrid).",
    )


class HealthResponse(BaseModel):
    """Response for the /health endpoint."""
    status: str
    version: str
    retrieval_mode: str
    chunks_loaded: int


class ErrorResponse(BaseModel):
    """Standard error response shape."""
    detail: str
    error_code: Optional[str] = None
