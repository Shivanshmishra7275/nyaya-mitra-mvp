# 09 — Engineering Scope Definition
## Nyaya Mitra — MVP In-Scope vs Out-of-Scope

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. Engineering Scope Philosophy

The MVP is scoped to demonstrate the **core value hypothesis** with minimum viable infrastructure:
> *"Can an AI grounded in Indian law provide reliable, cited legal information to citizens and assist advocates in drafting documents?"*

Everything that does not directly test this hypothesis is deferred.

---

## 2. MVP In-Scope (Phase 1)

### Backend
| Feature | Description |
|---|---|
| RAG Q&A Endpoint | POST `/api/v1/legal-query` with ChromaDB + Gemini |
| Document Drafting Endpoint | POST `/api/v1/draft-document` for 5 document types |
| Health Check Endpoint | GET `/health` with corpus stats |
| ChromaDB Integration | Persistent local vector store |
| Sentence Transformer Embeddings | `all-MiniLM-L6-v2` local inference |
| Gemini 2.5 Flash Integration | JSON-structured legal responses |
| CORS Middleware | Allow React Native Expo to call local backend |
| Pydantic Validation | Request/response schema enforcement |
| Structured Logging | Query latency, error logging to stdout |
| ETL Pipeline | PDF → ChromaDB population script |

### Frontend
| Feature | Description |
|---|---|
| Chat Screen | Full RAG Q&A chat interface |
| Message History | In-session chat history (local state) |
| AI Response Card | Explanation + citation pills + next steps |
| Document Draft Form | Type picker + facts text input |
| Draft Result Screen | Scrollable draft preview + copy to clipboard |
| Loading States | Animated indicators during API calls |
| Error Handling | User-friendly error messages |
| API Config | Configurable BASE_URL for device testing |

### Data / AI
| Feature | Description |
|---|---|
| PDF Corpus Ingestion | BNS, BNSS, BSA, Constitution PDFs |
| Chunk Strategy | 1000 chars / 200 overlap |
| Vector Search | K=15 semantic retrieval |
| Hallucination Constraints | System prompt grounding rules |
| Citation Extraction | Source + page in every response |

---

## 3. MVP Out-of-Scope (Deferred to Phase 2+)

### Authentication & Authorization
- ❌ User registration / login
- ❌ JWT token issuance and validation
- ❌ Social login (Google, Apple)
- ❌ Phone OTP (India-specific onboarding)
- ❌ Role-based access control (RBAC)

### Payments & Subscription
- ❌ Razorpay integration
- ❌ Subscription tiers enforcement (daily query limits)
- ❌ Invoice generation
- ❌ Webhook handling for payment events

### Enterprise Features
- ❌ Multi-tenant workspace isolation
- ❌ Custom knowledge base ingestion
- ❌ SSO / SAML integration
- ❌ Audit logs UI
- ❌ Admin dashboard

### Export & Sharing
- ❌ PDF export of drafted documents
- ❌ DOCX export
- ❌ Share via WhatsApp / email
- ❌ Print formatting

### Multi-language
- ❌ Hindi query support
- ❌ Hindi response generation
- ❌ Regional language support (Tamil, Bengali, Marathi)
- ❌ Translation layer

### Advanced AI
- ❌ Case precedent search (Supreme Court / High Court judgments)
- ❌ Hybrid BM25 + semantic retrieval (reciprocal rank fusion)
- ❌ Fine-tuned embedding model for Indian legal domain
- ❌ Streaming responses (SSE/WebSocket)
- ❌ Voice input for queries

### Infrastructure
- ❌ Cloud deployment (AWS/GCP)
- ❌ Docker containerization
- ❌ CI/CD pipeline
- ❌ Monitoring (Prometheus/Grafana)
- ❌ Rate limiting (Redis-backed)

### Analytics
- ❌ Query analytics dashboard
- ❌ A/B testing framework
- ❌ User behavior tracking (Mixpanel/Amplitude)

---

## 4. Explicit MVP Acceptance Criteria

The MVP is considered **complete and ready for demo** when:

1. ✅ `etl_pipeline.py` runs without error and populates ChromaDB with all 4 PDFs
2. ✅ `GET /health` returns `"vector_store": "loaded"` with chunk count > 1000
3. ✅ `POST /api/v1/legal-query` returns structured JSON within 5 seconds for any BNS/BNSS query
4. ✅ `POST /api/v1/draft-document` returns a coherent bail application draft > 300 words
5. ✅ React Native ChatScreen displays AI response card with at least 1 citation pill
6. ✅ React Native DraftScreen submits form and displays draft result
7. ✅ No unhandled exceptions in backend logs during a 10-query smoke test
8. ✅ App runs on Android emulator and physical Android device (Expo Go)

---

## 5. Technical Debt Accepted in MVP

| Debt Item | Risk | Mitigation Plan |
|---|---|---|
| SQLite instead of PostgreSQL | Low scalability | Alembic migration in Phase 2 |
| No input rate limiting | Potential API cost overrun | Add Redis rate limiter in Phase 2 |
| BM25 fallback removed | Lower recall on exact keyword matches | Re-add hybrid search in Phase 2 |
| No auth on endpoints | Security risk in production | JWT middleware before public launch |
| Mock session IDs | No user tracking | UUID sessions tied to Device ID in Phase 2 |
| `allow_origins=["*"]` CORS | XSS risk | Restrict to known domains before deployment |
