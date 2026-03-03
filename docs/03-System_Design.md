# 03 — System Design Document
## Nyaya Mitra — High-Level and Low-Level System Design

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          NYAYA MITRA PLATFORM                               │
│                                                                             │
│  ┌──────────────┐     HTTPS/REST     ┌────────────────────────────────────┐ │
│  │  React Native │ ──────────────── ▶│         FastAPI Backend            │ │
│  │  (Expo)       │                   │         (Python 3.11)              │ │
│  │               │ ◀──────────────── │                                    │ │
│  │  • ChatScreen │   JSON Response   │  ┌──────────────────────────────┐  │ │
│  │  • DraftScreen│                   │  │    RAG Query Engine          │  │ │
│  └──────────────┘                   │  │   ┌──────────────────────┐  │  │ │
│                                     │  │   │  ChromaDB Semantic   │  │  │ │
│  ┌──────────────┐                   │  │   │  Search (K=15)       │  │  │ │
│  │  ETL Pipeline │                   │  │   └──────────┬───────────┘  │  │ │
│  │  (offline)    │                   │  │              │               │  │ │
│  │               │                   │  │   ┌──────────▼───────────┐  │  │ │
│  │  PDFs ──────▶ │ ──── populate ──▶ │  │   │  Gemini 2.5 Flash    │  │  │ │
│  │  ChromaDB     │                   │  │   │  Generation          │  │  │ │
│  └──────────────┘                   │  │   └──────────────────────┘  │  │ │
│                                     │  └──────────────────────────────┘  │ │
│                                     └────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow — Legal Q&A (RAG Pipeline)

```
Step 1: User types query in ChatScreen
        "What punishment for theft under new law?"

Step 2: POST /api/v1/legal-query
        {"user_query": "What punishment for theft under new law?"}

Step 3: FastAPI receives request
        → Calls SentenceTransformer.encode(query) → 384-dim vector

Step 4: ChromaDB semantic search
        → collection.query(query_embeddings=[vector], n_results=15)
        → Returns: [{text, source, page}, ...] × 15 chunks

Step 5: Context assembly
        → Concatenate 15 chunks with source/page metadata
        → Estimated context: ~8,000–10,000 tokens

Step 6: Gemini 2.5 Flash prompt
        → System role: "You are Nyaya Mitra, grounded in Indian law..."
        → User message: context + query
        → generation_config temperature=0.1 (deterministic)

Step 7: JSON parse + validation
        → Extract {explanation, citations, suggested_next_steps}
        → Pydantic validation

Step 8: Response to frontend
        → ChatScreen renders structured card with citation pills
```

---

## 3. Data Flow — Document Drafting Pipeline

```
Step 1: User selects "Bail Application" on DraftScreen
        → Fills form: accused name, facts, court name

Step 2: POST /api/v1/draft-document
        {"document_type": "bail_application", "facts": "...", ...}

Step 3: Backend retrieves relevant legal provisions
        → Query ChromaDB with: "bail application conditions BNSS"
        → K=10 most relevant BNSS / BNS sections

Step 4: Template injection
        → Load template for bail_application from /templates/
        → Merge user facts + legal provisions

Step 5: Gemini generation
        → Output: complete draft document with proper legal formatting

Step 6: Return draft to frontend
        → DraftResultScreen presents scrollable markdown preview
        → "Copy to Clipboard" action
```

---

## 4. Component Interaction Diagram

```
[User] → [React Native App]
                ↓ HTTP POST
         [FastAPI Router]
                ↓
      [RAG Query Service]
         ↙           ↘
[ChromaDB Layer]  [Gemini Client]
         ↓               ↓
  [Chunk Retrieval]  [LLM Generation]
         ↘           ↙
      [Response Builder]
                ↓
      [Pydantic Validator]
                ↓ JSON
         [React Native]
                ↓
         [Chat UI / Draft UI]
```

---

## 5. ChromaDB Schema Design

```
Collection: "nyaya_mitra_legal"
├── id: "bns_p087_c003"          (source_page_chunk UUID)
├── document: "{raw chunk text}"
├── embedding: [384-dim float]
└── metadata:
    ├── source: "bns.pdf"
    ├── page: 87
    ├── chunk_index: 3
    ├── law_code: "BNS"
    └── section_hint: "303"      (extracted via regex if available)
```

---

## 6. SQLite Schema (MVP Session Storage)

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tier TEXT DEFAULT 'free'          -- 'free' | 'pro' | 'enterprise'
);

CREATE TABLE queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id),
    query TEXT NOT NULL,
    response_json TEXT NOT NULL,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id),
    document_type TEXT NOT NULL,
    input_facts TEXT NOT NULL,
    output_draft TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 7. Error Handling Strategy

| Error Type | HTTP Status | Handling |
|---|---|---|
| ChromaDB not initialized | 503 | Return "Service unavailable — vector store loading" |
| Gemini API quota exceeded | 429 | Return "AI service busy — try again in 30s" |
| Gemini returns invalid JSON | 502 | Regex rescue → fallback parse → log and retry 1× |
| No relevant chunks found | 404 | Return "No relevant legal information found" |
| PDF not found in Raw_Data | 500 (ETL) | Log warning, skip file, continue pipeline |

---

## 8. Infrastructure (MVP — Local Development)

```
Developer Machine
├── /backend              FastAPI on :8000
├── /chroma_db            ChromaDB persistent store (local files)
├── /Raw_Data             PDF corpus
└── Expo Dev Server       React Native on :8081

Physical Device / Android Emulator
└── Connects to http://<LAN_IP>:8000
```
