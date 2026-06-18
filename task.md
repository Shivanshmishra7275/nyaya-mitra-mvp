# Flawless Production-Readiness Task List

## Phase 1: Cybersecurity Hardening (Completed)
- `[x]` Fix Timing Attack & Randomness in `app/api/routes/admin.py`
- `[x]` Fix IP Spoofing (Rate Limit Bypass) in `app/main.py`
- `[x]` Mitigate Prompt Injection in `app/services/llm_service.py`
- `[x]` Fix Key Masking Leak in `app/services/llm_service.py`
- `[x]` Fix Out-of-Scope Bypass in `app/services/llm_service.py`
- `[x]` Fix ReDoS in `app/retrieval/bm25_retriever.py`

## Phase 2: Architecture & Scalability
- `[x]` Migrate Web App to Next.js (Free Tier Deployment)

## Phase 3: MLOps Optimization
- `[x]` Implement Semantic/Structural Chunking in `etl_pipeline.py`
- `[x]` Add Cross-Encoder Reranking in `app/retrieval/hybrid_retriever.py`

## Phase 4: DevOps, CI/CD, and Observability
- `[x]` Create GitHub Actions pipeline `.github/workflows/main.yml`
- `[x]` Pin exact dependencies in `requirements.txt`
- `[x]` Add structured logging with `structlog`
