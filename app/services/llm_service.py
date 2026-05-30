"""
app/services/llm_service.py
============================
Handles all interaction with the Gemini LLM.

SECURITY NOTES:
  - The raw API key is NEVER logged. Only the first/last 4 chars are logged for audit.
  - The key is used per-request and discarded immediately after the call.
  - The key is never stored, cached, or returned in any response.
"""
import json
import logging
import re

from google import genai

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _mask_key(key: str) -> str:
    """Return a safely masked version of the key for audit logging."""
    if not key or len(key) < 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def build_prompt(query: str, chunks: list[dict]) -> str:
    """Construct the LLM prompt from retrieved legal context chunks."""
    context_parts = []
    for c in chunks:
        meta = c.get("metadata", {})
        source = meta.get("source", "Unknown")
        page = meta.get("page", "?")
        text = c.get("text", "")
        context_parts.append(f"Source: {source} (Page {page})\n{text}")

    context_text = "\n\n---\n\n".join(context_parts)

    return f"""You are Nyaya Mitra, an AI legal guide for Indian law.
Use ONLY the following legal context to answer the user's query.
Do not use any outside knowledge.

CONTEXT:
{context_text}

USER QUERY: {query}

DISCLAIMER: You are an AI assistant providing legal information, not legal advice.
Users should consult a qualified lawyer for their specific situation.

INSTRUCTIONS:
1. Base your answer strictly on the provided context.
2. Output your response as a valid, raw JSON object exactly matching this schema:
{{
    "explanation": "Clear, plain-language explanation of the law based on context.",
    "citations": ["List of sources (e.g., 'BNS Page 14')"],
    "suggested_next_steps": ["Actionable advice 1", "Actionable advice 2"]
}}
3. DO NOT wrap the JSON in markdown or code blocks. Return ONLY the raw JSON string.
4. If the context does not contain enough information, say so honestly in the explanation field.
"""


def _clean_json_response(raw_text: str) -> str:
    """Strip markdown code fences if the LLM adds them despite instructions."""
    raw_text = raw_text.strip()
    # Remove ```json ... ``` or ``` ... ```
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
    raw_text = re.sub(r"\s*```$", "", raw_text)
    return raw_text.strip()


def generate_legal_response(query: str, chunks: list[dict], api_key: str) -> dict:
    """
    Call Gemini with the constructed prompt and return parsed JSON.

    Args:
        query:   The user's legal question (already validated).
        chunks:  Retrieved context chunks from the retriever.
        api_key: The Gemini API key for this request (BYOK or server default).
                 NEVER logged in full.

    Returns:
        dict with keys: explanation, citations, suggested_next_steps

    Raises:
        ValueError: if the LLM returns invalid JSON.
        Exception: propagated from Gemini SDK on API errors.
    """
    # Audit log — masked key only, never full key
    logger.info(
        "LLM call initiated. Model=%s Key=%s Chunks=%d",
        settings.GEMINI_MODEL,
        _mask_key(api_key),
        len(chunks),
    )

    client = genai.Client(api_key=api_key)
    prompt = build_prompt(query, chunks)

    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config={"temperature": settings.LLM_TEMPERATURE},
    )

    raw_text = response.text
    if not raw_text:
        raise ValueError("LLM returned an empty response.")

    clean = _clean_json_response(raw_text)

    try:
        return json.loads(clean)
    except json.JSONDecodeError as exc:
        logger.error("LLM output was not valid JSON. Raw (first 200 chars): %.200s", clean)
        raise ValueError(f"LLM returned malformed JSON: {exc}") from exc
