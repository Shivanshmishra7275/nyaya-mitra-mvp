# Nyaya Mitra - AI-First Legal Super-App
Empowering citizens with accessible legal awareness and offline-first assistance.

> ⚠️ **Development Status: Active Prototyping & Architecture Phase**
> 
> *Please note: This project is currently an MVP (Minimum Viable Product) undergoing rapid AI-assisted prototyping. The core system architecture and product vision are mapped out, but the codebase is in a state of active development, experimentation, and refactoring. Expect frequent updates and structural changes.*

## Core Features
* Mitra AI
* Raksha Mode
...

# ⚖️ Nyaya Mitra — AI-Powered Indian Legal Co-Pilot

> **"Nyaya Mitra" (न्याय मित्र) means "Friend of Justice."**
>
> A full-stack legal AI platform that makes India’s new criminal justice
> laws — **Bharatiya Nyaya Sanhita (BNS)**, **Bharatiya Nagarik Suraksha
> Sanhita (BNSS)**, and **Bharatiya Sakshya Adhiniyam (BSA)** — accessible
> to every citizen, advocate, and legal innovator.

Nyaya Mitra combines a **FastAPI + ChromaDB + Gemini 2.5 Flash** backend with a
**React Native / Expo** frontend to answer legal questions and draft court-ready
documents grounded strictly in the new Indian statutes and Constitution.

---

## 🏛 Architecture Overview

At a high level Nyaya Mitra is a **RAG + drafting engine** with a mobile-first UI:

- **React Native / Expo Frontend** (nyaya-mitra-app)
  - Presents a chat-style **Legal Q&A** interface and a **dynamic drafting form**.
  - Talks to the backend via HTTPS JSON APIs (`/health`, `/api/v1/legal-query`,
    `/api/v1/draft-document`).

- **FastAPI Backend** (Python)
  - Exposes versioned REST endpoints and performs request/response validation.
  - On startup, initialises:
    - **ChromaDB** persistent collection with law chunks (vector store).
    - **SentenceTransformer** embedding model (`all-MiniLM-L6-v2`).
    - **SQLite** database for anonymous session + analytics logging.

- **RAG & Drafting Services**
  - `rag_service.py` encodes queries, retrieves top-k legal chunks from ChromaDB,
    and assembles a structured context string.
  - `gemini_service.py` calls **Gemini 2.5 Flash** with tight JSON/drafting prompts.
  - `drafting_service.py` loads text templates, pulls relevant provisions, and drives
    AI document generation.

- **Data Stores**
  - **ChromaDB** (local directory `chroma_db/`) holds all embedded law chunks.
  - **SQLite** (`nyaya_mitra.db` by default) stores sessions, queries, and draft logs.

Data flow for a **Legal Q&A** request:

1. Frontend `ChatScreen` → calls `POST /api/v1/legal-query` with the user query.
2. Backend validates payload → embeds query → performs ChromaDB semantic search.
3. Retrieved chunks → formatted into a context string → passed into Gemini.
4. Gemini returns a structured JSON answer (explanation + citations + next steps).
5. Backend enforces disclaimer, logs to SQLite, and returns a `LegalQueryResponse`.
6. Frontend renders an `AiMessageCard` with citations, steps, and latency.

Data flow for **Document Drafting** is analogous but driven by templates and a
different prompt, returning a `DraftDocumentResponse` consumed by `DraftResultScreen`.

---

## ⚡ Quick Start Guide for New Developers

This section focuses on **time-to-first-run** on a typical developer laptop.

### Option A — Docker Path (Highly Recommended)

This is the fastest way to get *everything* (backend + frontend + data volumes)
running in isolation.

#### 1. Prerequisites

- Docker Engine + Docker Compose (v2) installed and running.
- A valid **Google Gemini API key** from Google AI Studio.

#### 2. Clone the Repository

```bash
git clone https://github.com/your-org/nyaya-mitra.git
cd nyaya-mitra
```

#### 3. Configure `.env`

Use the provided example as a template:

```bash
cp .env.example .env
```

Open `.env` and at minimum set:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

All other keys have safe defaults (documented later in this file).

#### 4. Build and Run with Docker Compose

```bash
# From the repository root
docker compose build
docker compose up
```

This will start two services:

- **backend** — FastAPI + Uvicorn on host port **8000**
- **frontend** — Expo web preview on host port **3000**

Named volumes are created for:

- `chroma_db_volume` → mounted at `/app/chroma_db` (vector store)
- `sqlite_db_volume` → mounted at `/app/db` (SQLite DB directory)

Once the stack is up:

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Frontend (web preview): http://localhost:3000

> Note: the first run may take longer while Docker builds Python and Node
> images and downloads the sentence-transformer model.

#### 5. Stopping and Cleaning Up

```bash
# Stop containers but keep volumes
docker compose down

# Stop and also remove volumes (wipes local DB + vector store)
docker compose down -v
```

---

### Option B — Local Development Path (For Advanced Contribution)

Use this path if you plan to iterate on backend logic, frontend UX, or the ETL
pipeline itself.

#### 1. Prerequisites

- Python **3.10+**
- Node.js **18+** and npm
- Git

#### 2. Clone the Repository

```bash
git clone https://github.com/your-org/nyaya-mitra.git
cd nyaya-mitra
```

#### 3. Backend Setup (Python / FastAPI)

Create and activate a virtual environment:

```bash
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows (CMD)
.\.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create your `.env` file (or copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and set `GEMINI_API_KEY` to your key.

Run the ETL pipeline **once** to build the ChromaDB index:

```bash
python etl_pipeline.py
```

Start the FastAPI server (development mode):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should now have:

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

#### 4. Frontend Setup (React Native / Expo)

In a **new terminal**:

```bash
cd nyaya-mitra-app
npm install
```

Ensure `constants/ApiConfig.js` points to your backend:

```js
export const BASE_URL = 'http://127.0.0.1:8000';
```

Start Expo:

```bash
npx expo start
```

From the Expo CLI:

- Press **`w`** → open web
- Press **`a`** → Android emulator
- Press **`i`** → iOS simulator

---

## 🔐 Environment Variable Guide

All environment variables are centralised in `config.py` on the backend and
documented in `.env.example`.

### Required

| Key             | Description |
|-----------------|-------------|
| `GEMINI_API_KEY` | **Required.** Google Gemini API key used by `google-generativeai` to call Gemini 2.5 Flash for Q&A and drafting. |

### Optional (Vector Store & RAG)

| Key                    | Default                | Description |
|------------------------|------------------------|-------------|
| `CHROMA_DB_PATH`       | `./chroma_db`         | Filesystem path where the ChromaDB persistent store is created. Can be pointed to any writable directory. |
| `CHROMA_COLLECTION_NAME` | `nyaya_mitra_legal` | Name of the ChromaDB collection that stores all embedded law chunks. |
| `EMBEDDING_MODEL`      | `all-MiniLM-L6-v2`    | HuggingFace model ID used by SentenceTransformer. Must match the embedding dimension expected by the app. |
| `RAG_TOP_K`            | `15`                  | Default number of chunks retrieved per query; can be tuned for recall vs. latency. |

### Optional (FastAPI & App Behaviour)

| Key             | Default       | Description |
|-----------------|---------------|-------------|
| `FASTAPI_HOST`  | `0.0.0.0`     | Host interface for the FastAPI server. For local dev this is typically left as-is. |
| `FASTAPI_PORT`  | `8000`        | Port that Uvicorn binds to. Must match any Docker/NGINX port mappings. |
| `FASTAPI_ENV`   | `development` | Controls CORS behaviour (`*` in dev, restricted in production). |
| `LOG_LEVEL`     | `INFO`        | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

### Optional (SQLite)

| Key              | Default              | Description |
|------------------|----------------------|-------------|
| `SQLITE_DB_PATH` | `./nyaya_mitra.db`  | Path to the SQLite database file that stores anonymous sessions, query logs, and draft logs. |

### How to Set Up `.env` Securely

1. **Never commit** your `.env` file. It is already excluded by `.gitignore`.
2. Create `.env` by copying the template and editing locally:

   ```bash
   cp .env.example .env
   ```

3. Fill in the values for your own environment only. For shared deployments,
   use orchestration-level secrets (Docker / Kubernetes / CI secrets) rather than
   baking keys into the repo.

---

## 🤝 Contributing Guide

Nyaya Mitra is designed to be contributor-friendly. Please follow this workflow
to keep the project stable for new developers.

### 1. Git Workflow

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/your-username/nyaya-mitra.git
cd nyaya-mitra

# Create a feature branch
git checkout -b feature/short-description
```

Make your changes in small, focused commits:

```bash
git commit -m "feat: add health endpoint docs"
git push origin feature/short-description
```

Open a Pull Request against the main repository and provide:

- A short summary of the change.
- Any screenshots for UI tweaks.
- Notes on how reviewers can verify the behaviour.

### 2. Running and Verifying Before You Commit

**Backend checks:**

- Ensure `.env` is configured and `GEMINI_API_KEY` is valid.
- Run the ETL pipeline at least once if you change anything related to `Raw_Data/`.
- Start the server locally and hit:
  - `GET /health` — should report `status="healthy"` once ChromaDB is ready.
  - `GET /docs` — should load the OpenAPI UI without errors.

**Frontend checks:**

- Run `npm install` in `nyaya-mitra-app` if dependencies changed.
- Start Expo and verify:
  - Home → Chat: can send a basic question and receive an AI answer.
  - Home → Draft: can generate at least one document type end-to-end.
  - Settings: correctly displays API URL and corpus stats.

**Docker checks:**

- From the repo root, run:

  ```bash
  docker compose build
  docker compose up
  ```

- Verify:
  - Backend health: `curl http://localhost:8000/health`
  - Swagger docs: open http://localhost:8000/docs in a browser.
  - Frontend web: open http://localhost:3000 and complete a basic Q&A.

Please avoid committing large generated assets (e.g., `chroma_db/`, `node_modules/`,
`.venv/`, build artifacts). These are already excluded via `.gitignore` and
`.dockerignore`.

### 3. Coding Style & Documentation

- Python:
  - Follow PEP 8 and PEP 257 (docstrings).
  - Keep all configuration access centralised in `config.py`.
  - Avoid calling `os.getenv` directly in business logic; import from config.

- JavaScript / React Native:
  - Use file-level headers and JSDoc-style comments for exported components.
  - Keep API URLs and constants inside `constants/` rather than scattering
    literals across screens.

---

## ⚠️ Legal Disclaimer

Nyaya Mitra is an **AI-assisted legal information and drafting tool**. All
outputs are generated by a large language model using statutory text as
context. It is **not** a substitute for professional legal advice.

- Any generated document must be reviewed, verified, and signed by a
  registered advocate before use in court or official proceedings.
- The maintainers and contributors of this project are **not responsible** for
  any outcome arising from reliance on the information or drafts produced by
  this software.

---

## 📜 License

This project is currently distributed under an open-source license (see
`LICENSE` in the repository if present). If no license file is included yet,
assume **“All rights reserved”** until one is added.

---

Built to democratise access to justice in India.

> Nyaya Mitra — न्याय मित्र
