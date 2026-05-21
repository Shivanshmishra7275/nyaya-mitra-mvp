"""
config.py
==========
Nyaya Mitra — Centralised Configuration
----------------------------------------
All tunables, environment variables, and constants live here.
The rest of the application imports from this module exclusively — 
no os.getenv() calls scattered across the codebase.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env before reading any environment variables ──────────────────────
load_dotenv()

# ── Project Root ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent

# ── API Keys ────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

if not GEMINI_API_KEY:
    raise ValueError(
        "GEMINI_API_KEY is missing. "
        "Create a .env file in the project root with: GEMINI_API_KEY=your_key"
    )

# ── ChromaDB ────────────────────────────────────────────────────────────────
CHROMA_DB_PATH: str       = os.getenv("CHROMA_DB_PATH", str(BASE_DIR / "chroma_db"))
CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "nyaya_mitra_legal")

# ── Embedding Model (Gemini) ────────────────────────────────────────────────
# Default to Google's latest text embedding model for retrieval.
# This is used both by the offline ETL pipeline and the online RAG service.
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "models/gemini-embedding-001")
EMBEDDING_DIMENSIONS: int = 768   # Matches gemini-embedding-001 output (approx.)

# ── RAG Configuration ────────────────────────────────────────────────────────
RAG_TOP_K: int        = int(os.getenv("RAG_TOP_K", "15"))
CHUNK_SIZE: int       = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP: int    = int(os.getenv("CHUNK_OVERLAP", "200"))

# ── Gemini Configuration ──────────────────────────────────────────────────
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# Low temperature for legal Q&A — maximal determinism over creativity
GEMINI_QA_TEMPERATURE: float         = 0.1
GEMINI_QA_MAX_OUTPUT_TOKENS: int     = 2048
GEMINI_QA_TOP_P: float               = 0.8

# Slightly higher temperature for document drafting — controlled language variety
GEMINI_DRAFT_TEMPERATURE: float      = 0.3
GEMINI_DRAFT_MAX_OUTPUT_TOKENS: int  = 4096
GEMINI_DRAFT_TOP_P: float            = 0.9

# ── FastAPI Configuration ────────────────────────────────────────────────────
FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "8000"))
FASTAPI_ENV: str  = os.getenv("FASTAPI_ENV", "development")

# CORS origins — locked down in production, open in development
if FASTAPI_ENV == "production":
    CORS_ORIGINS: list[str] = os.getenv("CORS_ORIGINS", "https://nyayamitra.in").split(",")
else:
    CORS_ORIGINS: list[str] = ["*"]

# ── SQLite Configuration (MVP) ───────────────────────────────────────────────
SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "nyaya_mitra.db"))

# ── Data Pipeline ────────────────────────────────────────────────────────────
RAW_DATA_DIR: Path = BASE_DIR / "Raw_Data"

# Ordered list of PDFs to ingest into ChromaDB
PDF_FILES: list[str] = [
    "bns.pdf",    # Bharatiya Nyaya Sanhita 2023
    "bnss.pdf",   # Bharatiya Nagarik Suraksha Sanhita 2023
    "bsa.pdf",    # Bharatiya Sakshya Adhiniyam 2023
    "const.pdf",  # Constitution of India
]

# Human-readable law code mapping for metadata
#   key = PDF filename stem, value = display name used in citations
LAW_CODE_MAP: dict[str, str] = {
    "bns":   "BNS",
    "bnss":  "BNSS",
    "bsa":   "BSA",
    "const": "Constitution",
}

# ── Templates ────────────────────────────────────────────────────────────────
TEMPLATES_DIR: Path = BASE_DIR / "templates"

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ── Application Metadata ─────────────────────────────────────────────────────
APP_TITLE:       str = "Nyaya Mitra API"
APP_DESCRIPTION: str = "AI-Powered Indian Legal Intelligence Platform"
APP_VERSION:     str = "1.0.0"

# ── Legal Disclaimer ─────────────────────────────────────────────────────────
# Appended to every AI response — mandatory for compliance
LEGAL_DISCLAIMER: str = (
    "⚖️ This is AI-generated legal information based on the BNS, BNSS, BSA, and "
    "Constitution of India. It is not legal advice. Consult a registered and "
    "qualified advocate for advice specific to your situation. Nyaya Mitra is not "
    "responsible for any action taken based on this information."
)
