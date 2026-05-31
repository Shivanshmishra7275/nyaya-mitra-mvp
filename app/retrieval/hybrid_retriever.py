"""
app/retrieval/hybrid_retriever.py
===================================
Hybrid retrieval orchestrator: BM25 (always) + Qdrant semantic (optional).

Architecture:
  Retriever A → BM25Retriever      (lexical, always available, zero infra)
  Retriever B → QdrantRetriever    (semantic, optional, requires Qdrant service)

Merging strategy — Reciprocal Rank Fusion (RRF):
  - Collect top_k results from each active retriever.
  - For each chunk, compute its RRF score:  1 / (k + rank)  where k=60 (standard).
  - Sum RRF scores across retrievers for chunks that appear in both.
  - Sort by combined RRF score descending and cap at top_k.

  RRF is the industry-standard rank fusion method. It outperforms simple
  concatenation because a chunk that ranks 12th in BM25 but 1st semantically
  will correctly surface above a chunk that's 1st in BM25 but absent semantically.

  Reference: Cormack et al. (2009), "Reciprocal Rank Fusion outperforms Condorcet
  and individual Rank Learning Methods" — SIGIR 2009.

When Qdrant is disabled: falls back to BM25-only with a retrieval_note.
"""
import logging
from typing import Optional

from app.retrieval.bm25_retriever import BM25Retriever

logger = logging.getLogger(__name__)

RRF_K = 60  # Standard RRF constant — higher = smoother, lower = more aggressive reranking


def _rrf_score(rank: int, k: int = RRF_K) -> float:
    """Reciprocal Rank Fusion score for a result at position `rank` (0-indexed)."""
    return 1.0 / (k + rank + 1)  # +1 for 0-indexing


class HybridRetriever:
    """
    Orchestrates BM25 + optional Qdrant semantic retrieval with RRF score fusion.
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
        Retrieve top_k chunks using Reciprocal Rank Fusion of BM25 + optional semantic.

        Returns:
            (chunks, retrieval_note) — note describes which retrievers fired.
        """
        bm25_results = self._bm25.retrieve(query, top_k=top_k)

        # BM25-only path (fast, no Qdrant)
        if self._qdrant is None:
            note = f"Retrieved {len(bm25_results[:top_k])} chunks via BM25-only."
            logger.info(note)
            return bm25_results[:top_k], note

        # Try hybrid path with RRF
        try:
            semantic_results = self._qdrant.retrieve(query, top_k=top_k)
            merged = _apply_rrf(bm25_results, semantic_results, top_k=top_k)
            note = f"Retrieved {len(merged)} chunks via Hybrid (BM25 + Semantic, RRF fusion)."
            logger.info(note)
            return merged, note

        except Exception as exc:
            logger.warning("Qdrant retrieval failed, falling back to BM25: %s", exc)
            fallback = bm25_results[:top_k]
            note = f"Retrieved {len(fallback)} chunks via BM25-only (Qdrant unavailable)."
            logger.info(note)
            return fallback, note


def _apply_rrf(
    primary_results: list[dict],
    secondary_results: list[dict],
    top_k: int,
) -> list[dict]:
    """
    Merge two ranked result lists using Reciprocal Rank Fusion.

    Chunks are identified by their chunk_id. Chunks appearing in both lists
    accumulate RRF scores from both rankings, naturally surfacing to the top.
    Chunks unique to one retriever still appear, scored by their single-list rank.

    Args:
        primary_results:   BM25 results, in rank order (best first).
        secondary_results: Semantic results, in rank order (best first).
        top_k:             Maximum number of results to return.

    Returns:
        Merged list sorted by RRF score descending, capped at top_k.
    """
    # chunk_id → (rrf_score, chunk_dict)
    scores: dict = {}

    def _get_id(chunk: dict) -> object:
        return chunk.get("chunk_id", id(chunk))

    # Score BM25 results
    for rank, chunk in enumerate(primary_results):
        cid = _get_id(chunk)
        scores[cid] = [_rrf_score(rank), chunk]

    # Score semantic results — add to existing score if chunk appeared in BM25
    for rank, chunk in enumerate(secondary_results):
        cid = _get_id(chunk)
        if cid in scores:
            scores[cid][0] += _rrf_score(rank)  # accumulate
        else:
            scores[cid] = [_rrf_score(rank), chunk]

    # Sort by descending RRF score and return the chunk dicts
    ranked = sorted(scores.values(), key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in ranked[:top_k]]
