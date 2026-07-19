# Nyaya Mitra SaaS Audit Report ⚖️

This comprehensive audit of **Project Nyaya Mitra** evaluates the architecture, code quality, security, and product strategy from the perspective of an expert technical team (Co-Founder, Full-Stack Dev, Mobile Dev, DevOps, and MLOps).

---

## 1. Executive Summary

Nyaya Mitra is a highly promising, domain-specific AI tool targeting the Indian legal tech space (BNS, BNSS, BSA). The **Zero Cost Architecture** with Bring Your Own Key (BYOK) is a brilliant go-to-market strategy for an MVP, keeping operational overhead near zero while validating user demand.

However, transitioning from an MVP to a robust, monetisable SaaS product requires addressing critical gaps in state management, security, testability, and backend scalability.

---

## 2. Architecture & Design (SaaS Perspective)

### Current State
- **Backend:** FastAPI (Python) serving a stateless REST API.
- **Frontend:** Two clients – an Expo/React Native mobile app and a Vanilla HTML/JS web app.
- **AI/Data Layer:** Google Gemini API (BYOK) + Local BM25/Qdrant Hybrid RAG.
- **Hosting:** Render Free Tier + Docker.

### 🔴 Flaws & Risks
1. **Stateless Conversational UX:** The backend API (`/legal-query`) handles one-off queries but doesn't persist conversation history or context. A true legal assistant requires multi-turn memory to refine facts.
2. **BYOK Limitations for Monetisation:** Relying entirely on users to bring their own Gemini API keys introduces massive UX friction for non-technical users (the mass market).
3. **No Database:** Without a persistent database (e.g., PostgreSQL), you cannot implement user authentication, save case histories, track usage for billing, or collect analytics on what users are searching for.

### 🟢 Solutions
- **Implement a Postgres Database:** Introduce SQLAlchemy and PostgreSQL (Render has a free tier for Postgres). Create `users`, `conversations`, and `queries` tables.
- **Hybrid Monetisation Strategy:** Keep BYOK as a "Free Tier / Pro Developer" option. Introduce a paid subscription tier (Stripe Integration) where you manage the API keys and offer a seamless UX.
- **Multi-Turn Memory:** Pass a `conversation_id` in the API and retrieve the last N turns from the database to inject into the LLM prompt.

---

## 3. Backend (FastAPI)

### Current State
- Solid use of FastAPI, Pydantic validation, and `slowapi` for rate limiting.
- Good async handling with `asyncio.to_thread()` for the blocking Gemini SDK calls.

### 🔴 Flaws & Risks
1. **Error Handling on LLM Failure:** The retry mechanism relies purely on `ValueError` for generic parsing errors. If Gemini's API changes its error schema or drops a connection, the `Exception` block catches it and throws a 500 without retrying.
2. **Hardcoded Model:** `settings.GEMINI_MODEL` is used globally. You cannot easily switch to `gemini-1.5-pro` for paid users and `gemini-1.5-flash` for free users.
3. **No Authentication/Authorisation:** The `/api/v1/admin` routes presumably rely on a simple `ADMIN_SECRET` header, which is prone to leakage or replay attacks.

### 🟢 Solutions
- **Dynamic Model Selection:** Update `llm_service.py` to accept the model as a parameter. Route premium users to the higher-tier Gemini model.
- **Advanced Retry Logic:** Implement the `tenacity` library for robust exponential backoff on network timeouts (HTTP 429/503/504).
- **JWT Authentication:** Implement OAuth2 with JWT tokens for user sessions instead of just rate-limiting by IP address (which breaks for users behind NATs or mobile networks).

---

## 4. MLOps & LLM Layer (RAG Pipeline)

### Current State
- Excellent data ingestion script (`etl_pipeline.py`) supporting both BM25 (lexical) and Qdrant (semantic) retrieval.
- Smart prompt engineering enforcing a strict JSON schema output.
- LLM response JSON repair function (`_attempt_repair`).

### 🔴 Flaws & Risks
1. **Brittle Chunking Strategy:** Splitting by a hardcoded 1000 characters (`CHUNK_SIZE = 1000`) with regex section fallbacks can easily break context. Legal acts often have clauses that span multiple pages.
2. **Context Stuffing:** Pulling top-K chunks and pasting them into the prompt can lead to the "Lost in the Middle" phenomenon, where the LLM ignores context in the middle of the prompt.
3. **Hallucination Risk on Out-of-Scope:** The `_is_clear_out_of_scope` uses hardcoded keyword matching. If a user asks a complex question missing those exact words, the LLM will try to force a criminal law answer.

### 🟢 Solutions
- **Semantic Chunking:** Upgrade `etl_pipeline.py` to use semantic chunking (splitting by semantic similarity boundaries) or structural chunking using a dedicated PDF layout parser (like Unstructured.io) to keep full sections intact.
- **Reranking:** Implement a Cross-Encoder (e.g., `bge-reranker`) after Qdrant retrieval to re-score the top 20 chunks down to the top 5 most relevant ones before passing to the LLM.
- **LLM-Based Intent Routing:** Instead of a hardcoded Python list for out-of-scope checking, use a small, fast, cheap LLM call (or local NLP model) specifically for Intent Classification before hitting the heavy RAG pipeline.

---

## 5. Frontend (Mobile App & Web App)

### Current State
- Mobile: React Native / Expo (`nyaya-mitra-app`).
- Web: Vanilla HTML/CSS/JS (`webapp/app.js`).

### 🔴 Flaws & Risks
1. **Web App Tech Debt:** Using a 23KB vanilla `app.js` file for the web app is not scalable. Managing state, routing, and UI updates manually will become a nightmare as features are added.
2. **BYOK Security on Client:** If users paste their Gemini API key into the frontend, it resides in memory or `AsyncStorage`. If the app has any XSS vulnerability (especially in the Web version), those keys can be stolen.
3. **SEO & Discoverability:** A vanilla JS Single Page Application (SPA) has terrible SEO. Since this is an informational legal tool, SEO is critical for organic growth.

### 🟢 Solutions
- **Migrate Web App to Next.js / React:** Rewrite the `webapp` folder using Next.js, React, and TailwindCSS. This will solve the state management issue and provide Server-Side Rendering (SSR) for massive SEO improvements.
- **Secure Key Storage:** In the mobile app, use `expo-secure-store` instead of `AsyncStorage` for the API key to encrypt it via the OS's keychain/keystore.
- **Monorepo Structure:** Consider moving to a monorepo (e.g., Turborepo) to share TypeScript types, API clients, and constants between the Next.js web app and the React Native mobile app.

---

## 6. DevOps & Deployment

### Current State
- Dockerized backend.
- Render `render.yaml` infrastructure as code.
- Local in-memory BM25 index.

### 🔴 Flaws & Risks
1. **Ephemeral File System on Render:** Render's free tier spins down after inactivity. If the `vector_store_mock.json` is generated locally and not committed, or if it needs live updates, Render will wipe it on every restart.
2. **Qdrant Deployment:** The code supports Qdrant, but running Qdrant inside the same Docker container or on the same free Render instance will cause Out-Of-Memory (OOM) crashes. Qdrant requires dedicated RAM.
3. **No CI/CD Pipeline:** There are tests (`tests/test_api.py`), but no automated pipeline runs them.

### 🟢 Solutions
- **Managed Vector Database:** Migrate Qdrant to Qdrant Cloud (they offer a generous free tier cluster) or Pinecone. Update `etl_pipeline.py` to push to the cloud cluster instead of localhost.
- **GitHub Actions:** Create a `.github/workflows/main.yml` to run `pytest`, `flake8/black`, and deploy to Render automatically on merges to `main`.
- **Blob Storage:** Move the raw PDFs and the BM25 JSON store to AWS S3 or Cloudflare R2, and have the backend download them on startup if they don't exist, preventing Docker image bloat.

---

## 7. Business & Future Roadmap

To turn this MVP into a scalable SaaS business:

1. **Target Audience Pivot:** While B2C (citizens) is a noble cause, B2B (Lawyers, Law Students, NGOs) will pay. Add a feature to generate "Legal Drafts" or "Bail Application Templates" based on the extracted facts.
2. **Phase out BYOK for B2B:** Lawyers will not generate Gemini API keys. You must implement a subscription (e.g., ₹999/month) where you handle the LLM costs.
3. **Expanded Corpus:** BNS, BNSS, and BSA are just the start. You need Supreme Court precedents (Case Law) to be truly useful to professionals. Look into integrating with Indian Kanoon's API or scraping public judgments.

> [!TIP]
> **Immediate Action Item:** Migrate the frontend to Next.js to unify your design system and add Postgres to start tracking user conversations and feedback. This is the fastest path to preparing for a monetised launch.
