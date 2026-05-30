"""
app/retrieval/qdrant_retriever.py
===================================
Semantic retriever using Qdrant (local or cloud) + sentence-transformers.

This is Retriever B in the hybrid pipeline.

Model choice: all-MiniLM-L6-v2
  - 22 MB on disk, 384-dimensional vectors
  - Runs fully local — no API call, no cost, no quota
  - Strong multilingual quality for English + Hindi legal text
  - Adequate for legal similarity (outperforms BM25 on paraphrase queries)

Qdrant choice:
  - Free open-source, runs locally via Docker
  - Free cloud tier at cloud.qdrant.io (1 GB storage)
  - docker run -p 6333:6333 qdrant/qdrant

Graceful degradation:
  - If Qdrant is unreachable, HybridRetriever falls back to BM25-only.
  - This module is only imported when QDRANT_ENABLED=true.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy imports — only pay cost when this module is actually used
_sentence_transformers = None
_QdrantClient = None
_models_qdrant = None


def _ensure_imports():
    """Import heavy dependencies only when Qdrant retriever is actually used."""
    global _sentence_transformers, _QdrantClient, _models_qdrant
    if _sentence_transformers is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        _sentence_transformers = SentenceTransformer
    if _QdrantClient is None:
        from qdrant_client import QdrantClient  # noqa: PLC0415
        from qdrant_client import models as qdrant_models  # noqa: PLC0415
        _QdrantClient = QdrantClient
        _models_qdrant = qdrant_models


EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class QdrantRetriever:
    """
    Semantic retriever: encodes query with a local sentence-transformer,
    then searches Qdrant for the nearest legal chunks by cosine similarity.

    Usage:
        retriever = QdrantRetriever(host="localhost", port=6333, collection="nyaya_legal_chunks")
        retriever.load()                           # downloads model on first run (~22 MB)
        results = retriever.retrieve("theft", 10)  # returns list of chunk dicts
    """

    def __init__(self, host: str = "localhost", port: int = 6333, collection: str = "nyaya_legal_chunks"):
        self._host = host
        self._port = port
        self._collection = collection
        self._client: Optional[object] = None
        self._model: Optional[object] = None
        self._loaded = False

    def load(self) -> bool:
        """
        Connect to Qdrant and load the embedding model.
        Returns True on success.
        """
        try:
            _ensure_imports()
            logger.info("Loading sentence-transformer model: %s", EMBEDDING_MODEL)
            self._model = _sentence_transformers(EMBEDDING_MODEL)

            logger.info("Connecting to Qdrant at %s:%s", self._host, self._port)
            self._client = _QdrantClient(host=self._host, port=self._port)

            # Verify collection exists
            collections = self._client.get_collections()
            names = [c.name for c in collections.collections]
            if self._collection not in names:
                logger.warning(
                    "Qdrant collection '%s' not found. Run: python etl_pipeline.py --qdrant",
                    self._collection,
                )
                return False

            info = self._client.get_collection(self._collection)
            logger.info(
                "Qdrant retriever ready. Collection='%s' vectors=%d",
                self._collection,
                info.vectors_count or 0,
            )
            self._loaded = True
            return True

        except Exception as exc:
            logger.error("QdrantRetriever.load() failed: %s", exc, exc_info=True)
            return False

    @property
    def is_ready(self) -> bool:
        return self._loaded and self._client is not None and self._model is not None

    def retrieve(self, query: str, top_k: int = 10) -> list[dict]:
        """
        Encode query and search Qdrant for semantically similar legal chunks.

        Returns:
            List of chunk dicts matching the schema from etl_pipeline.py:
            {chunk_id, text, metadata}
        """
        if not self.is_ready:
            logger.warning("QdrantRetriever not ready — skipping semantic search.")
            return []

        try:
            query_vector = self._model.encode(query, normalize_embeddings=True).tolist()

            results = self._client.search(
                collection_name=self._collection,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )

            chunks = []
            for hit in results:
                payload = hit.payload or {}
                chunks.append({
                    "chunk_id": payload.get("chunk_id", hit.id),
                    "text": payload.get("text", ""),
                    "metadata": payload.get("metadata", {}),
                    "_score": hit.score,  # cosine similarity score
                })

            logger.debug("Qdrant returned %d semantic results for query.", len(chunks))
            return chunks

        except Exception as exc:
            logger.error("Qdrant search failed: %s", exc, exc_info=True)
            return []
