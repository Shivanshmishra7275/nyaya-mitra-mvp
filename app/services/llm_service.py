"""
app/services/llm_service.py
============================
Handles all interaction with the Gemini LLM.

SECURITY NOTES:
  - The raw API key is NEVER logged. Only the first/last 4 chars are logged for audit.
  - The key is used per-request and discarded immediately after the call.
  - The key is never stored, cached, or returned in any response.

ASYNC NOTES:
  - `generate_legal_response` is a coroutine (async def).
  - The blocking Gemini SDK call is wrapped in asyncio.to_thread() so it does NOT
    block the event loop. With 2 Uvicorn workers, failing to do this would freeze
    all other requests for up to 60 seconds per LLM call.
  - The retry backoff uses asyncio.sleep(), not time.sleep().
"""
import asyncio
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


def _extract_json_from_response(raw_text: str) -> str:
    """
    Robustly extract JSON from an LLM response.
    Handles:
      - Clean JSON (ideal case)
      - ```json ... ``` fenced code blocks
      - ``` ... ``` fenced blocks
      - JSON embedded within surrounding text (thinking model verbosity)
    """
    raw_text = raw_text.strip()

    # 1. Try stripping markdown fences (most common case with Gemini Flash)
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned).strip()

    # 2. If it now starts with { it's probably clean JSON — try it directly
    if cleaned.startswith("{"):
        return cleaned

    # 3. Fallback: find the first { ... } block in the text
    # This handles thinking-mode responses that prepend verbose text
    match = re.search(r"\{.*\}", raw_text, re.DOTALL)
    if match:
        return match.group(0)

    # 4. Return as-is and let the caller handle the JSONDecodeError
    return raw_text


def _call_gemini_sync(client: genai.Client, prompt: str) -> str:
    """
    Synchronous Gemini call — intended to be run in a thread via asyncio.to_thread().
    Isolated here so the async wrapper stays clean.
    """
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config={"temperature": settings.LLM_TEMPERATURE},
    )
    return response.text


async def generate_legal_response(
    query: str,
    chunks: list[dict],
    api_key: str,
    max_retries: int = 2,
) -> dict:
    """
    Async coroutine — call Gemini with the constructed prompt and return parsed JSON.

    The blocking Gemini SDK call is offloaded to a thread pool via asyncio.to_thread()
    so it never stalls the event loop.

    Args:
        query:       The user's legal question (already validated).
        chunks:      Retrieved context chunks from the retriever.
        api_key:     The Gemini API key for this request (BYOK or server default).
                     NEVER logged in full.
        max_retries: Number of times to retry on transient failures.

    Returns:
        dict with keys: explanation, citations, suggested_next_steps

    Raises:
        ValueError: if the LLM returns invalid JSON after all retries.
        Exception:  propagated from Gemini SDK on non-transient API errors.
    """
    # Audit log — masked key only, never full key
    logger.info(
        "LLM call initiated. Model=%s Key=%s Chunks=%d",
        settings.GEMINI_MODEL,
        _mask_key(api_key),
        len(chunks),
    )

    client = genai.Client(api_key=api_key, http_options={"timeout": 60})
    prompt = build_prompt(query, chunks)

    last_exc = None
    for attempt in range(1, max_retries + 1):
        try:
            # Offload the blocking SDK call to a thread — does NOT block event loop
            raw_text = await asyncio.to_thread(_call_gemini_sync, client, prompt)

            if not raw_text:
                raise ValueError("LLM returned an empty response.")

            clean = _extract_json_from_response(raw_text)

            try:
                result = json.loads(clean)
            except json.JSONDecodeError as exc:
                logger.error(
                    "LLM output was not valid JSON (attempt %d/%d). Raw (first 300 chars): %.300s",
                    attempt, max_retries, clean,
                )
                raise ValueError(f"LLM returned malformed JSON: {exc}") from exc

            # Validate required keys are present
            required = {"explanation", "citations", "suggested_next_steps"}
            missing = required - result.keys()
            if missing:
                logger.warning(
                    "LLM JSON missing expected keys: %s. Filling with defaults.", missing
                )
                result.setdefault("explanation", "")
                result.setdefault("citations", [])
                result.setdefault("suggested_next_steps", [])

            logger.info("LLM call successful on attempt %d.", attempt)
            return result

        except ValueError as exc:
            # JSON parsing error — retry once with async backoff (does NOT block event loop)
            last_exc = exc  # store the instance, not the class
            if attempt < max_retries:
                logger.warning("Retrying LLM call in 2s (attempt %d/%d)...", attempt, max_retries)
                await asyncio.sleep(2)  # ← asyncio.sleep, not time.sleep
            continue

        except Exception as exc:
            # API errors (quota, auth, network) — don't retry, re-raise immediately
            logger.error("Gemini API error: %s", exc, exc_info=True)
            raise

    raise ValueError(f"LLM failed to return valid JSON after {max_retries} attempts.") from last_exc
