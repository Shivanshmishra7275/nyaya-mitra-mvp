# 04 — Software Architecture Document
## Nyaya Mitra — Enterprise Software Architecture

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. Architecture Principles

| Principle | Application in Nyaya Mitra |
|---|---|
| **Separation of Concerns** | ETL, RAG retrieval, generation, and presentation are isolated modules |
| **Grounding over Generation** | LLM output is ALWAYS grounded in retrieved corpus — no pure generation |
| **Fail Loudly** | Prefer explicit HTTP error codes over silent fallbacks |
| **Stateless API** | FastAPI endpoints are stateless; session state lives in SQLite/client |
| **Single Source of Truth** | ChromaDB is the sole retrieval layer; no dual-indexes in MVP |
| **Config over Code** | All tunables (K, chunk_size, temperature) are constants in config.py |

---

## 2. Layered Architecture

```
┌─────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                  │
│  React Native (Expo) — ChatScreen, DraftScreen      │
├─────────────────────────────────────────────────────┤
│                  API GATEWAY LAYER                   │
│  FastAPI — Router, CORS, Pydantic validation        │
├─────────────────────────────────────────────────────┤
│                  APPLICATION LAYER                   │
│  RAGQueryService, DocumentDraftingService           │
├─────────────────────────────────────────────────────┤
│                  DOMAIN LAYER                        │
│  ChromaDB retrieval, Embedding service              │
├─────────────────────────────────────────────────────┤
│                  INFRASTRUCTURE LAYER                │
│  ChromaDB persistent store, SQLite, Gemini HTTP     │
└─────────────────────────────────────────────────────┘
```

---

## 3. Backend Module Architecture

```
backend/
├── main.py                    — FastAPI app factory + lifespan manager
├── config.py                  — All environment variables + tunables
├── routers/
│   ├── legal_query.py         — POST /api/v1/legal-query
│   └── document_draft.py      — POST /api/v1/draft-document
├── services/
│   ├── rag_service.py         — ChromaDB query + context assembly
│   ├── gemini_service.py      — Gemini API client + prompt management
│   └── drafting_service.py    — Template loading + draft generation
├── models/
│   ├── request_models.py      — Pydantic request schemas
│   └── response_models.py     — Pydantic response schemas
├── db/
│   ├── chroma_client.py       — ChromaDB singleton client
│   └── sqlite_client.py       — SQLite session/query logging
└── templates/
    ├── bail_application.txt
    ├── fir_draft.txt
    ├── legal_notice.txt
    └── complaint_letter.txt
```

---

## 4. Frontend Module Architecture

```
nyaya-mitra-app/
├── App.js                     — Root navigator (Stack/Tab)
├── screens/
│   ├── HomeScreen.js          — Onboarding + feature overview
│   ├── ChatScreen.js          — RAG Q&A chat interface
│   ├── DraftScreen.js         — Document drafting form
│   ├── DraftResultScreen.js   — Draft preview + copy
│   └── SettingsScreen.js      — Config + tier info
├── components/
│   ├── CitationPill.js        — Reusable citation tag
│   ├── NextStepItem.js        — Reusable action item
│   ├── AiMessageCard.js       — Structured AI response card
│   ├── UserBubble.js          — User message bubble
│   └── LoadingDots.js         — Animated loading indicator
├── services/
│   └── apiService.js          — Axios-based API client
├── constants/
│   ├── Colors.js              — Design system color tokens
│   └── ApiConfig.js           — Base URL + endpoint paths
└── utils/
    └── formatters.js          — Text formatting helpers
```

---

## 5. ETL Pipeline Architecture

```
etl_pipeline.py
├── Configuration block        — RAW_DATA_DIR, OUTPUT_DIR, CHUNK_SIZE
├── extract_documents()        — PyPDFLoader, returns List[Document]
├── transform_chunks()         — RecursiveCharacterTextSplitter, metadata injection
├── generate_embeddings()      — SentenceTransformer.encode(), batch=32
├── load_to_chromadb()         — ChromaDB add() with upsert capability
└── main()                     — Orchestrates the full pipeline with timing logs
```

---

## 6. Key Design Decisions

### 6.1 Why ChromaDB over Pinecone/Weaviate for MVP?
- **Zero cost:** ChromaDB is free and runs locally
- **Zero infra:** No Docker, no cloud account needed for MVP
- **Migration path:** ChromaDB+PGVector or Pinecone serverless for production
- **Familiar API:** Python-native, minimal boilerplate

### 6.2 Why `all-MiniLM-L6-v2` for Embeddings?
- **No API key required:** Runs locally via SentenceTransformers
- **Legal domain performance:** Adequate for BM25→semantic upgrade in Indian legal texts
- **Speed:** ~50ms per batch of 32 chunks on CPU
- **Future upgrade:** Can swap to `intfloat/multilingual-e5-large` for Hindi support

### 6.3 Why Gemini 2.5 Flash vs GPT-4?
- **Long context:** 1M token context window handles full BNS corpus if needed
- **Price:** ~10× cheaper than GPT-4o at similar quality for constrained legal tasks
- **Indian law performance:** Better training representation of Indian legal texts
- **Temperature 0.1:** Minimizes hallucination for legal domain

### 6.4 Why Not a Vector Database Only (No BM25 Fallback)?
For MVP, pure semantic search with quality embeddings outperforms hybrid BM25+semantic for a structured legal corpus. Hybrid search (reciprocal rank fusion) will be introduced in Phase 2 when query volume justifies the complexity.

---

## 7. Security Architecture (MVP)

```
API Key Management:
  GEMINI_API_KEY → .env (never committed) → os.getenv()

CORS Policy (MVP — open for local dev):
  allow_origins=["*"]  ⚠ Locked to specific origins in production

Input Sanitization:
  Pydantic models enforce type + length constraints
  max_length=2000 on user_query to prevent prompt injection

No PII Storage (MVP):
  Session IDs are UUID-only
  Query text logged for debugging but not tied to user identity
```

---

## 8. Scalability Path

```
MVP (Now)           → Phase 2              → Phase 3 (Enterprise)
─────────────────────────────────────────────────────────────────
Local ChromaDB      → PGVector on RDS      → Pinecone/Weaviate cloud
SQLite sessions     → PostgreSQL RDS       → Multi-tenant PostgreSQL
Single FastAPI      → Gunicorn workers     → K8s on EKS
Gemini API          → Gemini API + cache   → Gemini + fallback GPT-4o
Expo dev build      → EAS Production Build → Web + iOS + Android stores
```
