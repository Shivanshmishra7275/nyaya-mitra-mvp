"""
routers/legal_query.py
=======================
Nyaya Mitra — Legal Q&A Router
--------------------------------
Handles POST /api/v1/legal-query — the core RAG pipeline endpoint.

Flow:
  Request → Validate (Pydantic) → ChromaDB Retrieval → Gemini Generation → Response
"""

import json
import logging
import time
import uuid

from fastapi import APIRouter, HTTPException, status

from config import LEGAL_DISCLAIMER
from db.chroma_client import ChromaDBClient
from db.sqlite_client import create_session, log_query
from models.request_models import LegalQueryRequest
from models.response_models import LegalQueryResponse
from services.rag_service import retrieve_context, assemble_context
from services.gemini_service import generate_legal_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Legal Q&A"])


@router.post(
    "/legal-query",
    response_model=LegalQueryResponse,
    summary="Legal Q&A (RAG Pipeline)",
    description=(
        "Performs semantic retrieval over the Indian legal corpus (ChromaDB) "
        "then generates a structured, citation-grounded response via Gemini 2.5 Flash."
    ),
)
async def legal_query(request: LegalQueryRequest) -> LegalQueryResponse:
    """
    Core RAG endpoint.

    1. Check ChromaDB is ready.
    2. Retrieve top_k semantically similar chunks.
    3. Assemble context string.
    4. Generate response via Gemini.
    5. Validate and return structured JSON.
    """
    start_time = time.monotonic()

    logger.info("Legal query received: '%.80s...'", request.user_query)

    # ── Guard: Vector store must be loaded ──────────────────────────────────
    if not ChromaDBClient.is_ready():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Knowledge base is not initialized. "
                "Run etl_pipeline.py to populate the vector store, then restart."
            ),
        )

    # ── Session management ───────────────────────────────────────────────────
    session_id = request.session_id or str(uuid.uuid4())
    create_session(session_id)

    # ── Step 1: ChromaDB semantic retrieval ─────────────────────────────────
    try:
        chunks = retrieve_context(request.user_query, top_k=request.top_k)
    except Exception as exc:
        logger.error("ChromaDB retrieval failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector search service is temporarily unavailable.",
        )

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No relevant legal information found for this query.",
        )

    # ── Step 2: Assemble context string ─────────────────────────────────────
    legal_context = assemble_context(chunks)

    # ── Step 3: Gemini generation ────────────────────────────────────────────
    try:
        response_data = generate_legal_response(
            user_query=request.user_query,
            legal_context=legal_context,
        )
    except json.JSONDecodeError as exc:
        logger.error("Gemini output was not valid JSON: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI service returned an unstructured response. Please retry.",
        )
    except Exception as exc:
        logger.error("Gemini API error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI generation failed: {str(exc)[:200]}",
        )

    # ── Step 4: Build response ───────────────────────────────────────────────
    latency_ms = int((time.monotonic() - start_time) * 1000)

    response = LegalQueryResponse(
        explanation=response_data.get("explanation", "No explanation generated."),
        citations=response_data.get("citations", []),
        suggested_next_steps=response_data.get("suggested_next_steps", []),
        disclaimer=response_data.get("disclaimer", LEGAL_DISCLAIMER),
        latency_ms=latency_ms,
    )

    # ── Step 5: Log to SQLite (non-blocking) ─────────────────────────────────
    log_query(
        session_id=session_id,
        query_text=request.user_query,
        response_json=response.model_dump_json(),
        latency_ms=latency_ms,
    )

    logger.info(
        "Legal query completed | latency=%dms | citations=%d",
        latency_ms,
        len(response.citations),
    )
    return response
