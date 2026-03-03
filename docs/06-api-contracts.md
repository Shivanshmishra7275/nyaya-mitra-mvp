# 06 — API Contracts
## Nyaya Mitra — FastAPI REST Endpoint Specifications

**Version:** 1.0.0  
**Date:** March 2026  
**Base URL:** `http://localhost:8000` (dev) | `https://api.nyayamitra.in` (prod)

---

## 1. Authentication (MVP — No Auth; Phase 2 — JWT Bearer)

```
MVP:   No authentication required
Phase 2: Authorization: Bearer <JWT_ACCESS_TOKEN>
```

All endpoints accept `Content-Type: application/json`.

---

## 2. Endpoint Registry

| Method | Path | Description | Auth | Tier |
|---|---|---|---|---|
| GET | `/health` | Service health check | None | All |
| POST | `/api/v1/legal-query` | RAG-powered legal Q&A | None (MVP) | Free + Pro |
| POST | `/api/v1/draft-document` | AI document drafting | None (MVP) | Pro + Enterprise |
| GET | `/api/v1/query-history` | List past queries | JWT (Phase 2) | Pro |
| GET | `/api/v1/corpus-stats` | Vector store statistics | None | All |

---

## 3. Endpoint Specifications

### 3.1 GET `/health`

**Purpose:** Load balancer health check and monitoring probe.

**Response 200:**
```json
{
  "status": "healthy",
  "vector_store": "loaded",
  "chunks_indexed": 1732,
  "embedding_model": "all-MiniLM-L6-v2",
  "version": "1.0.0"
}
```

**Response 503 (ChromaDB not ready):**
```json
{"detail": "Vector store not initialized. Run etl_pipeline.py first."}
```

---

### 3.2 POST `/api/v1/legal-query`

**Purpose:** Core RAG pipeline — semantic retrieval + Gemini generation.

**Request Body (Pydantic `LegalQueryRequest`):**
```json
{
  "user_query": "string",
  "top_k": 15,
  "session_id": "optional-uuid-string"
}
```

**Field Constraints:**
```python
class LegalQueryRequest(BaseModel):
    user_query: str = Field(
        ..., 
        min_length=5, 
        max_length=2000,
        description="Natural language legal question"
    )
    top_k: int = Field(default=15, ge=5, le=30)
    session_id: Optional[str] = None
```

**Response 200 (Pydantic `LegalQueryResponse`):**
```json
{
  "explanation": "Under the Bharatiya Nyaya Sanhita (BNS) 2023, theft is defined under Section 303 as the dishonest taking of moveable property without consent. The punishment ranges from imprisonment of up to 3 years (simple theft) to 7 years for repeat offenders.",
  "citations": [
    "BNS — Section 303, Page 87",
    "BNS — Section 304, Page 88",
    "BNS — Section 305, Page 88"
  ],
  "suggested_next_steps": [
    "File an FIR at the nearest police station under Section 303 BNS",
    "Request a copy of the FIR under Section 173 BNSS",
    "Consult an advocate if the stolen amount exceeds ₹20,000"
  ],
  "disclaimer": "This is AI-generated legal information, not legal advice. Consult a qualified advocate for your specific situation.",
  "latency_ms": 2340
}
```

**Error Responses:**
```json
// 404 — No relevant legal context found
{"detail": "No relevant legal information found for this query."}

// 422 — Validation error
{"detail": [{"loc": ["body", "user_query"], "msg": "field required", "type": "value_error.missing"}]}

// 429 — Rate limit exceeded (Free tier)
{"detail": "Daily query limit reached. Upgrade to Pro for unlimited queries."}

// 502 — Gemini returned invalid JSON
{"detail": "AI service returned an unstructured response. Please retry."}

// 503 — Vector store not loaded
{"detail": "Knowledge base unavailable. Please try again shortly."}
```

---

### 3.3 POST `/api/v1/draft-document`

**Purpose:** AI-powered legal document drafting using templates + RAG context.

**Request Body (Pydantic `DraftDocumentRequest`):**
```json
{
  "document_type": "bail_application",
  "facts": "My client Ramesh Kumar was arrested on 2026-03-01 by Delhi Police...",
  "accused_name": "Ramesh Kumar",
  "court": "Sessions Court, New Delhi",
  "sections_charged": ["BNS Section 303", "BNS Section 309"],
  "session_id": "optional-uuid-string"
}
```

**Supported `document_type` values:**
```
bail_application        — Bail application under BNSS Section 480/483
fir_draft               — FIR complaint draft
legal_notice            — Legal notice under general civil/criminal law
complaint_letter        — Complaint to senior police/magistrate
anticipatory_bail       — Anticipatory bail under BNSS Section 482
```

**Field Constraints:**
```python
class DraftDocumentRequest(BaseModel):
    document_type: Literal[
        "bail_application", "fir_draft", "legal_notice", 
        "complaint_letter", "anticipatory_bail"
    ]
    facts: str = Field(..., min_length=50, max_length=5000)
    accused_name: Optional[str] = Field(None, max_length=255)
    court: Optional[str] = Field(None, max_length=255)
    sections_charged: Optional[List[str]] = Field(default_factory=list)
    session_id: Optional[str] = None
```

**Response 200 (Pydantic `DraftDocumentResponse`):**
```json
{
  "document_type": "bail_application",
  "accused_name": "Ramesh Kumar",
  "court": "Sessions Court, New Delhi",
  "draft_content": "IN THE SESSIONS COURT OF NEW DELHI\n\nBAIL APPLICATION\nUnder Section 480 of the Bharatiya Nagarik Suraksha Sanhita, 2023\n\nIN THE MATTER OF:\nState vs. Ramesh Kumar\nFIR No: [TO BE FILLED]\n\nRESPECTFULLY SHOWETH:\n\n1. That the applicant Ramesh Kumar was arrested on 2026-03-01...",
  "citations_used": [
    "BNSS — Section 480",
    "BNSS — Section 483",
    "BNS — Section 303"
  ],
  "disclaimer": "AI-generated draft. Review with a qualified advocate before filing. Nyaya Mitra is not liable for outcomes.",
  "latency_ms": 3870
}
```

**Error Responses:**
```json
// 400 — Unsupported document type
{"detail": "Document type 'writ_petition' is not supported in MVP."}

// 402 — Premium feature
{"detail": "Document drafting requires a Pro subscription. Upgrade at nyayamitra.in/upgrade"}

// 503 — Gemini unavailable
{"detail": "Document generation service temporarily unavailable."}
```

---

### 3.4 GET `/api/v1/corpus-stats`

**Purpose:** Returns metadata about the loaded legal corpus for UI display.

**Response 200:**
```json
{
  "total_chunks": 1732,
  "sources": {
    "bns.pdf": 423,
    "bnss.pdf": 641,
    "bsa.pdf": 214,
    "const.pdf": 454
  },
  "embedding_model": "all-MiniLM-L6-v2",
  "embedding_dimensions": 384,
  "last_updated": "2026-03-01T10:00:00Z"
}
```

---

## 4. Request/Response Conventions

```
Content-Type:     application/json
Accept:           application/json
Error envelope:   {"detail": "Human-readable error message"}
Timestamps:       ISO 8601, UTC (Z suffix)
IDs:              UUID v4
Pagination:       cursor-based (Phase 2): {"cursor": "...", "limit": 20}
```

---

## 5. Rate Limiting (Phase 2)

```
Free Tier:        5 requests/day on /legal-query
Pro Tier:         Unlimited
Enterprise Tier:  Unlimited + priority queue

Headers returned:
  X-RateLimit-Limit: 5
  X-RateLimit-Remaining: 3
  X-RateLimit-Reset: 1741150000
```

---

## 6. Versioning Policy

- Current: `v1`
- Breaking changes → `v2` (old `v1` maintained for 6 months)
- Non-breaking additions → same `v1` with changelog
- Deprecation notices via `Deprecation: <date>` response header
