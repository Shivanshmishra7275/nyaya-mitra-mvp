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
        cross_encoder_model_name: Optional[str] = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        self._bm25 = bm25
        self._qdrant = qdrant_retriever
        self._cross_encoder = None
        if cross_encoder_model_name:
            try:
                from sentence_transformers import CrossEncoder # noqa: PLC0415
                logger.info("Loading Cross-Encoder model: %s", cross_encoder_model_name)
                self._cross_encoder = CrossEncoder(cross_encoder_model_name)
            except ImportError:
                logger.warning("sentence-transformers not installed. Cross-encoder disabled.")
            except Exception as e:
                logger.warning("Failed to load cross-encoder: %s", e)

    def retrieve(self, query: str, top_k: int = 15) -> tuple[list[dict], str]:
        """
        Retrieve top_k chunks using Reciprocal Rank Fusion of BM25 + optional semantic.

        Returns:
            (chunks, retrieval_note) — note describes which retrievers fired.
        """
        bm25_results = self._bm25.retrieve(query, top_k=top_k)
        act_names = sorted(self._bm25.act_names) if hasattr(self._bm25, "act_names") else []
        expected = {
            "Bharatiya Nyaya Sanhita, 2023",
            "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "Bharatiya Sakshya Adhiniyam, 2023",
        }
        missing = sorted(expected - set(act_names)) if act_names else []
        corpus_label = ", ".join(act_names) if act_names else "Unknown"
        coverage_note = f"Corpus: {corpus_label}."
        if missing:
            coverage_note += f" Coverage incomplete (missing: {', '.join(missing)})."
        coverage_note += " Sources are official act texts only (no case law)."

        # Apply Reranking if available
        def _rerank(results):
            if self._cross_encoder is not None and results:
                try:
                    pairs = [[query, chunk["text"]] for chunk in results]
                    scores = self._cross_encoder.predict(pairs)
                    for chunk, score in zip(results, scores):
                        chunk["rerank_score"] = float(score)
                    results = sorted(results, key=lambda x: x["rerank_score"], reverse=True)
                except Exception as e:
                    logger.warning("Cross-encoder reranking failed: %s", e)
            return results

        # BM25-only path (fast, no Qdrant)
        if self._qdrant is None:
            results = _rerank(bm25_results[:top_k])
            note = f"Retrieved {len(results)} chunks via BM25-only."
            if self._cross_encoder: note += " (Reranked via Cross-Encoder)."
            note += f" {coverage_note}"
            logger.info(note)
            return results, note

        # Try hybrid path with RRF
        try:
            semantic_results = self._qdrant.retrieve(query, top_k=top_k)
            merged = _apply_rrf(bm25_results, semantic_results, top_k=top_k)
            merged = _rerank(merged)
            note = f"Retrieved {len(merged)} chunks via Hybrid (BM25 + Semantic, RRF fusion)."
            if self._cross_encoder: note += " (Reranked via Cross-Encoder)."
            note += f" {coverage_note}"
            logger.info(note)
            return merged, note

        except Exception as exc:
            logger.warning("Qdrant retrieval failed, falling back to BM25: %s", exc)
            fallback = _rerank(bm25_results[:top_k])
            note = f"Retrieved {len(fallback)} chunks via BM25-only (Qdrant unavailable)."
            if self._cross_encoder: note += " (Reranked via Cross-Encoder)."
            note += f" {coverage_note}"
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
