"""
app/retrieval/bm25_retriever.py
================================
BM25 lexical retrieval over the pre-ingested JSON chunk store.
This is Retriever A in the hybrid pipeline.
"""
import json
import logging
import re
from pathlib import Path
from typing import Optional

from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> list[str]:
    """
    Tokenize text for BM25 indexing and querying.

    Uses regex \\b word-boundary matching instead of whitespace split so that:
      - Punctuation is stripped: "theft." == "theft", "section," == "section"
      - Numbers are preserved: "section 378" -> ["section", "378"]
      - Consistent tokenization between index-time and query-time
    """
    return re.findall(r'\b\w+\b', text.lower())


class BM25Retriever:
    """
    Loads chunks from a JSON file on init and builds a BM25 index.
    Thread-safe for read-only retrieval after initialisation.
    """

    def __init__(self, store_path: str):
        self._store_path = Path(store_path)
        self._chunks: list[dict] = []
        self._index: Optional[BM25Okapi] = None
        self._loaded = False

    def load(self) -> bool:
        """Load the JSON chunk store and build the BM25 index. Returns True on success."""
        if not self._store_path.exists():
            logger.warning(
                "BM25 store not found at '%s'. Run etl_pipeline.py first.",
                self._store_path,
            )
            return False

        try:
            with open(self._store_path, "r", encoding="utf-8") as f:
                self._chunks = json.load(f)

            corpus = [_tokenize(chunk["text"]) for chunk in self._chunks]
            self._index = BM25Okapi(corpus)
            self._loaded = True
            logger.info(
                "BM25 index built: %d chunks from '%s'",
                len(self._chunks),
                self._store_path,
            )
            return True
        except Exception as exc:
            logger.error("Failed to load BM25 store: %s", exc, exc_info=True)
            return False

    @property
    def is_ready(self) -> bool:
        return self._loaded and self._index is not None

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    def retrieve(self, query: str, top_k: int = 15) -> list[dict]:
        """Return top_k chunks most relevant to the query by BM25 score."""
        if not self.is_ready:
            logger.warning("BM25 retriever not ready — returning empty results.")
            return []

        tokenized = _tokenize(query)
        # BM25Okapi.get_top_n returns the actual document dicts
        return self._index.get_top_n(tokenized, self._chunks, n=top_k)
