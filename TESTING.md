# Nyaya Mitra — Testing & Validation Guide

## Pre-Production Validation

Run these checks before deploying to production:

### 1. Syntax & Import Validation

```bash
# Check all Python files for syntax errors
python -m py_compile *.py models/*.py routers/*.py services/*.py db/*.py

# Verify imports work
python -c "import main; import config; from services import rag_service, gemini_service, drafting_service"

# Check Dockerfile
docker build -t nyaya-test . --progress=plain
```

### 2. Configuration Validation

```bash
# Test .env loading
python validate_installation.py

# Verify environment variables
python -c "from config import *; print(f'GEMINI_MODEL={GEMINI_MODEL}'); print(f'EMBEDDING_DIMENSIONS={EMBEDDING_DIMENSIONS}')"
```

### 3. Dependency Check

```bash
# List all installed packages
pip list

# Check for outdated packages
pip list --outdated

# Security audit
pip install safety
safety check
```

### 4. API Startup Test

```bash
# Start the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, run smoke tests
# Health check
curl -s http://localhost:8000/health | python -m json.tool

# Expected output:
# {
#   "status": "degraded" or "healthy",
#   "vector_store": "not_loaded" or "loaded",
#   "chunks_indexed": <number>,
#   "embedding_model": "models/gemini-embedding-001",
#   "version": "1.0.0"
# }

# Corpus stats
curl -s http://localhost:8000/api/v1/corpus-stats | python -m json.tool
```

### 5. ETL Pipeline Test

```bash
# Ensure Raw_Data/ contains the required PDFs:
# - bns.pdf (Bharatiya Nyaya Sanhita)
# - bnss.pdf (Bharatiya Nagarik Suraksha Sanhita)
# - bsa.pdf (Bharatiya Sakshya Adhiniyam)
# - const.pdf (Constitution of India)

# Run ETL
python etl_pipeline.py

# Expected output:
# ============================================================
# Nyaya Mitra — ETL Pipeline  START
#   DB path    : ./chroma_db
#   Collection : nyaya_mitra_legal
#   Model      : models/gemini-embedding-001
# ============================================================
# [EXTRACT] bns.pdf        nnnn pages  (x.xxs)
# [EXTRACT] bnss.pdf       nnnn pages  (x.xxs)
# ... (and so on for other PDFs)
# [EMBED+LOAD] upserted nnn / nnnn chunks (x.xs)
# ============================================================
# Nyaya Mitra — ETL Pipeline  COMPLETE
#   Chunks ingested : nnnn
#   Collection size : nnnn
#   Total time      : xxx.xs
# ============================================================

# Exit code should be 0
echo $?  # Should print: 0
```

### 6. API Functional Tests

#### Test 1: Legal Query with Valid Input

```bash
curl -X POST http://localhost:8000/api/v1/legal-query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "What is the punishment for theft under BNS?",
    "top_k": 10
  }' | python -m json.tool

# Expected response:
# {
#   "explanation": "...",
#   "citations": ["BNS — Section XXX", ...],
#   "suggested_next_steps": [...],
#   "disclaimer": "⚖️ This is AI-generated...",
#   "latency_ms": 1000
# }
```

#### Test 2: Query with Custom Session ID

```bash
curl -X POST http://localhost:8000/api/v1/legal-query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "What are bail conditions?",
    "top_k": 15,
    "session_id": "test-session-12345"
  }' | python -m json.tool
```

#### Test 3: Query Validation Errors

```bash
# Too short query (min_length=5)
curl -X POST http://localhost:8000/api/v1/legal-query \
  -H "Content-Type: application/json" \
  -d '{"user_query": "abc"}'
# Should return 422 Unprocessable Entity

# Invalid top_k (max=30)
curl -X POST http://localhost:8000/api/v1/legal-query \
  -H "Content-Type: application/json" \
  -d '{"user_query": "What is bail?", "top_k": 100}'
# Should return 422 Unprocessable Entity
```

#### Test 4: Document Drafting

```bash
curl -X POST http://localhost:8000/api/v1/draft-document \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "bail_application",
    "facts": "The accused was arrested on suspicion of theft. No prior criminal record. Financial ties to the community.",
    "accused_name": "John Doe",
    "court": "District Court, New Delhi",
    "sections_charged": ["BNS Section 303", "BNS Section 304"]
  }' | python -m json.tool

# Expected response:
# {
#   "document_type": "Bail Application",
#   "accused_name": "John Doe",
#   "court": "District Court, New Delhi",
#   "draft_content": "...(complete legal document)...",
#   "citations_used": ["BNS — Section 303", ...],
#   "disclaimer": "⚠️ AI-generated legal draft...",
#   "latency_ms": 5000
# }
```

#### Test 5: All Document Types

```bash
for doc_type in bail_application anticipatory_bail fir_draft legal_notice complaint_letter; do
  echo "Testing: $doc_type"
  curl -X POST http://localhost:8000/api/v1/draft-document \
    -H "Content-Type: application/json" \
    -d "{
      \"document_type\": \"$doc_type\",
      \"facts\": \"Test facts for $doc_type\",
      \"accused_name\": \"Test Accused\",
      \"court\": \"Test Court\"
    }" > /dev/null && echo "✓ $doc_type OK" || echo "✗ $doc_type FAILED"
done
```

### 7. Docker Compose Test

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Check backend health
docker exec nyaya-mitra-backend curl -s http://localhost:8000/health | python -m json.tool

# Test through Docker network
docker exec nyaya-mitra-frontend curl -s http://backend:8000/health

# Stop services
docker-compose down

# Cleanup volumes (if needed)
docker-compose down -v
```

### 8. Database Integrity Checks

```bash
# Check SQLite database
sqlite3 nyaya_mitra.db ".tables"
# Should output: drafts  queries  sessions

# Check table schemas
sqlite3 nyaya_mitra.db ".schema"

# Count records
sqlite3 nyaya_mitra.db "SELECT COUNT(*) FROM sessions;"
sqlite3 nyaya_mitra.db "SELECT COUNT(*) FROM queries;"
sqlite3 nyaya_mitra.db "SELECT COUNT(*) FROM drafts;"

# Check WAL mode is enabled
sqlite3 nyaya_mitra.db "PRAGMA journal_mode;"
# Should output: wal

# Check ChromaDB collection
python -c "
from db.chroma_client import ChromaDBClient
ChromaDBClient.initialize()
print(f'Total chunks: {ChromaDBClient.get_chunk_count()}')
print(f'Ready: {ChromaDBClient.is_ready()}')
"
```

### 9. Error Handling Tests

#### Test: ChromaDB Not Initialized

```bash
# Remove chroma_db directory
rm -rf chroma_db/

# Start API
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Query should return 503
curl -X POST http://localhost:8000/api/v1/legal-query \
  -H "Content-Type: application/json" \
  -d '{"user_query": "What is bail?"}' \
  -w "\n%{http_code}\n"
# Should return 503 Service Unavailable

# Kill API
pkill -f uvicorn
```

#### Test: Invalid Document Type

```bash
curl -X POST http://localhost:8000/api/v1/draft-document \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "invalid_type",
    "facts": "Some facts"
  }' \
  -w "\n%{http_code}\n"
# Should return 422 (validation error)
```

#### Test: Missing Template

```bash
# Rename a template temporarily
mv templates/bail_application.txt templates/bail_application.txt.bak

# Try to draft
curl -X POST http://localhost:8000/api/v1/draft-document \
  -H "Content-Type: application/json" \
  -d '{"document_type": "bail_application", "facts": "test"}' \
  -w "\n%{http_code}\n"
# Should return 400

# Restore template
mv templates/bail_application.txt.bak templates/bail_application.txt
```

### 10. Load & Performance Tests

```bash
# Install Apache Bench
apt-get install apache2-utils  # or brew install httpd (Mac)

# Health check load test (100 requests, 10 concurrent)
ab -n 100 -c 10 http://localhost:8000/health

# Query load test
ab -n 20 -c 5 -p query.json -T application/json \
   http://localhost:8000/api/v1/legal-query

# Where query.json contains:
# {"user_query": "What is bail?", "top_k": 5}
```

### 11. Security Tests

```bash
# Check for hardcoded secrets
grep -r "GEMINI_API_KEY" *.py models/*.py routers/*.py services/*.py db/*.py
# Should not find the actual key, only variable references

# Check .gitignore covers secrets
cat .gitignore | grep -E "\.env|__pycache__|\.pyc"

# Verify .env is not in git
git ls-files | grep "\.env"
# Should return nothing

# Check for SQL injection vectors (inspect user inputs)
grep -n "\.format\|f\"\|f'" routers/*.py services/*.py db/*.py | grep -i "query\|sql"
# All database queries should use parameterized queries with ? placeholders
```

### 12. Deployment Pre-Check

```bash
# Verify all required config keys are present
python -c "
from config import *
required = ['GEMINI_API_KEY', 'GEMINI_MODEL', 'EMBEDDING_MODEL', 
            'EMBEDDING_DIMENSIONS', 'CHROMA_DB_PATH', 'SQLITE_DB_PATH',
            'TEMPLATES_DIR', 'CORS_ORIGINS', 'FASTAPI_ENV']
for key in required:
    print(f'{key}: OK')
"

# Verify templates exist
ls -la templates/
# Should list: bail_application.txt, anticipatory_bail.txt, fir_draft.txt, legal_notice.txt, complaint_letter.txt

# Final Dockerfile validation
docker build -t nyaya-final . && echo "✓ Docker build successful"
```

## Continuous Integration Checklist

Use these checks in your CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: CI/CD
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python -m py_compile *.py models/*.py routers/*.py services/*.py db/*.py
      - run: python validate_installation.py
      - run: pytest tests/ -v  # When tests are added
      - run: docker build -t nyaya-test .
```

## Manual Testing Walkthrough

For QA/testers without running code:

1. **Start Backend**: `uvicorn main:app --reload`
2. **Open Swagger UI**: http://localhost:8000/docs
3. **Test Each Endpoint**:
   - Click "Try it out" on each endpoint
   - Provide valid test data
   - Verify response structure matches schema
   - Check latency_ms is reasonable (< 10 seconds)
4. **Test Error Cases**:
   - Try invalid input (too short query, invalid document_type)
   - Verify error messages are clear
   - Check HTTP status codes (400, 422, 503, etc.)
5. **Frontend Testing** (when available):
   - Test chat interface
   - Test document drafting
   - Verify API integration
   - Test error messages

---

**Maintain this checklist and run it before every release.**
