"""
etl_pipeline.py
================
Nyaya Mitra — Legal AI ETL Pipeline (v2)
-----------------------------------------
Changes from v1:
  - Mock embeddings REMOVED entirely.
  - Dynamic PDF scanning: no more hardcoded filenames.
    Automatically picks up all .pdf files in Raw_Data/.
  - Chunk output simplified — metadata: source, page (1-indexed), start_index, chunk_id.
  - Optional --qdrant flag: computes real sentence-transformer embeddings and
    upserts them into Qdrant for hybrid semantic retrieval.

Usage:
    # BM25-only (fast, no model download):
    python etl_pipeline.py

    # BM25 + Qdrant semantic (downloads ~22 MB model on first run):
    python etl_pipeline.py --qdrant

    # Custom directories:
    python etl_pipeline.py --dir ./data --output ./store.json

    # Run Qdrant locally first:
    docker run -p 6333:6333 qdrant/qdrant
"""

import argparse
import json
import logging
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_RAW_DATA_DIR = Path("Raw_Data")
DEFAULT_OUTPUT_FILE = Path("vector_store_mock.json")

ACT_SOURCES = {
    "bns.pdf": {
        "act_name": "Bharatiya Nyaya Sanhita, 2023",
        "source_url": "https://www.mha.gov.in/sites/default/files/250883_english_01042024.pdf",
    },
    "bnss.pdf": {
        "act_name": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "source_url": "https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf",
    },
    "bsa.pdf": {
        "act_name": "Bharatiya Sakshya Adhiniyam, 2023",
        "source_url": "https://www.mha.gov.in/en/commoncontent/new-criminal-laws",
    },
}

SECTION_PATTERNS = [
    re.compile(r"(?m)^(?:Section|SECTION)\s+(\d+[A-Za-z]?)\s*[-–—:.]?\s*([^\n]*)$"),
    re.compile(r"(?m)^(\d{1,3}[A-Za-z]?)\.\s+([A-Z][^\n]{0,120})$"),
]

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

def discover_pdfs(pdf_dir: Path, include_all: bool = False) -> list[Path]:
    """
    Discover .pdf files in pdf_dir (non-recursive).
    By default, only official BNS/BNSS/BSA PDFs are included.
    """
    pdfs = sorted(pdf_dir.glob("*.pdf"))
    if not pdfs:
        logger.warning("No PDF files found in '%s'", pdf_dir)
        return []

    if include_all:
        logger.info("Discovered %d PDF(s): %s", len(pdfs), [p.name for p in pdfs])
        return pdfs

    allowed = {name.lower() for name in ACT_SOURCES.keys()}
    filtered = [p for p in pdfs if p.name.lower() in allowed]
    skipped = [p.name for p in pdfs if p.name.lower() not in allowed]

    if skipped:
        logger.warning("Skipping non-criminal-law PDFs: %s", skipped)

    logger.info("Discovered %d official PDF(s): %s", len(filtered), [p.name for p in filtered])
    return filtered


def extract_documents(pdf_dir: Path, include_all: bool = False) -> list[Any]:
    """
    Load all PDFs found in pdf_dir using LangChain's UnstructuredPDFLoader (or PyPDFLoader as fallback).
    Each page/element becomes a LangChain Document object.
    Source metadata is normalised to just the filename.
    """
    all_documents = []
    pdfs = discover_pdfs(pdf_dir, include_all=include_all)

    for pdf_path in pdfs:
        try:
            logger.info("Loading: %s", pdf_path.name)
            try:
                # Use Unstructured for better structural chunking out of the box if available
                loader = UnstructuredPDFLoader(str(pdf_path), mode="elements")
                documents = loader.load()
            except Exception as e:
                logger.warning("UnstructuredPDFLoader failed for '%s' (fallback to PyPDFLoader): %s", pdf_path.name, e)
                loader = PyPDFLoader(str(pdf_path))
                documents = loader.load()

            act_meta = ACT_SOURCES.get(pdf_path.name.lower()) if not include_all else None
            for doc in documents:
                # Normalise source to bare filename for consistent citation labels
                doc.metadata["source"] = pdf_path.name
                if act_meta:
                    doc.metadata["act_name"] = act_meta["act_name"]
                    doc.metadata["source_url"] = act_meta["source_url"]

            all_documents.extend(documents)
            logger.info("  -> %d element(s)/page(s) from '%s'", len(documents), pdf_path.name)
        except Exception as exc:
            logger.error("Failed to load '%s': %s", pdf_path.name, exc, exc_info=True)

    logger.info("Extraction complete. Total elements/pages: %d", len(all_documents))
    return all_documents


# ---------------------------------------------------------------------------
# Transform
# ---------------------------------------------------------------------------

def _merge_pages(pages: list[Document]) -> tuple[str, list[tuple[int, int]]]:
    """Merge page texts into one string and track start offsets per page."""
    parts = []
    offsets: list[tuple[int, int]] = []
    cursor = 0
    for doc in pages:
        page_num = doc.metadata.get("page", 0)
        offsets.append((cursor, int(page_num)))
        text = doc.page_content or ""
        parts.append(text)
        cursor += len(text) + 2
    return "\n\n".join(parts), offsets


def _page_for_offset(offset: int, offsets: list[tuple[int, int]]) -> int:
    """Resolve the nearest page number for a given text offset."""
    page = 0
    for start, page_num in offsets:
        if start <= offset:
            page = page_num
        else:
            break
    return int(page) + 1  # 1-indexed for human citations


def _split_by_section(text: str) -> list[dict]:
    """Best-effort section split using section-like headings."""
    matches = []
    for pattern in SECTION_PATTERNS:
        matches.extend(list(pattern.finditer(text)))

    if not matches:
        return [{"section_number": None, "section_title": None, "text": text, "start_index": 0}]

    # Sort by appearance in text
    matches = sorted(matches, key=lambda m: m.start())

    sections = []
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        section_number = match.group(1).strip() if match.group(1) else None
        section_title = match.group(2).strip() if match.group(2) else None
        sections.append({
            "section_number": section_number,
            "section_title": section_title,
            "text": section_text,
            "start_index": start,
        })

    return sections


def transform_documents(documents: list[Any]) -> list[dict]:
    """
    Split document pages into overlapping chunks, preferring section boundaries.
    Metadata fields: source, page (1-indexed), act_name, section_number, section_title, source_url.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True,
    )

    by_source: dict[str, list[Document]] = defaultdict(list)
    for doc in documents:
        source = doc.metadata.get("source", "Unknown")
        by_source[source].append(doc)

    section_docs: list[Document] = []
    for source, pages in by_source.items():
        pages = sorted(pages, key=lambda d: d.metadata.get("page", 0))
        full_text, offsets = _merge_pages(pages)
        sections = _split_by_section(full_text)

        act_name = pages[0].metadata.get("act_name") if pages else None
        source_url = pages[0].metadata.get("source_url") if pages else None

        for sec in sections:
            page = _page_for_offset(sec["start_index"], offsets)
            meta = {
                "source": source,
                "page": page,
                "act_name": act_name,
                "section_number": sec.get("section_number"),
                "section_title": sec.get("section_title"),
                "source_url": source_url,
            }
            section_docs.append(Document(page_content=sec["text"], metadata=meta))

    chunks = splitter.split_documents(section_docs)
    logger.info("Chunking complete. Total chunks: %d", len(chunks))

    processed: list[dict] = []
    for idx, chunk in enumerate(chunks):
        try:
            meta = dict(chunk.metadata)
            processed.append({
                "chunk_id": idx,
                "text": chunk.page_content,
                "metadata": meta,
                # No embedding stored in JSON — BM25 works on raw text.
                # Embeddings for Qdrant are computed separately in ingest_to_qdrant().
            })
        except Exception as exc:
            logger.error("Failed to process chunk %d: %s", idx, exc, exc_info=True)

    logger.info("Transform complete. Processed chunks: %d", len(processed))
    return processed


# ---------------------------------------------------------------------------
# Optional: Qdrant ingestion (real embeddings)
# ---------------------------------------------------------------------------

def ingest_to_qdrant(
    chunks: list[dict],
    host: str = "localhost",
    port: int = 6333,
    collection: str = "nyaya_legal_chunks",
    batch_size: int = 64,
) -> None:
    """
    Encode all chunks with a local sentence-transformer model and upsert into Qdrant.

    Model: all-MiniLM-L6-v2
      - 22 MB download on first run, then cached locally.
      - 384-dimensional float32 vectors.
      - Runs fully offline — no API key, no quota.

    Qdrant must be running before calling this:
      docker run -p 6333:6333 qdrant/qdrant
    """
    try:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        from qdrant_client import QdrantClient  # noqa: PLC0415
        from qdrant_client.models import Distance, VectorParams, PointStruct  # noqa: PLC0415
    except ImportError:
        logger.error(
            "sentence-transformers or qdrant-client not installed. "
            "Run: pip install sentence-transformers qdrant-client"
        )
        raise

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIM = 384

    logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)

    logger.info("Connecting to Qdrant at %s:%s", host, port)
    client = QdrantClient(host=host, port=port)

    # Create or recreate collection
    existing = [c.name for c in client.get_collections().collections]
    if collection in existing:
        logger.warning("Recreating existing Qdrant collection '%s'", collection)
        client.delete_collection(collection)

    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
    )
    logger.info("Qdrant collection '%s' created.", collection)

    # Encode and upsert in batches
    texts = [c["text"] for c in chunks]
    total = len(texts)
    logger.info("Encoding %d chunks (batch_size=%d)...", total, batch_size)

    points = []
    for i in range(0, total, batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_chunks = chunks[i : i + batch_size]

        # normalize_embeddings=True ensures cosine similarity works correctly
        embeddings = model.encode(batch_texts, normalize_embeddings=True, show_progress_bar=False)

        for j, (chunk, vector) in enumerate(zip(batch_chunks, embeddings)):
            points.append(
                PointStruct(
                    id=chunk["chunk_id"],
                    vector=vector.tolist(),
                    payload={
                        "chunk_id": chunk["chunk_id"],
                        "text": chunk["text"],
                        "metadata": chunk["metadata"],
                    },
                )
            )

        logger.info("  Encoded %d / %d chunks...", min(i + batch_size, total), total)

    client.upsert(collection_name=collection, points=points)
    logger.info(
        "Qdrant upsert complete. %d vectors in collection '%s'.",
        len(points), collection,
    )


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

def run_pipeline(
    raw_data_dir: Path,
    output_file: Path,
    include_all: bool = False,
    enable_qdrant: bool = False,
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    qdrant_collection: str = "nyaya_legal_chunks",
) -> None:
    logger.info("=" * 60)
    logger.info("Nyaya Mitra — ETL Pipeline v2   START")
    logger.info("Input:  %s", raw_data_dir.resolve())
    logger.info("Output: %s", output_file.resolve())
    logger.info("PDFs:   %s", "all PDFs" if include_all else "BNS/BNSS/BSA only")
    logger.info("Qdrant: %s", "ENABLED" if enable_qdrant else "disabled (BM25-only)")
    logger.info("=" * 60)

    documents = extract_documents(raw_data_dir, include_all=include_all)
    if not documents:
        logger.error("No documents loaded. Aborting.")
        sys.exit(1)

    chunks = transform_documents(documents)
    if not chunks:
        logger.error("No chunks produced. Aborting.")
        sys.exit(1)

    # Always write the BM25 JSON store
    load_to_json(chunks, output_file)

    # Optionally push to Qdrant for semantic retrieval
    if enable_qdrant:
        logger.info("Starting Qdrant ingestion...")
        ingest_to_qdrant(
            chunks,
            host=qdrant_host,
            port=qdrant_port,
            collection=qdrant_collection,
        )

    logger.info("=" * 60)
    logger.info("Nyaya Mitra — ETL Pipeline v2   COMPLETE")
    logger.info("Chunks: %d", len(chunks))
    if enable_qdrant:
        logger.info("Qdrant collection '%s' is ready for semantic retrieval.", qdrant_collection)
    logger.info("=" * 60)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Nyaya Mitra ETL Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python etl_pipeline.py                      # BM25-only (fast)
  python etl_pipeline.py --qdrant             # BM25 + Qdrant (requires Docker)
  python etl_pipeline.py --dir ./mypdfs       # custom input dir

For Qdrant, start the service first:
  docker run -p 6333:6333 qdrant/qdrant
"""
    )
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
    parser.add_argument(
        "--qdrant",
        action="store_true",
        default=False,
        help="Also ingest into Qdrant for semantic retrieval (requires qdrant-client + sentence-transformers)",
    )
    parser.add_argument("--qdrant-host", default="localhost", help="Qdrant host (default: localhost)")
    parser.add_argument("--qdrant-port", type=int, default=6333, help="Qdrant port (default: 6333)")
    parser.add_argument(
        "--qdrant-collection", default="nyaya_legal_chunks",
        help="Qdrant collection name (default: nyaya_legal_chunks)",
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        default=False,
        help="Include non-criminal-law PDFs in ingestion (not recommended).",
    )
    args = parser.parse_args()
    run_pipeline(
        raw_data_dir=args.dir,
        output_file=args.output,
        include_all=args.include_all,
        enable_qdrant=args.qdrant,
        qdrant_host=args.qdrant_host,
        qdrant_port=args.qdrant_port,
        qdrant_collection=args.qdrant_collection,
    )
