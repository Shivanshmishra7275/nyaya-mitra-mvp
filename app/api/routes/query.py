"""
app/api/routes/query.py
========================
The core legal query endpoint.

BYOK Flow (Bring Your Own Key):
  1. Frontend sends user API key in `Authorization: Bearer <key>` header.
  2. This endpoint extracts and validates it per-request.
  3. Key is passed directly to llm_service.generate_legal_response().
  4. Key is NEVER stored, cached, logged in full, or returned.
  5. If no BYOK key, falls back to server-side GEMINI_API_KEY env var.
  6. If neither exists, returns 401 with a clear actionable message.
"""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import get_settings
from app.models.schemas import QueryRequest, QueryResponse
from app.services.llm_service import (
    generate_legal_response,
    is_clear_out_of_scope,
    build_out_of_scope_response,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()
# Reuse the limiter singleton registered on app.state in main.py
limiter = Limiter(key_func=get_remote_address)


def _extract_api_key(authorization: Optional[str]) -> Optional[str]:
    """
    Extract the bearer token from the Authorization header.
    Returns None if header is absent or malformed.
    The raw key is never logged here.
    """
    if not authorization:
        return None
    if authorization.startswith("Bearer "):
        key = authorization[7:].strip()
        return key if key else None
    return None


@router.post(
    "/legal-query",
    response_model=QueryResponse,
    summary="Ask a legal question",
    description=(
        "Send a legal question in plain language. "
        "Provide your Gemini API key via `Authorization: Bearer <key>` header "
        "if the server has no default key configured."
    ),
    responses={
        401: {"description": "No API key provided"},
        404: {"description": "No relevant legal text found"},
        422: {"description": "Request validation error"},
        429: {"description": "Rate limit exceeded"},
        502: {"description": "LLM returned an invalid response"},
        500: {"description": "Internal server error"},
    },
)
@limiter.limit(lambda: f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def legal_query(
    request_body: QueryRequest,
    request: Request,
    authorization: Optional[str] = Header(None),
):
    # ── Early scope check (skip retrieval + key if clearly out of scope) ─────
    if is_clear_out_of_scope(request_body.user_query):
        response_data = build_out_of_scope_response(request_body.user_query)
        return QueryResponse(
            answer=response_data.get("answer", ""),
            legal_gps=response_data.get("legal_gps", ""),
            issue_graph=response_data.get("issue_graph", []),
            opposition_view=response_data.get("opposition_view", []),
            strategy_tree=response_data.get("strategy_tree", []),
            confidence=response_data.get("confidence"),
            next_actions=response_data.get("next_actions", []),
            scope_status=response_data.get("scope_status", "out_of_scope"),
            legal_mapping=response_data.get("legal_mapping", []),
            explanation=response_data.get("explanation", ""),
            weaknesses=response_data.get("weaknesses", []),
            strategy_paths=response_data.get("strategy_paths", []),
            lawyer_brief=response_data.get("lawyer_brief", ""),
            citations=response_data.get("citations", []),
            retrieval_note="Out of scope query. Retrieval skipped.",
        )

    # ── Resolve API key: BYOK takes priority over server default ─────────────
    api_key = _extract_api_key(authorization) or settings.GEMINI_API_KEY

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "No Gemini API key provided. "
                "Pass your key via 'Authorization: Bearer <your_key>' header, "
                "or configure GEMINI_API_KEY on the server."
            ),
        )

    # ── Retrieval ─────────────────────────────────────────────────────────────
    retriever = getattr(request.app.state, "retriever", None)

    if retriever is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retrieval system not ready. Run etl_pipeline.py first.",
        )

    chunks, retrieval_note = retriever.retrieve(request_body.user_query, top_k=settings.BM25_TOP_K)

    if not chunks:
        response_data = {
            "scope_status": "partial_scope",
            "answer": (
                "I could not find relevant BNS/BNSS/BSA sections for this query in the current corpus. "
                "Try rephrasing with specific criminal-law facts, dates, and actions."
            ),
            "legal_gps": "No Relevant Law Found",
            "confidence": {
                "label": "Low",
                "reason": "No relevant act text was retrieved for this query.",
            },
            "next_actions": [
                "Rephrase with clearer criminal-law facts and a timeline.",
                "Consult a qualified lawyer for urgent matters.",
            ],
            "explanation": "No relevant legal text could be matched to your facts.",
        }
        return QueryResponse(
            answer=response_data.get("answer", ""),
            legal_gps=response_data.get("legal_gps", ""),
            issue_graph=[],
            opposition_view=[],
            strategy_tree=[],
            confidence=response_data.get("confidence"),
            next_actions=response_data.get("next_actions", []),
            scope_status="partial_scope",
            legal_mapping=[],
            explanation=response_data.get("explanation", ""),
            weaknesses=[],
            strategy_paths=[],
            lawyer_brief="",
            citations=[],
            retrieval_note="No relevant act text found in the current corpus.",
        )

    # ── LLM Generation ───────────────────────────────────────────────────────
    try:
        response_data = await generate_legal_response(
            query=request_body.user_query,
            chunks=chunks,
            api_key=api_key,
        )
    except ValueError as exc:
        logger.error("LLM returned invalid response: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI model returned an invalid response format. Please try again.",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected LLM error: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while generating the response.",
        ) from exc

    answer = response_data.get("answer") or response_data.get("explanation", "")
    explanation = response_data.get("explanation") or answer
    strategy_tree = response_data.get("strategy_tree") or response_data.get("strategy_paths", [])
    strategy_paths = response_data.get("strategy_paths") or strategy_tree

    return QueryResponse(
        # New structured fields
        answer=answer,
        legal_gps=response_data.get("legal_gps", ""),
        issue_graph=response_data.get("issue_graph", []),
        opposition_view=response_data.get("opposition_view", []),
        strategy_tree=strategy_tree,
        confidence=response_data.get("confidence"),
        next_actions=response_data.get("next_actions", []),
        scope_status=response_data.get("scope_status", "in_scope"),

        # Backward-compatible fields
        legal_mapping=response_data.get("legal_mapping", []),
        explanation=explanation,
        weaknesses=response_data.get("weaknesses", []),
        strategy_paths=strategy_paths,
        lawyer_brief=response_data.get("lawyer_brief", ""),
        citations=response_data.get("citations", []),
        retrieval_note=retrieval_note,
    )
