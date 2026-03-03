# 02 — MVP Technical Specification
## Nyaya Mitra — Engineering Blueprint for MVP

**Version:** 1.0.0  
**Date:** March 2026  
**Status:** Active

---

## 1. Technology Stack Decision Matrix

| Layer | Choice | Rationale |
|---|---|---|
| Mobile Frontend | React Native (Expo SDK 51) | Cross-platform iOS/Android from single codebase; Expo Go for rapid iteration |
| Backend API | FastAPI (Python 3.11) | Async, auto-docs via OpenAPI, native Python AI ecosystem integration |
| AI Generation | Google Gemini 2.5 Flash | Best price/performance for long-context RAG; 1M token context window |
| Vector DB | ChromaDB (local, persistent) | Zero-infrastructure for MVP; Postgres-backed upgrade path for production |
| Embeddings | SentenceTransformers `all-MiniLM-L6-v2` | Runs locally, no external API call, 384-dim, fast inference |
| PDF Parsing | LangChain + PyPDF | Battle-tested PDF extraction with page metadata preservation |
| Relational DB | SQLite (MVP) → PostgreSQL (Production) | Stores users, sessions, query history |
| Environment | python-dotenv + .env | Secrets management (API keys never committed to repo) |

---

## 2. RAG Architecture (Transition from BM25 → ChromaDB)

### Previous Implementation (Phase 4 Baseline)
```
User Query → BM25Okapi keyword search over vector_store_mock.json → Gemini → JSON Response
```
**Limitations:**
- BM25 is lexical (bag-of-words); fails on semantic queries ("when can police arrest without warrant?" vs "section 35 BNSS")
- Mock embeddings `[0.1, 0.2, 0.3]` provide zero semantic signal
- JSON file store doesn't scale beyond ~50k chunks

### MVP Target Implementation (ChromaDB RAG)
```
ETL Pipeline:
  PDFs → PyPDFLoader → RecursiveCharacterTextSplitter (1000/200) 
       → SentenceTransformer encode → ChromaDB.add()

Query Pipeline:
  User Query → SentenceTransformer encode → ChromaDB.query(K=15)
             → Top-K chunks + metadata → Gemini 2.5 Flash prompt 
             → Structured JSON → FastAPI Response → React Native UI
```

---

## 3. Data Corpus (MVP)

| File | Content | Approx Pages | Est. Chunks |
|---|---|---|---|
| `bns.pdf` | Bharatiya Nyaya Sanhita 2023 (replaces IPC) | ~200 | ~400 |
| `bnss.pdf` | Bharatiya Nagarik Suraksha Sanhita 2023 (replaces CrPC) | ~300 | ~600 |
| `bsa.pdf` | Bharatiya Sakshya Adhiniyam 2023 (replaces Indian Evidence Act) | ~100 | ~200 |
| `const.pdf` | Constitution of India | ~250 | ~500 |

**Total Estimated Chunks: ~1700**

---

## 4. Embedding Model Specification

```python
Model: sentence-transformers/all-MiniLM-L6-v2
Dimension: 384
Distance Metric: Cosine Similarity
Normalization: L2-normalized embeddings
Max Sequence Length: 256 tokens
Inference: Local CPU (no GPU required for MVP)
Batch Size: 32 (during ETL ingestion)
```

---

## 5. ChromaDB Configuration (MVP)

```python
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(
    name="nyaya_mitra_legal",
    metadata={"hnsw:space": "cosine"}
)
# Fields stored per chunk:
# - documents: [chunk_text]
# - metadatas: [{"source": "bns.pdf", "page": 14, "chunk_id": "bns_p14_c2"}]
# - ids: ["bns_p14_c2_unique_hash"]
# - embeddings: [[384-dim float vector]]
```

---

## 6. FastAPI Endpoint Specification (MVP)

### POST `/api/v1/legal-query`
**Request:**
```json
{"user_query": "What are the sections for theft under BNS?"}
```
**Response:**
```json
{
  "explanation": "Under the Bharatiya Nyaya Sanhita...",
  "citations": ["BNS — Section 303, Page 87"],
  "suggested_next_steps": ["File a complaint at the nearest police station..."]
}
```

### POST `/api/v1/draft-document`
**Request:**
```json
{
  "document_type": "bail_application",
  "facts": "My client was arrested on 2026-03-01...",
  "accused_name": "Ramesh Kumar",
  "court": "Sessions Court, Delhi"
}
```
**Response:**
```json
{
  "draft_content": "IN THE SESSIONS COURT OF DELHI\n\nBAIL APPLICATION\n\n...",
  "citations_used": ["BNSS Section 480", "BNSS Section 483"],
  "disclaimer": "AI-generated draft. Review with qualified advocate before filing."
}
```

---

## 7. React Native Screen Architecture

```
App.js (Navigator)
├── HomeScreen.js          — Landing page, feature overview
├── ChatScreen.js          — Primary RAG Q&A chat (B2C Citizen)
├── DraftScreen.js         — Document type picker + input form (B2B Pro)
├── DraftResultScreen.js   — Rendered draft with export option
└── SettingsScreen.js      — API URL config, tier info
```

---

## 8. Development Environment Requirements

```bash
# Python
Python >= 3.11
pip install -r requirements.txt

# Node / React Native
Node >= 18.x
npm install
npx expo start

# Vector DB population (run once after placing PDFs in Raw_Data/)
python etl_pipeline.py
```

---

## 9. MVP Exclusions

- Authentication / User Accounts (Phase 2)
- Payments / Subscription Management (Phase 2)
- Multi-language support / Hindi NLP (Phase 3)
- PDF Export of drafted documents (Phase 2)
- Admin Dashboard / Analytics (Phase 3)
