"""
etl_pipeline.py
================
Nyaya Mitra - Legal AI ETL Pipeline (ChromaDB Edition)
-------------------------------------------------------
Extract  : Loads raw legal PDFs from Raw_Data/ via LangChain PyPDFLoader.
Transform: Splits pages into overlapping chunks; enriches metadata with
           law_code, chunk_id (deterministic), and 1-indexed page numbers.
Embed    : Encodes every chunk with SentenceTransformer all-MiniLM-L6-v2
           (384-dimensional dense vectors, runs locally on CPU).
Load     : Upserts all chunks + embeddings + metadata into a ChromaDB
           PersistentClient collection (cosine similarity, HNSW index).

Run once before starting the FastAPI server:
    python etl_pipeline.py
"""

import logging
import time
from pathlib import Path
from typing import Any

import chromadb
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

from config import (
    CHROMA_COLLECTION_NAME,
    CHROMA_DB_PATH,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_MODEL,
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
# Constants
# ---------------------------------------------------------------------------

EMBED_BATCH_SIZE = 32   # chunks per SentenceTransformer encode() call
CHROMA_BATCH_SIZE = 500  # documents per ChromaDB upsert() call


# ---------------------------------------------------------------------------
# EXTRACT
# ---------------------------------------------------------------------------

def extract_documents(pdf_dir: Path, pdf_files: list[str]) -> list[Any]:
    """
    Load all PDFs from *pdf_dir* using PyPDFLoader.
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
                "  [EXTRACT] %-12s  %4d pages  (%.2fs)", filename, len(documents), elapsed
            )

        except Exception as exc:
            logger.error("Failed to load '%s': %s", filename, exc, exc_info=True)

    logger.info("Extraction complete — total pages: %d", len(all_documents))
    return all_documents


# ---------------------------------------------------------------------------
# TRANSFORM
# ---------------------------------------------------------------------------

def transform_chunks(documents: list[Any]) -> list[dict]:
    """
    Split pages into overlapping chunks and enrich each with a deterministic
    chunk_id of the form  <stem>_p<page:04d>_c<i:04d>  (e.g. bns_p0023_c0002).

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
# EMBED
# ---------------------------------------------------------------------------

def generate_embeddings(
    chunks: list[dict], model: SentenceTransformer
) -> list[list[float]]:
    """
    Encode chunk texts in batches of EMBED_BATCH_SIZE.
    Returns list of 384-dim float vectors aligned 1:1 with *chunks*.
    """
    texts = [c["text"] for c in chunks]
    all_embeddings: list[list[float]] = []

    total_batches = (len(texts) + EMBED_BATCH_SIZE - 1) // EMBED_BATCH_SIZE
    t0 = time.perf_counter()

    for batch_idx in range(total_batches):
        start = batch_idx * EMBED_BATCH_SIZE
        end = start + EMBED_BATCH_SIZE
        batch = texts[start:end]

        vectors = model.encode(batch, show_progress_bar=False).tolist()
        all_embeddings.extend(vectors)

        if (batch_idx + 1) % 10 == 0 or (batch_idx + 1) == total_batches:
            elapsed = time.perf_counter() - t0
            logger.info(
                "  [EMBED] batch %d/%d  |  %d/%d chunks  (%.1fs)",
                batch_idx + 1, total_batches,
                min(end, len(texts)), len(texts),
                elapsed,
            )

    logger.info(
        "Embedding complete — %d vectors generated in %.1fs",
        len(all_embeddings),
        time.perf_counter() - t0,
    )
    return all_embeddings


# ---------------------------------------------------------------------------
# LOAD
# ---------------------------------------------------------------------------

def load_to_chromadb(
    chunks: list[dict],
    embeddings: list[list[float]],
    db_path: str,
    collection_name: str,
) -> int:
    """
    Upsert all chunks into a ChromaDB PersistentClient in batches.
    Returns the final document count in the collection.
    """
    client = chromadb.PersistentClient(path=db_path)

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    total = len(chunks)
    upserted = 0
    t0 = time.perf_counter()

    for start in range(0, total, CHROMA_BATCH_SIZE):
        end = min(start + CHROMA_BATCH_SIZE, total)
        batch_chunks = chunks[start:end]
        batch_embeddings = embeddings[start:end]

        collection.upsert(
            ids=[c["chunk_id"] for c in batch_chunks],
            embeddings=batch_embeddings,
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
        upserted += len(batch_chunks)
        logger.info(
            "  [LOAD] upserted %d / %d  (%.1fs)",
            upserted, total, time.perf_counter() - t0,
        )

    final_count = collection.count()
    logger.info(
        "Load complete — collection '%s' now holds %d documents (%.1fs total)",
        collection_name, final_count, time.perf_counter() - t0,
    )
    return final_count


# ---------------------------------------------------------------------------
# PIPELINE ORCHESTRATOR
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Full ETL: Extract → Transform → Embed → Load
    """
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
        return

    # 2. TRANSFORM
    chunks = transform_chunks(documents)
    if not chunks:
        logger.error("No chunks produced. Aborting.")
        return

    # 3. EMBED — load model once, reuse for all chunks
    logger.info("Loading SentenceTransformer model: %s", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)
    embeddings = generate_embeddings(chunks, model)

    # 4. LOAD
    final_count = load_to_chromadb(
        chunks, embeddings, CHROMA_DB_PATH, CHROMA_COLLECTION_NAME
    )

    elapsed = time.perf_counter() - pipeline_start
    logger.info("=" * 64)
    logger.info("Nyaya Mitra — ETL Pipeline  COMPLETE")
    logger.info("  Chunks ingested : %d", len(chunks))
    logger.info("  Collection size : %d", final_count)
    logger.info("  Total time      : %.1fs", elapsed)
    logger.info("=" * 64)


if __name__ == "__main__":
    main()
