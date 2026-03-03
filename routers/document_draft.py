"""
routers/document_draft.py
==========================
Nyaya Mitra — Document Drafting Router
----------------------------------------
Handles POST /api/v1/draft-document — AI-powered legal document generation.
"""

import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, status

from config import LEGAL_DISCLAIMER
from db.chroma_client import ChromaDBClient
from db.sqlite_client import create_session, log_draft
from models.request_models import DraftDocumentRequest
from models.response_models import DraftDocumentResponse
from services.drafting_service import generate_draft, DOCUMENT_TYPE_LABELS

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Document Drafting"])

DRAFT_DISCLAIMER = (
    "⚠️ AI-generated legal draft. This document must be reviewed, verified, "
    "and signed by a registered advocate before filing in any court. "
    "Nyaya Mitra is not responsible for the outcome of any legal proceeding "
    "based on this draft. Confidentiality of your facts is maintained."
)


@router.post(
    "/draft-document",
    response_model=DraftDocumentResponse,
    summary="AI Legal Document Drafting",
    description=(
        "Generates a court-ready legal document draft by combining "
        "user-provided facts with retrieved BNS/BNSS/BSA provisions and Gemini generation."
    ),
)
async def draft_document(request: DraftDocumentRequest) -> DraftDocumentResponse:
    """
    Document drafting endpoint.

    1. Check ChromaDB is ready.
    2. Retrieve legal provisions relevant to the document type.
    3. Load document template.
    4. Generate draft via Gemini.
    5. Extract citations from generated text.
    6. Return structured draft response.
    """
    start_time = time.monotonic()

    logger.info(
        "Draft request received | type='%s' | accused='%s'",
        request.document_type,
        request.accused_name or "not provided",
    )

    # ── Guard: Vector store must be loaded ──────────────────────────────────
    if not ChromaDBClient.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Legal knowledge base is not initialized. "
                "Run etl_pipeline.py and restart the server."
            ),
        )

    # ── Session management ───────────────────────────────────────────────────
    session_id = request.session_id or str(uuid.uuid4())
    create_session(session_id)

    # ── Generate draft ───────────────────────────────────────────────────────
    try:
        result = generate_draft(
            document_type=request.document_type,
            facts=request.facts,
            accused_name=request.accused_name,
            court=request.court,
            sections_charged=request.sections_charged or [],
        )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("Draft generation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Document generation failed: {str(exc)[:200]}",
        )

    # ── Build response ───────────────────────────────────────────────────────
    latency_ms = int((time.monotonic() - start_time) * 1000)
    doc_label = DOCUMENT_TYPE_LABELS.get(request.document_type, request.document_type)

    response = DraftDocumentResponse(
        document_type=doc_label,
        accused_name=request.accused_name,
        court=request.court,
        draft_content=result["draft_content"],
        citations_used=result["citations_used"],
        disclaimer=DRAFT_DISCLAIMER,
        latency_ms=latency_ms,
    )

    # ── Log to SQLite ─────────────────────────────────────────────────────────
    log_draft(
        session_id=session_id,
        document_type=request.document_type,
        accused_name=request.accused_name,
        input_facts=request.facts,
        output_draft=result["draft_content"],
        latency_ms=latency_ms,
    )

    logger.info(
        "Draft completed | type='%s' | latency=%dms | citations=%d",
        request.document_type,
        latency_ms,
        len(response.citations_used),
    )
    return response
