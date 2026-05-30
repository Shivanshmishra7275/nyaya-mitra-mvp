"""
tests/test_api.py
==================
Nyaya Mitra backend tests.
Run with: pytest tests/ -v

Tests cover:
  - /health endpoint (including retrieval_mode field)
  - /version endpoint
  - /api/v1/legal-query input validation
  - /api/v1/legal-query missing API key (401)
  - BM25 retriever unit test
  - HybridRetriever BM25-only path
  - QdrantRetriever graceful failure (returns [] when Qdrant is unreachable)
  - E2E smoke path: /health → BM25 retrieve → LLM skipped (no key required for retrieval)
"""
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.retrieval.bm25_retriever import BM25Retriever
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.qdrant_retriever import QdrantRetriever


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


# ─── HybridRetriever BM25-only path ──────────────────────────────────────────

def test_hybrid_retriever_bm25_only():
    """HybridRetriever without Qdrant returns BM25 results and correct mode note."""
    bm25 = BM25Retriever(store_path="vector_store_mock.json")
    bm25.load()
    hybrid = HybridRetriever(bm25=bm25, qdrant_retriever=None)

    results, note = hybrid.retrieve("murder punishment BNS", top_k=5)
    assert isinstance(results, list)
    assert len(results) <= 5
    assert "BM25-only" in note
    assert "Retrieved" in note


# ─── QdrantRetriever graceful failure ─────────────────────────────────────────

def test_qdrant_retriever_returns_empty_when_unreachable():
    """
    QdrantRetriever.retrieve() must return an empty list (not raise)
    when Qdrant is not running. This ensures HybridRetriever always degrades
    gracefully to BM25-only.
    """
    retriever = QdrantRetriever(host="localhost", port=19999)  # intentionally wrong port
    # load() will fail but should not raise — returns False
    ok = retriever.load()
    assert ok is False
    assert not retriever.is_ready

    # retrieve() on an unready retriever must return [] not raise
    results = retriever.retrieve("theft")
    assert results == []


# ─── HybridRetriever with failing Qdrant degrades to BM25 ────────────────────

def test_hybrid_retriever_degrades_when_qdrant_fails():
    """
    If the Qdrant retriever is wired but fails during retrieve(),
    HybridRetriever must still return BM25 results.
    """
    bm25 = BM25Retriever(store_path="vector_store_mock.json")
    bm25.load()

    # Mock a Qdrant retriever that always raises on retrieve()
    bad_qdrant = MagicMock()
    bad_qdrant.retrieve.side_effect = RuntimeError("Qdrant timeout")

    hybrid = HybridRetriever(bm25=bm25, qdrant_retriever=bad_qdrant)
    results, note = hybrid.retrieve("theft punishment", top_k=5)

    # Should still return BM25 results
    assert len(results) > 0
    assert "unavailable" in note or "BM25" in note


# ─── E2E smoke: health + BM25 retrieval path ──────────────────────────────────

def test_e2e_smoke_health_and_retrieval_path(client):
    """
    End-to-end smoke test:
    1. /health returns 200 with chunks_loaded > 0
    2. The retrieval system is wired and returning results for a real query
       (LLM step is not tested here — requires a live API key)
    """
    # Step 1: health check confirms server and retrieval are ready
    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "ok"
    assert body["chunks_loaded"] > 0, (
        "No chunks loaded — run: python etl_pipeline.py"
    )
    assert body["retrieval_mode"] in (
        "BM25-only",
        "Hybrid (BM25 + Semantic)",
        "BM25-only (Qdrant unavailable)",
    )

    # Step 2: retrieval path directly (bypass LLM)
    retriever = BM25Retriever(store_path="vector_store_mock.json")
    retriever.load()
    results = retriever.retrieve("theft punishment section BNS", top_k=3)
    assert len(results) > 0, "BM25 returned no results for a common legal query"
    # Each result must have text + metadata (source, page) for citation
    for chunk in results:
        assert "text" in chunk and len(chunk["text"]) > 10
        assert "metadata" in chunk
        assert "source" in chunk["metadata"]
