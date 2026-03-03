"""
models/request_models.py
=========================
Nyaya Mitra — Pydantic Request Schemas
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class LegalQueryRequest(BaseModel):
    """
    Request schema for POST /api/v1/legal-query.
    
    user_query  : The natural language legal question from the user.
    top_k       : Number of ChromaDB chunks to retrieve (default 15, max 30).
    session_id  : Optional client-provided session UUID for logging.
    """
    user_query: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="Natural language legal question (English)",
        examples=["What is the punishment for theft under BNS?"],
    )
    top_k: int = Field(
        default=15,
        ge=5,
        le=30,
        description="Number of context chunks to retrieve from ChromaDB",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Client session UUID for query logging",
    )


class DraftDocumentRequest(BaseModel):
    """
    Request schema for POST /api/v1/draft-document.
    
    document_type    : One of the supported legal document types.
    facts            : User-provided factual description (50–5000 chars).
    accused_name     : Name of the accused / respondent (optional).
    court            : Court name (optional, filled as placeholder if absent).
    sections_charged : List of legal sections e.g. ["BNS Section 303"].
    session_id       : Optional session UUID.
    """
    document_type: Literal[
        "bail_application",
        "anticipatory_bail",
        "fir_draft",
        "legal_notice",
        "complaint_letter",
    ] = Field(
        ...,
        description="Type of legal document to generate",
    )
    facts: str = Field(
        ...,
        min_length=50,
        max_length=5000,
        description="Factual description provided by the user / advocate",
    )
    accused_name: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Name of the accused or respondent",
    )
    court: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Name of the court (e.g., 'Sessions Court, New Delhi')",
    )
    sections_charged: Optional[list[str]] = Field(
        default_factory=list,
        description="List of charges (e.g., ['BNS Section 303', 'BNS Section 309'])",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Client session UUID",
    )
