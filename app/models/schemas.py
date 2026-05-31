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


class StrategyPath(BaseModel):
    """A single potential legal strategy or action path."""
    path_name: str = Field(description="Name of the strategy (e.g., 'Anticipatory Bail Route')")
    when_suitable: str = Field(description="When this path is most appropriate.")
    benefit: str = Field(description="Primary benefit of this path.")
    risk: str = Field(description="Primary risk or downside of this path.")


class QueryResponse(BaseModel):
    """Structured response for the Criminal Case Intelligence Assistant."""
    legal_mapping: list[str] = Field(
        default_factory=list,
        description="Applicable legal sections (e.g., BNS Section 378).",
    )
    explanation: str = Field(
        description="Plain-language explanation of how the law applies to the facts."
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Identified weak points, missing evidence, or loopholes in the user's facts.",
    )
    strategy_paths: list[StrategyPath] = Field(
        default_factory=list,
        description="Multiple strategic options for the user.",
    )
    lawyer_brief: str = Field(
        description="A concise, structured summary designed to be handed to a lawyer.",
    )
    citations: list[str] = Field(
        default_factory=list,
        description="List of cited source references.",
    )
    retrieval_note: Optional[str] = Field(
        None,
        description="Note about retrieval quality.",
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
