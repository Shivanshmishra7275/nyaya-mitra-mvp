# 05 — Database Schema
## Nyaya Mitra — PostgreSQL Relational Schema + ChromaDB Vector Schema

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. Overview

Nyaya Mitra uses two database layers:
1. **ChromaDB** — Vector store for semantic chunk retrieval (RAG core)
2. **PostgreSQL** (SQLite for MVP) — Relational store for users, sessions, queries, billing

---

## 2. ChromaDB Vector Schema

### Collection: `nyaya_mitra_legal`

```python
# Collection metadata
collection_config = {
    "name": "nyaya_mitra_legal",
    "metadata": {
        "hnsw:space": "cosine",            # Similarity metric
        "hnsw:construction_ef": 100,       # HNSW build accuracy
        "hnsw:search_ef": 50,              # Query-time accuracy
        "description": "Indian legal corpus — BNS, BNSS, BSA, Constitution"
    }
}

# Per-document (chunk) schema
chunk_schema = {
    "id": "bns_p087_c003",                 # {law_code}_{page}_{chunk_index}
    "document": "Section 303 — Theft...",  # Raw chunk text (max 1000 chars)
    "embedding": [0.123, -0.456, ...],     # 384-dim float32 (all-MiniLM-L6-v2)
    "metadata": {
        "source": "bns.pdf",               # Source PDF filename
        "page": 87,                        # Page number in PDF
        "chunk_index": 3,                  # Chunk number within page
        "law_code": "BNS",                 # Human-readable law identifier
        "section_hint": "303",             # Section number (regex-extracted)
        "word_count": 187,                 # Token budget awareness
        "ingested_at": "2026-03-01T10:00:00Z"
    }
}
```

### ChromaDB Performance Notes
- Estimated documents: ~1,700 chunks
- Memory footprint: ~1700 × 384 × 4 bytes ≈ **2.6 MB** (fits in RAM easily)
- Query latency: ~5–20ms for K=15 retrieval on local CPU

---

## 3. PostgreSQL Relational Schema

### 3.1 `users` Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    name VARCHAR(255),
    tier VARCHAR(20) NOT NULL DEFAULT 'free',  -- 'free' | 'pro' | 'enterprise'
    org_id UUID REFERENCES organizations(id),  -- NULL for B2C users
    daily_query_count INTEGER NOT NULL DEFAULT 0,
    daily_query_reset_at DATE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    is_active BOOLEAN DEFAULT TRUE
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_org ON users(org_id);
```

### 3.2 `organizations` Table (B2B Enterprise)
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255),                        -- For SSO domain matching
    tier VARCHAR(20) DEFAULT 'enterprise',
    seat_count INTEGER DEFAULT 10,
    api_key_hash TEXT,                          -- Hashed API key for server-to-server
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 3.3 `sessions` Table
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    started_at TIMESTAMPTZ DEFAULT now(),
    ended_at TIMESTAMPTZ,
    device_type VARCHAR(50),                    -- 'android' | 'ios' | 'web'
    app_version VARCHAR(20)
);
CREATE INDEX idx_sessions_user ON sessions(user_id);
```

### 3.4 `queries` Table (Legal Q&A Log)
```sql
CREATE TABLE queries (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    user_id UUID REFERENCES users(id),
    query_text TEXT NOT NULL CHECK (char_length(query_text) <= 2000),
    response_explanation TEXT,
    response_citations JSONB,                   -- ["BNS Section 303, Page 87"]
    response_next_steps JSONB,
    chunks_retrieved INTEGER,
    retrieval_latency_ms INTEGER,
    generation_latency_ms INTEGER,
    total_latency_ms INTEGER,
    gemini_tokens_used INTEGER,
    feedback_score SMALLINT CHECK (feedback_score IN (1, -1)),  -- thumbs up/down
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_queries_user ON queries(user_id);
CREATE INDEX idx_queries_created ON queries(created_at DESC);
```

### 3.5 `drafts` Table (Document Drafting Log)
```sql
CREATE TABLE drafts (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    session_id UUID REFERENCES sessions(id),
    document_type VARCHAR(50) NOT NULL,         -- 'bail_application' | 'fir_draft' | 'legal_notice'
    input_facts TEXT NOT NULL,
    accused_name VARCHAR(255),
    court_name VARCHAR(255),
    output_draft TEXT NOT NULL,
    citations_used JSONB,
    disclaimer TEXT,
    gemini_tokens_used INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_drafts_user ON drafts(user_id);
CREATE INDEX idx_drafts_type ON drafts(document_type);
```

### 3.6 `subscriptions` Table (Phase 2)
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    org_id UUID REFERENCES organizations(id),
    plan VARCHAR(20) NOT NULL,                  -- 'pro_monthly' | 'enterprise_annual'
    status VARCHAR(20) DEFAULT 'active',        -- 'active' | 'cancelled' | 'past_due'
    razorpay_subscription_id VARCHAR(255),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 4. SQLite MVP Schema (Development Only)

For MVP/local development, use the same DDL as above but SQLite-compatible:

```sql
-- SQLite-compatible DDL
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    tier TEXT DEFAULT 'free',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id),
    query_text TEXT NOT NULL,
    response_json TEXT NOT NULL,
    latency_ms INTEGER,
    feedback INTEGER,     -- 1=thumbs up, -1=thumbs down
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT REFERENCES sessions(id),
    document_type TEXT NOT NULL,
    input_facts TEXT NOT NULL,
    output_draft TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);
```

---

## 5. Data Retention Policy

| Table | Retention | Rationale |
|---|---|---|
| `queries` | 90 days (free), 2 years (pro/enterprise) | Audit trail + product analytics |
| `drafts` | 1 year | User reference + compliance |
| `sessions` | 30 days | Session analytics |
| ChromaDB chunks | Indefinite | Core knowledge base |
| User PII (email/phone) | Until account deletion | DPDP Act 2023 compliance |

---

## 6. Migration Strategy

```
MVP (SQLite, local)
    ↓ Alembic migration script
Phase 2 (PostgreSQL on RDS ap-south-1)
    ↓ pgvector extension for hybrid search
Phase 3 (PGVector + ChromaDB on dedicated EBS)
```
