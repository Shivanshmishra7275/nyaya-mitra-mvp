# Nyaya Mitra: Flawless Production-Readiness Implementation Plan 🚀

This master blueprint is designed to transform Nyaya Mitra from an MVP into a **flawless, secure, and highly scalable production-ready SaaS**. Acting as your cybersecurity expert, project manager, and lead architect, I have outlined every phase required to harden, scale, and open-source this dream project.

## User Review Required
> [!IMPORTANT]
> Please review this plan. This is a massive overhaul affecting Security, Architecture, DevOps, and MLOps. Once you approve, I will begin executing these changes step-by-step.

## Open Questions
1. **Frontend Migration:** Do you approve migrating the Vanilla JS web app to **Next.js** for better state management and SEO? We will deploy this on Vercel for **Free**.

> [!TIP]
> **Zero-Cost Strategy:** Since you mentioned having no budget, we will keep the entire architecture 100% free.
> - Backend: Render Free Tier
> - Frontend: Vercel Free Tier
> - Mobile App: Expo Go / Free APK builds
> - Database: Removed. We will keep the application completely stateless so you do not need to pay for a managed PostgreSQL instance.
> - LLM: Users provide their own Gemini API Keys (BYOK), costing you $0.

---

## Proposed Changes

### Phase 1: Cybersecurity Hardening (Immediate Priority)
We must close all critical security loopholes before a public open-source release to prevent exploitation.

#### [MODIFY] [app/api/routes/admin.py](file:///c:/Users/91727/Desktop/Project%20Nyaya%20Mitra/app/api/routes/admin.py)
- **Fix Timing Attack:** Replace the insecure `!=` string comparison for `X-Admin-Secret` with `hmac.compare_digest`.
- **Fix Randomness:** Replace `random.randint` with `secrets.choice` for cryptographic safety.

#### [MODIFY] [app/main.py](file:///c:/Users/91727/Desktop/Project%20Nyaya%20Mitra/app/main.py)
- **Fix IP Spoofing (Rate Limit Bypass):** Integrate `ProxyHeadersMiddleware` from `uvicorn.middleware.proxy_headers`. This ensures `slowapi` reads the true client IP from Render's load balancer and rejects forged `X-Forwarded-For` headers.

#### [MODIFY] [app/services/llm_service.py](file:///c:/Users/91727/Desktop/Project%20Nyaya%20Mitra/app/services/llm_service.py)
- **Mitigate Prompt Injection:** Isolate the `{query}` inside strict XML tags (e.g., `<user_input>`) and instruct the LLM to ignore system overrides within those tags.
- **Fix Key Masking Leak:** Update `_mask_key` to only expose the last 4 characters (`***A1B2`) instead of the first 4 as well.
- **Fix Out-of-Scope Bypass:** Improve `_is_clear_out_of_scope` to prevent simple bypasses (like appending the word "fir" to a divorce query).

#### [MODIFY] [app/retrieval/bm25_retriever.py](file:///c:/Users/91727/Desktop/Project%20Nyaya%20Mitra/app/retrieval/bm25_retriever.py)
- **Fix ReDoS:** Replace `re.findall(r'\b\w+\b', ...)` with the safer, non-backtracking `re.split(r'\W+', ...)` to prevent CPU exhaustion on malformed inputs.

---

### Phase 2: Architecture & Scalability Upgrades

#### [MODIFY] [webapp/](file:///c:/Users/91727/Desktop/Project%20Nyaya%20Mitra/webapp) -> [NEW] Next.js Web App
- The 23KB Vanilla JS `app.js` is unmaintainable for an open-source project.
- **Action:** Rewrite the web client using **Next.js and React**. (We will use pure Vanilla CSS instead of Tailwind to ensure maximum customizability without bloated utility classes). This will be deployed to Vercel (100% Free).

#### [DELETED] Database & Models (Removed for Zero-Cost)
- We will NOT implement a PostgreSQL database. The application will remain stateless to ensure you never have to pay for database hosting.

---

### Phase 3: MLOps & RAG Pipeline Optimization

#### [MODIFY] [etl_pipeline.py](file:///c:/Users/91727/Desktop/Project%20Nyaya%20Mitra/etl_pipeline.py)
- **Semantic Chunking:** The current `RecursiveCharacterTextSplitter` (1000 chars) arbitrarily cuts legal clauses in half. We will implement semantic chunking or structural PDF parsing (via `unstructured`) to ensure full legal sections remain intact.

#### [MODIFY] [app/retrieval/hybrid_retriever.py](file:///c:/Users/91727/Desktop/Project%20Nyaya%20Mitra/app/retrieval/hybrid_retriever.py)
- **Cross-Encoder Reranking:** Implement a lightweight local reranker (e.g., `bge-reranker`) that takes the top 20 chunks from BM25/Qdrant and precisely scores them down to the top 5 before passing them to the LLM.

---

### Phase 4: DevOps, CI/CD, and Observability

#### [NEW] .github/workflows/main.yml
- Create a GitHub Actions pipeline to run `pytest` (`tests/test_api.py`), `flake8`, and `black` on every Pull Request. This is mandatory for a healthy open-source repository.

#### [MODIFY] [requirements.txt](file:///c:/Users/91727/Desktop/Project%20Nyaya%20Mitra/requirements.txt)
- Pin exact versions (e.g., `fastapi==0.111.0`) instead of `>=`. Generate a strict `requirements.lock` file to guarantee reproducible builds across all environments.

#### [MODIFY] [app/main.py](file:///c:/Users/91727/Desktop/Project%20Nyaya%20Mitra/app/main.py)
- **Structured Logging:** Replace the default Python logger with `structlog` to output logs in JSON format, making them instantly searchable in tools like Datadog or AWS CloudWatch.

---

## Verification Plan

### Automated Tests
- Run `pytest tests/ -v` to ensure no existing functionality breaks.
- Add specific unit tests for the timing attack mitigation and prompt injection isolation.

### Manual Verification
- Attempt to bypass the rate limiter using `X-Forwarded-For: spoofed_ip` headers via `curl`.
- Attempt to steal system prompt via prompt injection.
- Review the Next.js web application for responsive UI and correct state management.
