"""
etl_pipeline.py
================
Nyaya Mitra - Legal AI ETL Pipeline
--------------------------------------
Extract  : Loads raw legal PDFs from the Raw_Data directory via PyPDFLoader.
Transform : Splits documents into overlapping chunks with RecursiveCharacterTextSplitter.
            Preserves source filename in chunk metadata for citation tracking.
            Attaches a mock embedding vector to every chunk.
Load      : Serialises all processed chunks to vector_store_mock.json.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

RAW_DATA_DIR = Path("Raw_Data")
OUTPUT_FILE  = Path("vector_store_mock.json")

# Chunking strategy for legal texts:
# • chunk_size=1000  — large enough to capture a full legal sub-section or
#                      article without losing meaning.
# • chunk_overlap=200 — ~20 % overlap ensures a sentence spanning a chunk
#                        boundary appears in both neighbours, so no clause
#                        is silently truncated during retrieval.
CHUNK_SIZE    = 1000
CHUNK_OVERLAP = 200

# PDFs to ingest (order is preserved in the output).
PDF_FILES = ["bns.pdf", "bnss.pdf", "bsa.pdf", "const.pdf"]

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
# Mock Embedding
# ---------------------------------------------------------------------------

def get_mock_embedding(text: str) -> list[float]:
    """
    Placeholder embedding function.
    Returns a constant 3-dimensional vector for every input text.

    TODO: Replace with a real embedding model, e.g.
          - openai.embeddings.create(input=text, model="text-embedding-3-small")
          - SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    """
    return [0.1, 0.2, 0.3]


# ---------------------------------------------------------------------------
# Extract
# ---------------------------------------------------------------------------

def extract_documents(pdf_dir: Path, pdf_files: list[str]) -> list[Any]:
    """
    Load all PDFs in *pdf_files* from *pdf_dir* using LangChain's PyPDFLoader.
    Each page is returned as a LangChain Document object.

    The source field in metadata is normalised to just the filename (e.g. 'bns.pdf')
    so downstream citation logic works independently of the ingestion path.

    Returns a flat list of Document objects across all PDFs.
    """
    all_documents = []

    for filename in pdf_files:
        pdf_path = pdf_dir / filename

        if not pdf_path.exists():
            logger.warning("PDF not found — skipping: %s", pdf_path)
            continue

        try:
            logger.info("Loading: %s", pdf_path)
            loader    = PyPDFLoader(str(pdf_path))
            documents = loader.load()

            # Normalise the source field to the bare filename so every chunk
            # from bns.pdf carries  metadata['source'] == 'bns.pdf', regardless
            # of where the script is executed from.
            for doc in documents:
                doc.metadata["source"] = filename

            all_documents.extend(documents)
            logger.info("  -> %d page(s) loaded from '%s'", len(documents), filename)

        except Exception as exc:
            logger.error(
                "Failed to load '%s': %s", filename, exc, exc_info=True
            )

    logger.info("Extraction complete. Total pages loaded: %d", len(all_documents))
    return all_documents


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform_documents(documents: list[Any]) -> list[dict]:
    """
    Split raw Document pages into semantically meaningful chunks and attach
    mock embeddings.

    Chunking rationale
    ------------------
    RecursiveCharacterTextSplitter splits on ['\n\n', '\n', ' ', ''] in order,
    preserving paragraph and sentence boundaries wherever possible.  This is
    far preferable to a naive fixed-width split for legal text, which relies
    heavily on numbered sections (e.g. "Section 302 IPC") and sub-clauses.

    chunk_size=1000
        Keeps each vector small enough for an LLM prompt window while still
        containing enough context for meaningful similarity retrieval.

    chunk_overlap=200
        Consecutive chunks share 200 characters, so a statutory condition that
        straddles a boundary is present in at least one chunk in full.

    Returns a list of dicts ready for JSON serialisation.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        # length_function=len uses character count (not tokens), which is
        # consistent and library-agnostic.  Swap to tiktoken if you need
        # token-level precision aligned to a specific model's context window.
        length_function=len,
        add_start_index=True,  # records char offset of chunk within its parent page
    )

    chunks = splitter.split_documents(documents)
    logger.info("Chunking complete. Total chunks produced: %d", len(chunks))

    processed_chunks: list[dict] = []

    for idx, chunk in enumerate(chunks):
        try:
            embedding = get_mock_embedding(chunk.page_content)

            processed_chunks.append({
                "chunk_id" : idx,
                "text"     : chunk.page_content,
                # metadata contains at minimum: source (filename), page (0-indexed),
                # and start_index (character offset inside the page).
                "metadata" : chunk.metadata,
                "embedding": embedding,
            })

        except Exception as exc:
            logger.error(
                "Failed to process chunk %d from '%s': %s",
                idx, chunk.metadata.get("source", "unknown"), exc, exc_info=True,
            )

    logger.info(
        "Transform complete. Chunks successfully processed: %d", len(processed_chunks)
    )
    return processed_chunks


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_to_json(processed_chunks: list[dict], output_path: Path) -> None:
    """
    Serialise the processed chunks to a JSON file as our mock vector store.

    In production this step would be replaced by upserts into a real vector
    database (e.g. Pinecone, Weaviate, Qdrant, or pgvector).
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(processed_chunks, fh, ensure_ascii=False, indent=2)

        logger.info(
            "Load complete. %d chunks written to '%s'",
            len(processed_chunks), output_path,
        )

    except OSError as exc:
        logger.error(
            "Failed to write output file '%s': %s", output_path, exc, exc_info=True
        )
        raise


# ---------------------------------------------------------------------------
# Pipeline Orchestrator
# ---------------------------------------------------------------------------

def run_pipeline() -> None:
    """
    Entry point.  Executes the three ETL stages in sequence:
        Extract  ->  Transform  ->  Load
    """
    logger.info("=" * 60)
    logger.info("Nyaya Mitra — Legal AI ETL Pipeline   START")
    logger.info("=" * 60)

    # 1. Extract — load raw PDF pages
    documents = extract_documents(RAW_DATA_DIR, PDF_FILES)
    if not documents:
        logger.error("No documents were loaded. Aborting pipeline.")
        return

    # 2. Transform — chunk, enrich metadata, embed
    processed_chunks = transform_documents(documents)
    if not processed_chunks:
        logger.error("No chunks were produced. Aborting pipeline.")
        return

    # 3. Load — persist to mock vector store
    load_to_json(processed_chunks, OUTPUT_FILE)

    logger.info("=" * 60)
    logger.info("Nyaya Mitra — Legal AI ETL Pipeline   COMPLETE")
    logger.info("Output : %s", OUTPUT_FILE.resolve())
    logger.info("=" * 60)


if __name__ == "__main__":
    run_pipeline()
