"""
services/rag_service.py
========================
Nyaya Mitra — RAG Retrieval Service
--------------------------------------
Handles:
  1. Encoding user queries using SentenceTransformer (all-MiniLM-L6-v2).
  2. Semantic search over ChromaDB (K=15 by default).
  3. Assembling retrieved chunks into a structured context string for Gemini.

Design note:
  The embedding model is loaded ONCE at module import time and reused for
  all requests. Loading it per-request would add ~2–3 seconds of startup
  latency to every query.
"""

import logging
import re
from typing import Optional

from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, RAG_TOP_K, LAW_CODE_MAP
from db.chroma_client import ChromaDBClient

logger = logging.getLogger(__name__)

# ── Singleton Embedding Model ────────────────────────────────────────────────
# Loaded once when the module is first imported (during FastAPI startup).
# The model download is cached by sentence_transformers in ~/.cache/
logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
_embedding_model = SentenceTransformer(EMBEDDING_MODEL)
logger.info("Embedding model loaded successfully.")


def retrieve_context(query: str, top_k: int = RAG_TOP_K) -> list[dict]:
    """
    Performs semantic search over the ChromaDB legal corpus.

    Steps:
      1. Encodes the query string into a 384-dim embedding vector.
      2. Queries ChromaDB for the top_k most similar document chunks.
      3. Returns a list of dicts, each with 'document' and 'metadata' keys.

    Args:
        query:  Natural language legal query from the user.
        top_k:  Number of chunks to retrieve (default from config.RAG_TOP_K).

    Returns:
        List of chunk dicts: [{"document": str, "metadata": {...}}, ...]

    Raises:
        RuntimeError: If ChromaDB collection is not initialized.
    """
    collection = ChromaDBClient.get_collection()

    # Encode the query to a vector (returns numpy array → convert to plain list)
    query_embedding: list[float] = _embedding_model.encode(query).tolist()

    # Perform ANN search in ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),   # Guard against empty collection
        include=["documents", "metadatas", "distances"],
    )

    # ChromaDB returns nested lists (one sublist per query batch)
    documents  = results.get("documents", [[]])[0]
    metadatas  = results.get("metadatas", [[]])[0]
    distances  = results.get("distances", [[]])[0]

    # Zip into structured chunk dicts for consumption by the Gemini service
    chunks = [
        {
            "document": doc,
            "metadata": meta,
            "similarity": round(1 - dist, 4),  # cosine distance → similarity score
        }
        for doc, meta, dist in zip(documents, metadatas, distances)
    ]

    logger.info(
        "Retrieved %d chunks for query (top similarity: %.3f)",
        len(chunks),
        chunks[0]["similarity"] if chunks else 0,
    )
    return chunks


def assemble_context(chunks: list[dict]) -> str:
    """
    Formats a list of retrieved chunks into a structured context string
    suitable for injection into the Gemini prompt.

    Format per chunk:
        [N] Source: bns.pdf | Page: 87 | Law: BNS | Relevance: 0.892
        ---
        <raw chunk text>

    Args:
        chunks: List of chunk dicts from retrieve_context().

    Returns:
        Formatted multi-chunk context string.
    """
    parts: list[str] = []

    for i, chunk in enumerate(chunks, start=1):
        meta     = chunk.get("metadata", {})
        source   = meta.get("source", "unknown")
        page     = meta.get("page", "?")
        law_code = meta.get("law_code", _infer_law_code(source))
        similarity = chunk.get("similarity", 0.0)

        header = (
            f"[{i}] Source: {source} | Page: {page} | "
            f"Law: {law_code} | Relevance: {similarity:.3f}"
        )
        text = chunk.get("document", "").strip()
        parts.append(f"{header}\n---\n{text}")

    return "\n\n".join(parts)


def _infer_law_code(source_filename: str) -> str:
    """
    Derives the human-readable law code from the PDF filename stem.
    e.g. 'bns.pdf' → 'BNS', 'const.pdf' → 'Constitution'
    """
    stem = source_filename.lower().replace(".pdf", "")
    return LAW_CODE_MAP.get(stem, stem.upper())


def extract_citations_from_chunks(chunks: list[dict]) -> list[str]:
    """
    Constructs citation strings from chunk metadata.
    Used as a fallback if Gemini's JSON does not include citations.

    Returns list like: ["BNS — Section 303, Page 87"]
    """
    citations: list[str] = []
    seen: set[str] = set()

    for chunk in chunks:
        meta     = chunk.get("metadata", {})
        source   = meta.get("source", "unknown")
        page     = meta.get("page", "?")
        law_code = meta.get("law_code", _infer_law_code(source))

        # Attempt to extract section number from chunk text
        section_match = re.search(
            r'(?:Section|Sec\.?)\s+(\d+[A-Z]?)',
            chunk.get("document", ""),
            re.IGNORECASE,
        )
        if section_match:
            section = section_match.group(1)
            citation = f"{law_code} — Section {section}, Page {page}"
        else:
            citation = f"{law_code} — Page {page}"

        if citation not in seen:
            seen.add(citation)
            citations.append(citation)

    return citations[:5]  # Cap at 5 citations to avoid overwhelming the UI
