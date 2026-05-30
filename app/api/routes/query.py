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

from app.core.config import get_settings
from app.models.schemas import QueryRequest, QueryResponse
from app.services.llm_service import generate_legal_response

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()


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
        502: {"description": "LLM returned an invalid response"},
        500: {"description": "Internal server error"},
    },
)
async def legal_query(
    request_body: QueryRequest,
    raw_request: Request,
    authorization: Optional[str] = Header(None),
):
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
    retriever = getattr(raw_request.app.state, "retriever", None)

    if retriever is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Retrieval system not ready. Run etl_pipeline.py first.",
        )

    chunks, retrieval_note = retriever.retrieve(request_body.user_query, top_k=settings.BM25_TOP_K)

    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No relevant legal text found for your query. Try rephrasing.",
        )

    # ── LLM Generation ───────────────────────────────────────────────────────
    try:
        response_data = generate_legal_response(
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

    return QueryResponse(
        explanation=response_data.get("explanation", ""),
        citations=response_data.get("citations", []),
        suggested_next_steps=response_data.get("suggested_next_steps", []),
        retrieval_note=retrieval_note,
    )
