"""
app/models/schemas.py
=====================
All Pydantic request and response models for the Nyaya Mitra API.
"""
from typing import Optional, Literal
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


class Confidence(BaseModel):
    """Confidence signal for the response, grounded in retrieval quality."""
    label: str = Field(description="Low / Medium / High")
    reason: str = Field(description="Reason for the confidence level")


class QueryResponse(BaseModel):
    """Structured response for the Criminal Case Intelligence Assistant."""
    # New structured fields (Phase 1+)
    answer: str = Field(
        default="",
        description="Primary plain-language answer summary.",
    )
    legal_gps: str = Field(
        default="",
        description="Plain-language orientation of where the user stands procedurally.",
    )
    issue_graph: list[str] = Field(
        default_factory=list,
        description="Key legal issue nodes detected from the user's facts.",
    )
    opposition_view: list[str] = Field(
        default_factory=list,
        description="How the other side/police/court might argue or inspect the matter.",
    )
    strategy_tree: list[StrategyPath] = Field(
        default_factory=list,
        description="Structured strategy options with tradeoffs.",
    )
    confidence: Optional[Confidence] = Field(
        None,
        description="Confidence label and reason grounded in retrieval quality.",
    )
    next_actions: list[str] = Field(
        default_factory=list,
        description="Actionable immediate steps for the user.",
    )
    scope_status: Literal["in_scope", "partial_scope", "out_of_scope"] = Field(
        default="in_scope",
        description="Scope classification for Indian criminal-law coverage.",
    )

    # Backward-compatible fields (existing UI depends on these)
    legal_mapping: list[str] = Field(
        default_factory=list,
        description="Applicable legal sections (e.g., BNS Section 378).",
    )
    explanation: str = Field(
        default="",
        description="Plain-language explanation of how the law applies to the facts.",
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
        default="",
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
