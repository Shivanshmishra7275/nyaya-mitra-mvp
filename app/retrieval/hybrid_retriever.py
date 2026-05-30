"""
app/retrieval/hybrid_retriever.py
===================================
Hybrid retrieval orchestrator: BM25 (always) + Qdrant semantic (optional).

Architecture:
  Retriever A → BM25Retriever      (lexical, always available, zero infra)
  Retriever B → QdrantRetriever    (semantic, optional, requires Qdrant service)

Merging strategy:
  - Collect top_k results from each active retriever.
  - Deduplicate by chunk_id.
  - BM25 results are slightly preferred (appear first after dedup).
  - When Qdrant is disabled, falls back to BM25-only with a retrieval_note.
"""
import logging
from typing import Optional

from app.retrieval.bm25_retriever import BM25Retriever

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Orchestrates BM25 + optional Qdrant semantic retrieval.
    Call `retrieve()` — it always returns results even if Qdrant is down.
    """

    def __init__(
        self,
        bm25: BM25Retriever,
        qdrant_retriever=None,  # Optional QdrantRetriever — None disables semantic
    ):
        self._bm25 = bm25
        self._qdrant = qdrant_retriever

    def retrieve(self, query: str, top_k: int = 15) -> tuple[list[dict], str]:
        """
        Retrieve top_k chunks using hybrid search.

        Returns:
            (chunks, retrieval_note) — note describes which retrievers fired.
        """
        bm25_results = self._bm25.retrieve(query, top_k=top_k)
        seen_ids: set = set()
        merged: list[dict] = []

        # Add BM25 results first
        for chunk in bm25_results:
            cid = chunk.get("chunk_id", id(chunk))
            if cid not in seen_ids:
                seen_ids.add(cid)
                merged.append(chunk)

        mode = "BM25-only"

        # Optionally layer in Qdrant semantic results
        if self._qdrant is not None:
            try:
                semantic_results = self._qdrant.retrieve(query, top_k=top_k)
                for chunk in semantic_results:
                    cid = chunk.get("chunk_id", id(chunk))
                    if cid not in seen_ids:
                        seen_ids.add(cid)
                        merged.append(chunk)
                mode = "Hybrid (BM25 + Semantic)"
            except Exception as exc:
                logger.warning("Qdrant retrieval failed, falling back to BM25: %s", exc)
                mode = "BM25-only (Qdrant unavailable)"

        # Cap at top_k
        final = merged[:top_k]
        note = f"Retrieved {len(final)} chunks via {mode}."
        logger.info(note)
        return final, note
