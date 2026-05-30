"""
etl_pipeline.py
================
Nyaya Mitra — Legal AI ETL Pipeline (v2)
-----------------------------------------
Changes from v1:
  - Mock embeddings REMOVED entirely.
  - Dynamic PDF scanning: no more hardcoded filenames.
    Automatically picks up all .pdf files in Raw_Data/.
  - Chunk output simplified (no embedding field stored).
  - Metadata enriched: source, page (1-indexed for humans), start_index, chunk_index.

Future: Add --qdrant flag to also push embeddings to Qdrant for semantic retrieval.
        For now, BM25 is the primary retrieval mode.

Usage:
    python etl_pipeline.py               # scans Raw_Data/, writes vector_store_mock.json
    python etl_pipeline.py --dir ./data  # custom input dir
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_RAW_DATA_DIR = Path("Raw_Data")
DEFAULT_OUTPUT_FILE = Path("vector_store_mock.json")

CHUNK_SIZE = 1000    # characters — enough for a full legal sub-section
CHUNK_OVERLAP = 200  # ~20% overlap ensures boundary clauses are not truncated

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
# Extract — Dynamic PDF scanning
# ---------------------------------------------------------------------------

def discover_pdfs(pdf_dir: Path) -> list[Path]:
    """
    Dynamically discover all .pdf files in pdf_dir (non-recursive).
    Replaces the old hardcoded PDF_FILES list.
    """
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        logger.warning("No PDF files found in '%s'", pdf_dir)
    else:
        logger.info("Discovered %d PDF(s): %s", len(pdfs), [p.name for p in pdfs])
    return pdfs


def extract_documents(pdf_dir: Path) -> list[Any]:
    """
    Load all PDFs found in pdf_dir using LangChain's PyPDFLoader.
    Each page becomes a LangChain Document object.
    Source metadata is normalised to just the filename.
    """
    all_documents = []
    pdfs = discover_pdfs(pdf_dir)

    for pdf_path in pdfs:
        try:
            logger.info("Loading: %s", pdf_path.name)
            loader = PyPDFLoader(str(pdf_path))
            documents = loader.load()

            for doc in documents:
                # Normalise source to bare filename for consistent citation labels
                doc.metadata["source"] = pdf_path.name

            all_documents.extend(documents)
            logger.info("  -> %d page(s) from '%s'", len(documents), pdf_path.name)
        except Exception as exc:
            logger.error("Failed to load '%s': %s", pdf_path.name, exc, exc_info=True)

    logger.info("Extraction complete. Total pages: %d", len(all_documents))
    return all_documents


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def transform_documents(documents: list[Any]) -> list[dict]:
    """
    Split document pages into overlapping chunks.
    No mock embeddings. No useless constant vectors.
    Metadata fields: source, page (1-indexed), start_index, chunk_id.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True,
    )

    chunks = splitter.split_documents(documents)
    logger.info("Chunking complete. Total chunks: %d", len(chunks))

    processed: list[dict] = []
    for idx, chunk in enumerate(chunks):
        try:
            meta = dict(chunk.metadata)
            # Convert page to 1-indexed integer for human-readable citations
            raw_page = meta.get("page", 0)
            meta["page"] = int(raw_page) + 1 if isinstance(raw_page, (int, float)) else raw_page

            processed.append({
                "chunk_id": idx,
                "text": chunk.page_content,
                "metadata": meta,
                # NOTE: No embedding stored. BM25 works on raw text.
                # When Qdrant is added, embeddings are computed and pushed there, not here.
            })
        except Exception as exc:
            logger.error(
                "Failed to process chunk %d: %s", idx, exc, exc_info=True
            )

    logger.info("Transform complete. Processed chunks: %d", len(processed))
    return processed


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------

def load_to_json(chunks: list[dict], output_path: Path) -> None:
    """
    Write the processed chunks to a JSON file.
    This is the BM25 retrieval store — no real vector DB required.
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            json.dump(chunks, fh, ensure_ascii=False, indent=2)
        logger.info("Wrote %d chunks to '%s' (%.1f MB)", len(chunks), output_path,
                    output_path.stat().st_size / 1_048_576)
    except OSError as exc:
        logger.error("Failed to write '%s': %s", output_path, exc, exc_info=True)
        raise


# ---------------------------------------------------------------------------
# Pipeline Orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(raw_data_dir: Path, output_file: Path) -> None:
    logger.info("=" * 60)
    logger.info("Nyaya Mitra — ETL Pipeline v2   START")
    logger.info("Input:  %s", raw_data_dir.resolve())
    logger.info("Output: %s", output_file.resolve())
    logger.info("=" * 60)

    documents = extract_documents(raw_data_dir)
    if not documents:
        logger.error("No documents loaded. Aborting.")
        sys.exit(1)

    chunks = transform_documents(documents)
    if not chunks:
        logger.error("No chunks produced. Aborting.")
        sys.exit(1)

    load_to_json(chunks, output_file)

    logger.info("=" * 60)
    logger.info("Nyaya Mitra — ETL Pipeline v2   COMPLETE")
    logger.info("Chunks: %d  |  Run the API server to use them.", len(chunks))
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Nyaya Mitra ETL Pipeline")
    parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_RAW_DATA_DIR,
        help="Directory containing legal PDF files (default: Raw_Data/)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help="Output JSON file path (default: vector_store_mock.json)",
    )
    args = parser.parse_args()
    run_pipeline(args.dir, args.output)
