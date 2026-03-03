"""
services/drafting_service.py
=============================
Nyaya Mitra — Document Drafting Orchestration Service
-------------------------------------------------------
Handles:
  1. Loading template files for each supported document type.
  2. Building retrieval queries tailored to each document type.
  3. Orchestrating the full draft generation pipeline.
  4. Extracting and returning citations from the generated draft.
"""

import logging
import re
from datetime import date
from pathlib import Path
from typing import Optional

from config import TEMPLATES_DIR
from services.rag_service import retrieve_context, assemble_context
from services.gemini_service import generate_draft_document

logger = logging.getLogger(__name__)


# ── Template-to-search-query mapping ─────────────────────────────────────────
# Each document type has an optimized retrieval query that ensures the most
# relevant legal provisions are retrieved from ChromaDB for that document.
DRAFTING_RETRIEVAL_QUERIES: dict[str, str] = {
    "bail_application":    "bail application conditions grounds BNSS Section 480 483",
    "anticipatory_bail":   "anticipatory bail Section 482 BNSS apprehension arrest",
    "fir_draft":           "FIR first information report complaint BNSS Section 173 175",
    "legal_notice":        "legal notice demand criminal procedure BNS civil remedy",
    "complaint_letter":    "complaint to senior police officer Superintendent BNSS cognizable",
}

# Display names for document types (used in responses and UI)
DOCUMENT_TYPE_LABELS: dict[str, str] = {
    "bail_application":    "Bail Application",
    "anticipatory_bail":   "Anticipatory Bail Application",
    "fir_draft":           "FIR Draft",
    "legal_notice":        "Legal Notice",
    "complaint_letter":    "Complaint Letter",
}


def load_template(document_type: str) -> str:
    """
    Loads the text template for the given document type from the /templates directory.

    Args:
        document_type: One of the supported document type keys.

    Returns:
        Template string content.

    Raises:
        FileNotFoundError: If the template file is missing.
    """
    template_path: Path = TEMPLATES_DIR / f"{document_type}.txt"

    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found for document type '{document_type}' at: {template_path}"
        )

    return template_path.read_text(encoding="utf-8")


def generate_draft(
    document_type: str,
    facts: str,
    accused_name: Optional[str],
    court: Optional[str],
    sections_charged: list[str],
) -> dict:
    """
    Orchestrates the full draft generation pipeline:
      1. Retrieve relevant legal provisions from ChromaDB.
      2. Assemble context string.
      3. Load document template.
      4. Call Gemini to generate the draft.
      5. Extract citations from the generated text.

    Args:
        document_type:    Supported document type key.
        facts:            User-provided factual description.
        accused_name:     Name of the accused (optional).
        court:            Court name (optional).
        sections_charged: List of legal sections (optional).

    Returns:
        Dict with keys: draft_content, citations_used.
    """
    # Step 1: Retrieve relevant legal provisions
    retrieval_query = DRAFTING_RETRIEVAL_QUERIES.get(
        document_type,
        f"{document_type} legal provisions India",
    )
    logger.info("Retrieving legal provisions for '%s'", document_type)
    chunks = retrieve_context(retrieval_query, top_k=10)
    legal_context = assemble_context(chunks)

    # Step 2: Load template
    template_content = load_template(document_type)

    # Step 3: Generate draft via Gemini
    today_str = date.today().strftime("%d %B %Y")
    draft_content = generate_draft_document(
        legal_context=legal_context,
        template_content=template_content,
        user_facts=facts,
        accused_name=accused_name or "[ACCUSED/APPLICANT NAME]",
        court_name=court or "[COURT NAME]",
        sections_charged=sections_charged,
        today_date=today_str,
    )

    # Step 4: Extract citations from the generated draft
    citations = _extract_citations(draft_content)

    return {
        "draft_content": draft_content,
        "citations_used": citations,
    }


def _extract_citations(draft_text: str) -> list[str]:
    """
    Extracts law citations from a generated draft text using regex.

    Matches patterns like:
      - "Section 480 of BNSS"
      - "BNS Section 303"
      - "BNSS Section 480"
      - "Article 21 of the Constitution"
    """
    patterns = [
        r'(?:BNS|BNSS|BSA)\s+(?:Section|Sec\.?)\s+\d+[A-Z]?',
        r'Section\s+\d+[A-Z]?\s+of\s+(?:the\s+)?(?:BNS|BNSS|BSA|Constitution)',
        r'Article\s+\d+[A-Z]?\s+of\s+the\s+Constitution',
    ]

    citations: list[str] = []
    seen: set[str] = set()

    for pattern in patterns:
        for match in re.finditer(pattern, draft_text, re.IGNORECASE):
            citation = match.group().strip()
            normalized = " ".join(citation.split())  # collapse whitespace
            if normalized not in seen:
                seen.add(normalized)
                citations.append(normalized)

    return citations
