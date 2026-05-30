"""
tests/test_api.py
==================
Nyaya Mitra backend tests.
Run with: pytest tests/ -v

Tests cover:
  - /health endpoint
  - /version endpoint
  - /api/v1/legal-query input validation
  - /api/v1/legal-query missing API key (401)
  - BM25 retriever unit test
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.retrieval.bm25_retriever import BM25Retriever


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """TestClient that properly triggers lifespan (loads BM25 index)."""
    with TestClient(app) as c:
        yield c


# ─── Health & Version ─────────────────────────────────────────────────────────

def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "retrieval_mode" in body
    assert "chunks_loaded" in body


def test_version_returns_200(client):
    resp = client.get("/version")
    assert resp.status_code == 200
    body = resp.json()
    assert "version" in body
    assert "name" in body


# ─── Input validation ─────────────────────────────────────────────────────────

def test_query_too_short_returns_422(client):
    resp = client.post("/api/v1/legal-query", json={"user_query": "hi"})
    assert resp.status_code == 422


def test_query_too_long_returns_422(client):
    resp = client.post(
        "/api/v1/legal-query",
        json={"user_query": "a" * 1001},
    )
    assert resp.status_code == 422


def test_query_empty_string_returns_422(client):
    resp = client.post("/api/v1/legal-query", json={"user_query": "   "})
    assert resp.status_code == 422


def test_query_missing_field_returns_422(client):
    resp = client.post("/api/v1/legal-query", json={})
    assert resp.status_code == 422


# ─── BYOK / auth ──────────────────────────────────────────────────────────────

def test_query_without_any_key_returns_401_when_no_server_key(client, monkeypatch):
    """If neither BYOK header nor server env key is set, expect 401."""
    import app.api.routes.query as q_module
    monkeypatch.setattr(q_module.settings, "GEMINI_API_KEY", None)

    resp = client.post(
        "/api/v1/legal-query",
        json={"user_query": "What is murder under BNS?"},
    )
    assert resp.status_code == 401
    assert "API key" in resp.json()["detail"]


# ─── BM25 retriever unit test ──────────────────────────────────────────────────

def test_bm25_retriever_loads_and_retrieves():
    """BM25 retriever should load vector_store_mock.json and return chunks."""
    retriever = BM25Retriever(store_path="vector_store_mock.json")
    ok = retriever.load()
    assert ok is True, "BM25 failed to load — run etl_pipeline.py first"
    assert retriever.chunk_count > 0

    results = retriever.retrieve("theft robbery punishment", top_k=5)
    assert isinstance(results, list)
    assert len(results) <= 5
    for chunk in results:
        assert "text" in chunk
        assert "metadata" in chunk
