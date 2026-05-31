"""
app/core/config.py
==================
All configuration is loaded from environment variables.
Never hardcode secrets here. Copy .env.example -> .env and fill in values.
"""
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App metadata ─────────────────────────────────────────────────────────
    APP_NAME: str = "Nyaya Mitra API"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"  # "development" | "production"

    # ── Server-side Gemini key (optional — BYOK is preferred) ────────────────
    # If set, this is used as a fallback when no user key is provided.
    # Leave blank in production to force BYOK.
    GEMINI_API_KEY: Optional[str] = None

    # ── Admin endpoints ──────────────────────────────────────────────────────
    # Set a strong random secret in production: openssl rand -hex 32
    # If not set: admin routes are disabled in production, open (with warning) in dev.
    ADMIN_SECRET: Optional[str] = None

    # ── Rate limiting ────────────────────────────────────────────────────────
    # Max requests per minute per IP on the /legal-query endpoint.
    RATE_LIMIT_PER_MINUTE: int = 10

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    # In production, set this to your actual frontend URL(s).
    # Example: "https://nyaya-mitra.onrender.com,http://localhost:19006"
    ALLOWED_ORIGINS: str = "*"

    # ── Retrieval ─────────────────────────────────────────────────────────────
    VECTOR_STORE_PATH: str = "vector_store_mock.json"
    BM25_TOP_K: int = 15

    # ── Qdrant (optional — used for hybrid semantic retrieval) ────────────────
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "nyaya_legal_chunks"
    QDRANT_ENABLED: bool = False  # Set to True once Qdrant is running

    # ── LLM ───────────────────────────────────────────────────────────────────
    GEMINI_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parse ALLOWED_ORIGINS into a list."""
        if self.ALLOWED_ORIGINS.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — call this everywhere instead of importing Settings directly."""
    return Settings()
