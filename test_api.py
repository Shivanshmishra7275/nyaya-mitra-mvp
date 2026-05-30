from fastapi.testclient import TestClient
from main import app, retrieve_context

def test_legal_query():
    with TestClient(app) as client:
        response = client.get("/docs")
        assert response.status_code == 200

        chunks = retrieve_context("murder")
        assert isinstance(chunks, list)
        
if __name__ == "__main__":
    test_legal_query()
    print("Tests passed!")
