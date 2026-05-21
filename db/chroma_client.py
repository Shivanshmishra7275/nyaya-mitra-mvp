"""
db/chroma_client.py
====================
Nyaya Mitra — ChromaDB Persistent Client (Singleton)
------------------------------------------------------
Manages a single ChromaDB PersistentClient instance shared
across all requests via FastAPI's application state. Avoids
opening multiple connections to the same on-disk database.
"""

import logging
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.api.models.Collection import Collection

from config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """
    Singleton wrapper around chromadb.PersistentClient.
    Call ChromaDBClient.get_collection() to retrieve the legal corpus collection.
    """

    _client: Optional[chromadb.PersistentClient] = None
    _collection: Optional[Collection] = None

    @classmethod
    def initialize(cls) -> None:
        """
        Opens (or re-opens) the persistent ChromaDB store at CHROMA_DB_PATH.
        Called once during FastAPI startup (lifespan handler in main.py).
        
        The collection uses cosine similarity, which is appropriate for
        normalized dense embeddings (Gemini text embeddings in our case).
        """
        # Ensure the directory exists (ChromaDB will create files inside it)
        Path(CHROMA_DB_PATH).mkdir(parents=True, exist_ok=True)

        logger.info("Initializing ChromaDB at path: %s", CHROMA_DB_PATH)
        cls._client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

        cls._collection = cls._client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},   # Cosine distance for semantic search
        )

        count = cls._collection.count()
        logger.info(
            "ChromaDB ready — collection '%s' contains %d chunks.",
            CHROMA_COLLECTION_NAME,
            count,
        )

    @classmethod
    def get_collection(cls) -> Collection:
        """
        Returns the active ChromaDB collection.
        Raises RuntimeError if initialize() has not been called.
        """
        if cls._collection is None:
            raise RuntimeError(
                "ChromaDB collection is not initialized. "
                "Run etl_pipeline.py first to populate the vector store, "
                "then restart the FastAPI server."
            )
        return cls._collection

    @classmethod
    def get_chunk_count(cls) -> int:
        """Returns the total number of chunks in the collection, or 0 if not ready."""
        try:
            return cls._collection.count() if cls._collection else 0
        except Exception:
            return 0

    @classmethod
    def is_ready(cls) -> bool:
        """Returns True if the collection is loaded and contains at least one chunk."""
        return cls._collection is not None and cls.get_chunk_count() > 0
