"""etl_pipeline.py
===================
Nyaya Mitra - Legal AI ETL Pipeline (ChromaDB + Gemini)
-------------------------------------------------------
Extract  : Loads raw legal PDFs from Raw_Data/ via LangChain PyPDFLoader.
Transform: Splits pages into overlapping chunks; enriches metadata with
           law_code, chunk_id (deterministic), and 1-indexed page numbers.
Embed    : Encodes every chunk using the Gemini embedding API in batches,
           with quota-aware retry and a local checkpoint.
Load     : Upserts chunks + embeddings + metadata into a ChromaDB
           PersistentClient collection (cosine similarity, HNSW index).

Run once before starting the FastAPI server:
    python etl_pipeline.py
"""

from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

import chromadb
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    BASE_DIR,
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
    GEMINI_API_KEY,
    LAW_CODE_MAP,
    PDF_FILES,
    RAW_DATA_DIR,
)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants & Checkpointing
# ---------------------------------------------------------------------------

# Number of chunks to embed per Gemini API call. Kept in the
# 10–20 range (16) to balance latency and quota safety.
EMBED_BATCH_SIZE = 16

# Wait time (seconds) before retrying when hitting free-tier quota limits.
EMBED_RETRY_SLEEP_SECONDS = 60

# Local JSON checkpoint file to allow resuming long ETL runs without
# re-embedding already-processed chunks.
CHECKPOINT_PATH = BASE_DIR / "etl_checkpoint.json"


# ---------------------------------------------------------------------------
# Gemini Embeddings Setup
# ---------------------------------------------------------------------------

# Configure the Gemini SDK once for the ETL process. The API key is loaded
# from config.py, which in turn reads it from the environment (.env).
genai.configure(api_key=GEMINI_API_KEY)


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def _load_checkpoint(total_chunks: int) -> int:
    """Return the next chunk index to process based on the checkpoint.

    If no checkpoint exists or it cannot be read, start from 0.
    """
    if not CHECKPOINT_PATH.exists():
        return 0

    try:
        with CHECKPOINT_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        idx = int(data.get("next_index", 0))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "Failed to read ETL checkpoint '%s': %s; starting from 0",
            CHECKPOINT_PATH,
            exc,
        )
        return 0

    # Clamp to valid range
    return max(0, min(idx, total_chunks))


def _save_checkpoint(next_index: int, total_chunks: int) -> None:
    """Persist the index of the next chunk to process as JSON."""
    payload = {
        "next_index": int(next_index),
        "total_chunks": int(total_chunks),
        "timestamp": time.time(),
    }
    try:
        with CHECKPOINT_PATH.open("w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning(
            "Failed to write ETL checkpoint '%s': %s",
            CHECKPOINT_PATH,
            exc,
        )


# ---------------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------------

def extract_documents(pdf_dir: Path, pdf_files: list[str]) -> list[Any]:
    """Load all PDFs from *pdf_dir* using PyPDFLoader.

    Normalises metadata:
      - source  → bare filename (e.g. 'bns.pdf')
      - page    → 1-indexed integer (PyPDFLoader uses 0-indexed by default)
      - law_code → human-readable law name from LAW_CODE_MAP
    """
    all_documents: list[Any] = []

    for filename in pdf_files:
        pdf_path = pdf_dir / filename
        if not pdf_path.exists():
            logger.warning("PDF not found — skipping: %s", pdf_path)
            continue

        try:
            t0 = time.perf_counter()
            loader = PyPDFLoader(str(pdf_path))
            documents = loader.load()

            stem = Path(filename).stem  # e.g. "bns"
            law_code = LAW_CODE_MAP.get(stem, stem.upper())

            for doc in documents:
                doc.metadata["source"] = filename
                doc.metadata["law_code"] = law_code
                # Convert 0-indexed page to 1-indexed for citation display
                raw_page = doc.metadata.get("page", 0)
                doc.metadata["page"] = int(raw_page) + 1

            all_documents.extend(documents)
            elapsed = time.perf_counter() - t0
            logger.info(
                "  [EXTRACT] %-12s  %4d pages  (%.2fs)",
                filename,
                len(documents),
                elapsed,
            )

        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to load '%s': %s", filename, exc, exc_info=True)

    logger.info("Extraction complete — total pages: %d", len(all_documents))
    return all_documents


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------

def transform_chunks(documents: list[Any]) -> list[dict]:
    """Split pages into overlapping chunks and enrich with deterministic IDs.

    Returns a list of plain dicts:
        {
            "chunk_id": str,
            "text":     str,
            "source":   str,
            "law_code": str,
            "page":     int,
        }
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True,
    )

    raw_chunks = splitter.split_documents(documents)
    logger.info("Chunking complete — total raw chunks: %d", len(raw_chunks))

    # Group by (source, page) to assign per-page chunk indices
    page_counters: dict[tuple, int] = {}
    processed: list[dict] = []

    for chunk in raw_chunks:
        source = chunk.metadata.get("source", "unknown.pdf")
        page = chunk.metadata.get("page", 1)
        law_code = chunk.metadata.get("law_code", "UNKNOWN")
        stem = Path(source).stem

        key = (source, page)
        idx = page_counters.get(key, 0)
        page_counters[key] = idx + 1

        chunk_id = f"{stem}_p{page:04d}_c{idx:04d}"

        processed.append({
            "chunk_id": chunk_id,
            "text": chunk.page_content,
            "source": source,
            "law_code": law_code,
            "page": page,
        })

    logger.info("Transform complete — chunks ready for embedding: %d", len(processed))
    return processed


# ---------------------------------------------------------------------------
# EMBED + LOAD (Gemini API with checkpointing)
# ---------------------------------------------------------------------------

def embed_and_load_with_checkpoint(chunks: list[dict]) -> int:
    """Embed all chunks with Gemini and upsert into ChromaDB incrementally.

    Uses batch embedding (EMBED_BATCH_SIZE texts per API call), handles
    free-tier quota errors with a fixed backoff, and writes a checkpoint
    after every successful upsert so that long runs can be resumed.
    """
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    total = len(chunks)
    start_index = _load_checkpoint(total)

    if start_index >= total:
        logger.info(
            "Checkpoint indicates all %d chunks already processed; "
            "skipping embedding.",
            total,
        )
        return collection.count()

    if start_index > 0:
        logger.info("Resuming ETL from chunk index %d / %d", start_index, total)

    t0 = time.perf_counter()

    for start in range(start_index, total, EMBED_BATCH_SIZE):
        end = min(start + EMBED_BATCH_SIZE, total)
        batch_chunks = chunks[start:end]
        texts = [c["text"] for c in batch_chunks]

        # Single embed_content call per batch; if we hit a quota error, we
        # sleep EMBED_RETRY_SLEEP_SECONDS and retry the same batch.
        while True:
            try:
                result = genai.embed_content(
                    model=EMBEDDING_MODEL,
                    content=texts,
                )
                break
            except ResourceExhausted as exc:
                logger.warning(
                    "Gemini embedding quota hit; sleeping %.1fs before "
                    "retrying batch (%d-%d) / %d: %s",
                    EMBED_RETRY_SLEEP_SECONDS,
                    start,
                    end,
                    total,
                    exc,
                )
                time.sleep(EMBED_RETRY_SLEEP_SECONDS)

        if "embeddings" in result:
            batch_vectors = [emb["values"] for emb in result["embeddings"]]
        else:
            # Fallback for unexpected single-embedding responses.
            batch_vectors = [result["embedding"]]

        collection.upsert(
            ids=[c["chunk_id"] for c in batch_chunks],
            embeddings=batch_vectors,
            documents=[c["text"] for c in batch_chunks],
            metadatas=[
                {
                    "source": c["source"],
                    "law_code": c["law_code"],
                    "page": c["page"],
                }
                for c in batch_chunks
            ],
        )

        _save_checkpoint(end, total)

        if (end % 200 == 0) or end == total:
            elapsed = time.perf_counter() - t0
            logger.info(
                "  [EMBED+LOAD] upserted %d / %d chunks (%.1fs)",
                end,
                total,
                elapsed,
            )

    final_count = collection.count()
    logger.info(
        "Embed+Load complete — collection '%s' now holds %d documents.",
        CHROMA_COLLECTION_NAME,
        final_count,
    )
    return final_count


# ---------------------------------------------------------------------------
# PIPELINE ORCHESTRATOR
# ---------------------------------------------------------------------------

def main() -> None:
     """Full ETL: Extract → Transform → Embed → Load."""
     pipeline_start = time.perf_counter()
 
     logger.info("=" * 64)
     logger.info("Nyaya Mitra — ETL Pipeline  START")
     logger.info("  DB path    : %s", CHROMA_DB_PATH)
     logger.info("  Collection : %s", CHROMA_COLLECTION_NAME)
     logger.info("  Model      : %s", EMBEDDING_MODEL)
     logger.info("=" * 64)
 
     # 1. EXTRACT
     documents = extract_documents(RAW_DATA_DIR, PDF_FILES)
     if not documents:
         logger.error("No documents loaded. Aborting.")
         sys.exit(1)
 
     # 2. TRANSFORM
     chunks = transform_chunks(documents)
     if not chunks:
         logger.error("No chunks produced. Aborting.")
         sys.exit(1)

    # 3. EMBED + LOAD — Gemini embeddings with checkpointed Chroma upserts
    logger.info("Embedding and loading with Gemini model: %s", EMBEDDING_MODEL)
    final_count = embed_and_load_with_checkpoint(chunks)

    elapsed = time.perf_counter() - pipeline_start
    logger.info("=" * 64)
    logger.info("Nyaya Mitra — ETL Pipeline  COMPLETE")
    logger.info("  Chunks ingested : %d", len(chunks))
    logger.info("  Collection size : %d", final_count)
    logger.info("  Total time      : %.1fs", elapsed)
    logger.info("=" * 64)


if __name__ == "__main__":
    main()
