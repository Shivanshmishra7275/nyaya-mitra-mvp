# Nyaya Mitra — Known Issues and Future Work

## Critical Issues Fixed (v1.0)

✅ Config mismatch between docker-compose and actual embedding model  
✅ Hardcoded Gemini model version (now configurable)  
✅ Dockerfile healthcheck using missing `requests` library  
✅ Docker-compose circular dependency (backend → frontend)  
✅ ETL pipeline silent failures (now exits with code 1 on error)  
✅ Missing error handling in RAG embedding API calls  
✅ Gemini API calls without timeout  
✅ Unsafe fallback responses exposing raw Gemini output  
✅ SQLite database without WAL mode (concurrent access issues)  
✅ Database text fields unbounded (bloats over time)  
✅ Router error messages revealing internal implementation to users  
✅ Query logging exposing full user text (privacy risk)  
✅ Template files not validated at startup  
✅ README references outdated SentenceTransformer model  
✅ Frontend application missing from repository  

## Remaining Medium-Priority Issues

### rag-001: Citation extraction depends on unreliable regex

**Status**: Open  
**Priority**: Medium  
**File**: `services/rag_service.py` (137-169)  
**Issue**: The `extract_citations_from_chunks()` function uses regex fallback patterns that may not match all citation formats in legal text, especially for complex citations.

**Impact**: Users see incomplete or missing source citations.

**Solution**:
1. Add comprehensive test suite for citation extraction
2. Enhance regex patterns to cover:
   - "Section X of the Constitution"
   - "Article Y"
   - "Chapter Z"
   - Range citations: "Sections 1-5"
3. Add fallback citation generation from structured metadata

**Effort**: Medium (2-3 hours)

---

### gem-003: Prompts scattered across functions

**Status**: Open  
**Priority**: Low  
**File**: `services/gemini_service.py` (45-100)  
**Issue**: System instructions and user templates are defined as raw strings in the module, making them hard to version, test, or internationalize.

**Impact**: Prompt tuning requires code changes; difficult to A/B test prompt variants.

**Solution**:
1. Create `prompts/` directory
2. Move prompts to YAML/JSON files:
   - `prompts/qa_system.txt`
   - `prompts/qa_user.txt`
   - `prompts/drafting_system.txt`
   - `prompts/drafting_user.txt`
3. Load prompts at startup
4. Add version control for prompt changes

**Effort**: Low (1-2 hours)

---

### feat-001: DraftDocumentRequest document_type validation too loose

**Status**: Open  
**Priority**: Medium  
**File**: `models/request_models.py` (49-57)  
**Issue**: Despite using Pydantic `Literal` type hint, the validation may not strictly enforce the allowed document types.

**Impact**: Invalid document types cause template loading failures with confusing error messages.

**Solution**:
1. Add explicit validation at router level before calling service
2. Return 400 Bad Request with clear message listing valid types
3. Add integration test for each document type

**Effort**: Low (1 hour)

---

### feat-002: Corpus stats endpoint may timeout on large collections

**Status**: Open  
**Priority**: Low  
**File**: `routers/health.py` (42-85)  
**Issue**: The corpus stats endpoint calls `collection.get(limit=10000)` which could be slow on first request if collection has many items.

**Impact**: Frontend health check may timeout during startup, delaying app initialization.

**Solution**:
1. Implement pagination (fetch in batches of 1000)
2. Cache corpus stats with TTL (1 hour)
3. Return partial stats instead of timing out

**Effort**: Medium (2-3 hours)

---

### feat-003: No rate limiting or quota tracking for Gemini API

**Status**: Open  
**Priority**: High  
**File**: Global  
**Issue**: Unlimited requests hit Gemini API quota without tracking or backoff.

**Impact**: App becomes unusable after quota exhaustion; no graceful degradation.

**Solution**:
1. Implement per-session quota tracking
2. Add token counting before calling Gemini
3. Return 429 Too Many Requests when quota exceeded
4. Implement exponential backoff on rate limit errors
5. Log quota usage for monitoring

**Effort**: High (4-5 hours)

---

### rec-001: No periodic health check for degraded services

**Status**: Open  
**Priority**: Medium  
**File**: `main.py`  
**Issue**: If ChromaDB fails at startup, app stays in degraded mode indefinitely. No retry mechanism.

**Impact**: Users stuck with unavailable service even after ChromaDB recovers.

**Solution**:
1. Add background health check task (asyncio)
2. Runs every 5 minutes if ChromaDB is degraded
3. Attempts to re-initialize failed services
4. Updates app state when service recovers

**Effort**: Medium (2-3 hours)

---

## Phase 2: Major Architecture Changes

These are planned for a future major release and require significant refactoring.

### Database Migration: SQLite → PostgreSQL

**Status**: Planned  
**Priority**: High  
**Timeline**: Phase 2

**Current State**: SQLite with WAL mode

**Issues**:
- File-based locking under concurrent load
- No native support for distributed deployments
- Limited to single machine
- No query optimization

**Solution**:
1. Create `models/orm_models.py` using SQLAlchemy
2. Define Session, Query, Draft models
3. Create Alembic migration from SQLite schema
4. Add connection pooling (pgbouncer)
5. Add PostgreSQL-specific optimizations (indexes, partitioning)

**Effort**: High (8-10 hours)

---

### Vector Store Migration: ChromaDB → Pinecone/Supabase

**Status**: Planned  
**Priority**: High  
**Timeline**: Phase 2

**Current State**: ChromaDB local persistent client (single machine)

**Issues**:
- Can't scale horizontally
- No redundancy
- Backup/restore is manual
- No native filtering/metadata search

**Solution**:
1. Create abstract `VectorStoreClient` interface
2. Implement `PineconeClient` and `SupabaseVectorClient`
3. Update ETL to support both backends
4. Add configuration to switch at deployment time
5. Implement migration script

**Effort**: High (6-8 hours)

---

### Frontend Implementation: React Native → React Native + Web

**Status**: Planned  
**Priority**: High  
**Timeline**: Phase 2

**Current State**: Empty stub

**Solution**:
1. Initialize Expo project
2. Implement core screens:
   - ChatScreen (legal Q&A)
   - DraftScreen (document generation)
   - SettingsScreen (corpus stats, API config)
3. Add client-side caching with AsyncStorage
4. Implement offline mode with local queue
5. Add biometric auth (fingerprint)

**Effort**: Very High (15-20 hours)

---

### Authentication System

**Status**: Planned  
**Priority**: High  
**Timeline**: Phase 2

**Current State**: Anonymous sessions only

**Solution**:
1. Add user registration/login
2. Implement JWT token-based auth
3. Add role-based access control (RBAC)
4. Track usage per user
5. Implement API key system for third-party integrations

**Effort**: High (8-10 hours)

---

### Observability: Monitoring & Tracing

**Status**: Planned  
**Priority**: Medium  
**Timeline**: Phase 2

**Current State**: Basic structured logging only

**Solution**:
1. Integrate OpenTelemetry
2. Add distributed tracing (Jaeger)
3. Export metrics to Prometheus
4. Create Grafana dashboards
5. Implement alerting rules

**Effort**: Medium (4-6 hours)

---

### Testing & CI/CD

**Status**: In Progress  
**Priority**: High  
**Timeline**: Immediate

**Current State**: No automated tests

**Solution**:
1. Add pytest unit tests for all services
2. Add integration tests for API endpoints
3. Add E2E tests with Playwright
4. Set up GitHub Actions CI/CD
5. Add code coverage tracking

**Effort**: High (10-12 hours)

---

## Low-Priority Enhancements

### Internationalization (i18n)

- Support Hindi, Tamil, Kannada, Telugu legal terminology
- Translate UI and error messages
- Localize date/currency formatting

---

### Document Sharing & Collaboration

- Allow users to share drafts with advocates
- Real-time collaborative editing
- Version history and diff view

---

### Advanced Legal Analysis

- Extract entities (parties, dates, amounts)
- Summarize long documents
- Cross-reference multiple statutes
- Generate case law citations

---

### Performance Optimizations

- Implement query result caching (Redis)
- Add response compression (gzip)
- Lazy load templates on demand
- Optimize ChromaDB indexing (HNSW tuning)

---

## Testing Checklist

Before each release, verify:

- [ ] All syntax checks pass (`python -m py_compile`)
- [ ] All imports resolve
- [ ] All type hints are valid
- [ ] Linting passes (`pylint` or `ruff`)
- [ ] Type checking passes (`mypy` or `pyright`)
- [ ] Unit tests pass (`pytest`)
- [ ] Integration tests pass (API endpoints)
- [ ] Docker build succeeds
- [ ] Docker image runs without errors
- [ ] Health check endpoint returns healthy
- [ ] Sample legal query returns valid response
- [ ] Sample document draft completes
- [ ] No security warnings (bandit, safety)
- [ ] No unused imports or dead code
- [ ] Documentation is up-to-date

---

## Contribution Guidelines

When working on issues from this list:

1. Create a feature branch: `git checkout -b fix/issue-name`
2. Link to this issue in commit messages
3. Write tests for your changes
4. Update documentation
5. Create a PR with a clear description
6. Get code review approval
7. Merge only after all CI checks pass

---

**Last Updated**: 2025-05-21  
**Current Version**: 1.0.0 (MVP)  
**Target Stability**: Production Ready
