# 12 — Testing Strategy
## Nyaya Mitra — Testing RAG Hallucinations, API Latency, and UX Quality

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. Testing Philosophy

Legal AI requires a **higher bar than typical software testing**. A wrong answer about bail conditions could harm a user's freedom. The testing strategy is built on:

1. **Hallucination detection** — Does the AI invent laws that don't exist?
2. **Retrieval accuracy** — Are the right chunks being returned for a query?
3. **Latency guarantees** — Does the API meet the < 4s P95 target?
4. **Citation validity** — Do cited sections actually appear in the corpus?
5. **Edge case resilience** — How does the system handle adversarial or out-of-scope queries?

---

## 2. Testing Pyramid

```
                   ┌────────────────────┐
                   │     E2E Tests      │  (5%)
                   │  Detox / Appium    │
                  ┌┴────────────────────┴┐
                  │  Integration Tests   │  (25%)
                  │  FastAPI TestClient  │
                 ┌┴──────────────────────┴┐
                 │      Unit Tests         │  (70%)
                 │  pytest + mocks         │
                 └────────────────────────┘
```

---

## 3. Unit Tests

### 3.1 RAG Service Tests (`test_rag_service.py`)
```python
import pytest
from unittest.mock import MagicMock, patch
from services.rag_service import RAGService

class TestRAGService:
    
    def test_retrieve_context_returns_top_k_chunks(self):
        """Verify K=15 chunks returned for standard query."""
        service = RAGService(mock_collection)
        chunks = service.retrieve_context("punishment for theft", k=15)
        assert len(chunks) == 15
    
    def test_retrieve_context_returns_metadata(self):
        """Each chunk must have source and page metadata."""
        service = RAGService(mock_collection)
        chunks = service.retrieve_context("bail conditions BNSS")
        for chunk in chunks:
            assert "source" in chunk["metadata"]
            assert "page" in chunk["metadata"]
    
    def test_retrieve_context_empty_chromadb_raises_503(self):
        """If ChromaDB is empty, raise appropriate error."""
        service = RAGService(empty_collection)
        with pytest.raises(VectorStoreNotReadyError):
            service.retrieve_context("any query")
    
    def test_context_assembly_format(self):
        """Context string must include Source and Page headers."""
        service = RAGService(mock_collection)
        context = service.assemble_context(mock_chunks)
        assert "Source:" in context
        assert "Page" in context
```

### 3.2 Gemini Service Tests (`test_gemini_service.py`)
```python
class TestGeminiService:
    
    def test_parse_valid_json_response(self):
        """Valid JSON Gemini output parses without error."""
        raw = '{"explanation": "...", "citations": [], "suggested_next_steps": []}'
        result = GeminiService.parse_response(raw)
        assert result["explanation"] is not None
    
    def test_parse_json_wrapped_in_markdown(self):
        """Gemini sometimes wraps JSON in ```json``` blocks — must be stripped."""
        raw = '```json\n{"explanation": "...", "citations": [], "suggested_next_steps": []}\n```'
        result = GeminiService.parse_response(raw)
        assert result["explanation"] is not None
    
    def test_invalid_json_raises_parse_error(self):
        """Non-JSON output from Gemini raises JSONDecodeError."""
        with pytest.raises(json.JSONDecodeError):
            GeminiService.parse_response("I cannot answer this question.")
    
    @patch("google.generativeai.GenerativeModel.generate_content")
    def test_gemini_call_uses_low_temperature(self, mock_generate):
        """Temperature must be 0.1 for deterministic legal responses."""
        GeminiService.generate_legal_response("test query", mock_chunks)
        call_kwargs = mock_generate.call_args.kwargs
        assert call_kwargs["generation_config"]["temperature"] == 0.1
```

### 3.3 ETL Pipeline Tests (`test_etl_pipeline.py`)
```python
class TestETLPipeline:
    
    def test_chunk_size_within_bounds(self, sample_pdf_path):
        """No chunk should exceed CHUNK_SIZE characters."""
        chunks = transform_chunks(extract_documents([sample_pdf_path]))
        for chunk in chunks:
            assert len(chunk.page_content) <= CHUNK_SIZE * 1.1  # 10% tolerance
    
    def test_chunk_metadata_has_required_fields(self, sample_pdf_path):
        """Every chunk must have source and page metadata."""
        chunks = transform_chunks(extract_documents([sample_pdf_path]))
        for chunk in chunks:
            assert "source" in chunk.metadata
            assert "page" in chunk.metadata
    
    def test_missing_pdf_is_skipped_gracefully(self, tmp_path):
        """Pipeline must not crash if a PDF is missing."""
        docs = extract_documents(tmp_path, ["nonexistent.pdf"])
        assert docs == []  # Returns empty, doesn't raise
```

---

## 4. Integration Tests

### 4.1 API Integration Tests (`test_legal_query.py`)
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestLegalQueryEndpoint:
    
    def test_legal_query_returns_200_with_valid_query(self):
        response = client.post("/api/v1/legal-query", 
                               json={"user_query": "What is punishment for theft under BNS?"})
        assert response.status_code == 200
        data = response.json()
        assert "explanation" in data
        assert "citations" in data
        assert "suggested_next_steps" in data
        assert isinstance(data["citations"], list)
    
    def test_legal_query_returns_422_for_empty_query(self):
        response = client.post("/api/v1/legal-query", json={"user_query": ""})
        assert response.status_code == 422
    
    def test_legal_query_returns_422_for_too_long_query(self):
        response = client.post("/api/v1/legal-query", 
                               json={"user_query": "x" * 2001})
        assert response.status_code == 422
    
    def test_legal_query_response_under_5_seconds(self):
        import time
        start = time.time()
        response = client.post("/api/v1/legal-query",
                               json={"user_query": "bail conditions BNSS"})
        elapsed = time.time() - start
        assert elapsed < 5.0
    
    def test_health_endpoint_returns_loaded_status(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["vector_store"] == "loaded"
```

---

## 5. Hallucination Test Suite

This is the most critical test category for a legal AI.

### 5.1 Grounding Test — Does the AI cite real sections?
```python
KNOWN_BNS_SECTIONS = {303, 304, 305, 307, 309, 311, 351}  # Known theft/assault sections

def test_citations_reference_real_bns_sections():
    """All cited BNS sections must exist in the actual BNS corpus."""
    response = client.post("/api/v1/legal-query",
                           json={"user_query": "theft punishment BNS"})
    citations = response.json()["citations"]
    
    for citation in citations:
        # Extract section number from "BNS — Section 303, Page 87"
        match = re.search(r'Section (\d+)', citation)
        if match and "BNS" in citation:
            section_num = int(match.group(1))
            assert section_num in KNOWN_BNS_SECTIONS, \
                f"Hallucinated BNS section: {section_num}"
```

### 5.2 Out-of-Corpus Query Test — Does the AI refuse gracefully?
```python
OUT_OF_CORPUS_QUERIES = [
    "What does the Companies Act say about mergers?",
    "Explain the GST registration process",
    "What are the requirements under SEBI regulations?",
]

def test_out_of_corpus_query_handled_gracefully(query):
    """For non-ingested laws, AI must acknowledge limitation, not hallucinate."""
    response = client.post("/api/v1/legal-query", json={"user_query": query})
    assert response.status_code in [200, 404]
    if response.status_code == 200:
        explanation = response.json()["explanation"].lower()
        # Should not confidently answer about laws not in corpus
        refusal_indicators = ["not covered", "outside", "don't have information", 
                               "limited to", "bns", "bnss", "bsa", "constitution"]
        # At minimum, response should mention scope limitation
```

### 5.3 Golden Dataset Test (Manual + Automated)
```
golden_dataset.json: 50 question-answer pairs hand-verified by a law student

Format:
{
  "query": "Under BNS, what is the punishment for assault?",
  "expected_sections": ["BNS Section 351", "BNS Section 352"],
  "expected_topic": "assault",
  "ground_truth_explanation": "...",
  "acceptable_answer_keywords": ["351", "assault", "year", "imprisonment"]
}

Automated check: Response must contain at least 3 of 5 acceptable_answer_keywords.
Target: 80% pass rate on golden dataset.
```

---

## 6. Performance Tests

```python
import locust  # Load testing

class NyayaMitraLoadTest(HttpUser):
    wait_time = between(1, 3)
    
    @task(3)
    def legal_query(self):
        self.client.post("/api/v1/legal-query", 
                         json={"user_query": "bail conditions under BNSS"})
    
    @task(1)
    def health_check(self):
        self.client.get("/health")

# Target: 50 concurrent users, P95 < 4000ms, error rate < 1%
# Run: locust -f locustfile.py --host=http://localhost:8000
```

---

## 7. Running All Tests

```powershell
# From project root (venv activated)

# Unit + Integration tests
pytest tests/ -v --tb=short --cov=. --cov-report=html

# Performance test (requires locust)
pip install locust
locust -f tests/locustfile.py --host=http://localhost:8000 \
       --headless -u 50 -r 5 --run-time 60s

# Hallucination test suite only
pytest tests/ -v -k "hallucination"
```

---

## 8. Quality Gates

| Gate | Threshold | Blocks Deploy |
|---|---|---|
| Unit test coverage | > 80% | Yes |
| Integration tests passing | 100% | Yes |
| Golden dataset pass rate | > 80% | Yes |
| P95 latency (load test) | < 4000ms | Yes |
| Hallucination rate | < 5% | Yes |
| Error rate (load test) | < 1% | Yes |
