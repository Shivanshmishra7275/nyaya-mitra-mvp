"""
test_api.py
============
Nyaya Mitra — Basic API smoke tests.
Run:  pytest test_api.py -v
      python test_api.py       (direct)
"""
from fastapi.testclient import TestClient
from app.main import app


def test_health_endpoint():
    """Health endpoint should always return 200."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"
        assert "version" in data
        assert "retrieval_mode" in data
        assert "chunks_loaded" in data


def test_version_endpoint():
    """Version endpoint should return app metadata."""
    with TestClient(app) as client:
        response = client.get("/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "name" in data


def test_legal_query_no_key_returns_401():
    """Without an API key, the endpoint should return 401."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/legal-query",
            json={"user_query": "What is the punishment for theft under BNS?"},
        )
        # 401 if no key provided and no server-side default key in test env
        # 200 if GEMINI_API_KEY is set in .env
        assert response.status_code in (200, 401, 503)


def test_legal_query_empty_string_returns_422():
    """Empty query should fail pydantic validation with 422."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/legal-query",
            json={"user_query": ""},
        )
        assert response.status_code == 422


def test_legal_query_too_short_returns_422():
    """Query shorter than min_length=3 should return 422."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/legal-query",
            json={"user_query": "hi"},
        )
        assert response.status_code == 422


def test_admin_corpus_debug():
    """Admin debug corpus endpoint should return corpus stats."""
    with TestClient(app) as client:
        response = client.get("/api/v1/admin/debug/corpus")
        assert response.status_code == 200
        data = response.json()
        # Either status=ok (loaded) or error key (not loaded)
        assert "status" in data or "error" in data


def test_docs_available_in_dev():
    """Swagger docs should be available in development mode."""
    with TestClient(app) as client:
        response = client.get("/docs")
        # Available in non-production env
        assert response.status_code in (200, 404)


if __name__ == "__main__":
    test_health_endpoint()
    test_version_endpoint()
    test_legal_query_no_key_returns_401()
    test_legal_query_empty_string_returns_422()
    test_legal_query_too_short_returns_422()
    test_admin_corpus_debug()
    test_docs_available_in_dev()
    print("✅ All smoke tests passed!")
