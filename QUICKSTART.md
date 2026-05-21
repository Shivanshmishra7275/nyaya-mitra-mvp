# Nyaya Mitra — Quick Start for Developers

**Get the entire application running in 5 minutes.**

## Prerequisites

- Python 3.10+
- Docker & Docker Compose (optional, but recommended)
- Google Gemini API key from https://aistudio.google.com/app/apikey
- Git

## Option A: Local Development (5 min)

### Step 1: Clone & Setup (1 min)

```bash
git clone https://github.com/Shivanshmishra7275/nyaya-mitra-mvp.git
cd nyaya-mitra-mvp

# Copy environment template
cp .env.example .env

# Edit .env and add your Gemini API key
# GEMINI_API_KEY=your_actual_key_here
```

### Step 2: Install Dependencies (2 min)

```bash
# Create virtual environment
python -m venv .venv

# Activate (choose your OS)
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### Step 3: Run ETL Pipeline (1 min)

```bash
# Download the 4 required PDFs into Raw_Data/ first:
# - bns.pdf (Bharatiya Nyaya Sanhita)
# - bnss.pdf (Bharatiya Nagarik Suraksha Sanhita)
# - bsa.pdf (Bharatiya Sakshya Adhiniyam)
# - const.pdf (Constitution of India)

# Then run the ETL pipeline
python etl_pipeline.py

# Should complete with: "✓ Chunks ingested: ~1700"
```

### Step 4: Start Backend (1 min)

```bash
# Terminal 1: Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Should log: "Nyaya Mitra API ready."
```

### Step 5: Test It

```bash
# Terminal 2: Test the API
curl -X POST http://localhost:8000/api/v1/legal-query \
  -H "Content-Type: application/json" \
  -d '{"user_query": "What is bail?", "top_k": 10}'

# Should return a JSON response with legal explanation and citations
```

**Done!** ✅ API is running. See http://localhost:8000/docs for interactive docs.

---

## Option B: Docker (3 min)

### Step 1: Prepare Environment

```bash
cp .env.example .env
# Edit .env to add GEMINI_API_KEY
```

### Step 2: Build & Run

```bash
# Download PDFs into Raw_Data/ first

# Build and start
docker-compose build
docker-compose up -d

# Wait 30 seconds for services to start
sleep 30

# Verify
curl http://localhost:8000/health
```

**Done!** ✅  
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

---

## Common Tasks

### Test a Legal Query

```bash
curl -X POST http://localhost:8000/api/v1/legal-query \
  -H "Content-Type: application/json" \
  -d '{
    "user_query": "What is the punishment for theft under BNS?",
    "top_k": 15
  }' | python -m json.tool
```

### Generate a Document

```bash
curl -X POST http://localhost:8000/api/v1/draft-document \
  -H "Content-Type: application/json" \
  -d '{
    "document_type": "bail_application",
    "facts": "The accused was arrested on suspicion of theft with no prior criminal record.",
    "accused_name": "John Doe",
    "court": "District Court, New Delhi",
    "sections_charged": ["BNS Section 303"]
  }' | python -m json.tool
```

### Check API Health

```bash
curl http://localhost:8000/health | python -m json.tool
```

### View API Documentation

Open http://localhost:8000/docs in your browser and try endpoints interactively.

---

## File Structure

```
nyaya-mitra-mvp/
├── main.py                    # FastAPI application factory
├── config.py                  # Centralized configuration
├── etl_pipeline.py            # PDF ingestion & embedding
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Container build
├── docker-compose.yml         # Multi-service orchestration
│
├── models/                    # Pydantic schemas
│   ├── request_models.py
│   └── response_models.py
│
├── routers/                   # API endpoints
│   ├── health.py
│   ├── legal_query.py
│   └── document_draft.py
│
├── services/                  # Business logic
│   ├── rag_service.py        # ChromaDB retrieval
│   ├── gemini_service.py     # LLM prompting
│   └── drafting_service.py   # Document generation
│
├── db/                        # Data layer
│   ├── chroma_client.py      # Vector DB client
│   └── sqlite_client.py      # Session logging
│
├── templates/                 # Document templates
│   ├── bail_application.txt
│   ├── anticipatory_bail.txt
│   ├── fir_draft.txt
│   ├── legal_notice.txt
│   └── complaint_letter.txt
│
├── Raw_Data/                  # PDF corpus (add here)
│   ├── bns.pdf
│   ├── bnss.pdf
│   ├── bsa.pdf
│   └── const.pdf
│
├── chroma_db/                 # Vector store (auto-generated)
│
├── .env.example               # Config template
├── .gitignore                 # Git exclusions
├── README.md                  # Full documentation
├── DEPLOYMENT.md              # Production guide
├── TESTING.md                 # Test procedures
└── KNOWN_ISSUES.md            # Issue tracking
```

---

## Core Concepts

### RAG Pipeline (Retrieval-Augmented Generation)

1. **User Query** → "What is bail?"
2. **Embed Query** → Convert to vector via Gemini
3. **Retrieve** → Find top-k similar legal chunks from ChromaDB
4. **Assemble Context** → Format chunks with metadata
5. **Generate Response** → Call Gemini with context + system prompt
6. **Return** → JSON with explanation, citations, next steps

### Document Drafting

1. **User Provides** → Facts, accused name, charges
2. **Template Loaded** → Get document template
3. **Retrieve Provisions** → Find relevant legal sections
4. **Generate Draft** → Fill template with Gemini generation
5. **Extract Citations** → Parse draft for cited sections
6. **Return** → Complete legal document

---

## Troubleshooting

### Error: GEMINI_API_KEY not found

```
ValueError: GEMINI_API_KEY is missing
```

**Fix**: Add your API key to `.env`:
```
GEMINI_API_KEY=your_actual_key_here
```

### Error: No documents loaded

```
etl_pipeline.py: No documents loaded. Aborting.
```

**Fix**: Ensure `Raw_Data/` contains the 4 required PDFs:
- bns.pdf
- bnss.pdf
- bsa.pdf
- const.pdf

### Error: ChromaDB collection is empty

```
WARNING: ChromaDB collection is empty.
```

**Fix**: Run `python etl_pipeline.py` to populate the vector store.

### Error: Port 8000 already in use

```
OSError: [Errno 48] Address already in use
```

**Fix**: Kill the process or use a different port:
```bash
# Find and kill the process on port 8000
lsof -i :8000 | awk 'NR!=1 {print $2}' | xargs kill -9

# Or use a different port
uvicorn main:app --port 8001
```

### Error: Docker build fails

```
docker build error: permission denied
```

**Fix**: Ensure Docker daemon is running and you have permissions:
```bash
# macOS/Linux: use sudo or add user to docker group
sudo docker-compose build

# Or check Docker status
docker ps
```

---

## Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `GEMINI_API_KEY` | ✅ YES | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.5-flash` | Model version |
| `EMBEDDING_MODEL` | No | `models/gemini-embedding-001` | Embedding model ID |
| `RAG_TOP_K` | No | `15` | Number of chunks to retrieve |
| `FASTAPI_ENV` | No | `development` | `development` or `production` |
| `LOG_LEVEL` | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `UVICORN_WORKERS` | No | `1` | Number of Uvicorn workers (production) |

---

## API Endpoints

### Health

```
GET /health
GET /api/v1/corpus-stats
```

### Legal Q&A

```
POST /api/v1/legal-query
Input:  {user_query: str, top_k?: int, session_id?: str}
Output: {explanation: str, citations: [str], suggested_next_steps: [str], disclaimer: str, latency_ms: int}
```

### Document Drafting

```
POST /api/v1/draft-document
Input:  {
  document_type: "bail_application" | "anticipatory_bail" | "fir_draft" | "legal_notice" | "complaint_letter",
  facts: str,
  accused_name?: str,
  court?: str,
  sections_charged?: [str],
  session_id?: str
}
Output: {document_type: str, draft_content: str, citations_used: [str], disclaimer: str, latency_ms: int}
```

---

## Testing Your Changes

Before committing code:

```bash
# 1. Validate syntax
python -m py_compile *.py models/*.py routers/*.py services/*.py db/*.py

# 2. Run installation validation
python validate_installation.py

# 3. Test Docker build
docker build -t nyaya-test .

# 4. Verify API works
uvicorn main:app --reload &
sleep 2
curl http://localhost:8000/health
```

---

## Getting Help

1. **Check Logs**: `tail -f app.log` or use `LOG_LEVEL=DEBUG`
2. **Read Docs**: http://localhost:8000/docs (interactive Swagger)
3. **Browse Code**: Start with `main.py`, then explore routers
4. **Run Tests**: See `TESTING.md` for comprehensive test procedures
5. **Issue Tracking**: See `KNOWN_ISSUES.md` for known problems and Phase 2 work

---

## Next Steps After Setup

1. **Explore the Codebase**:
   - Read `main.py` to understand app structure
   - Review `routers/` to see API endpoints
   - Check `services/` to understand business logic

2. **Understand the RAG Pipeline**:
   - Read `services/rag_service.py` for retrieval logic
   - Read `services/gemini_service.py` for generation

3. **Make Your First Change**:
   - Try tuning RAG prompts in `services/gemini_service.py`
   - Try adding a new document type to `services/drafting_service.py`
   - Try adjusting error messages in `routers/legal_query.py`

4. **Run the Full Test Suite**:
   - Follow `TESTING.md` for comprehensive validation

---

**Questions?** Start with the README.md or DEPLOYMENT.md  
**Found a bug?** See KNOWN_ISSUES.md and add to the tracking  
**Ready for production?** Follow DEPLOYMENT.md step-by-step

Happy coding! 🚀
