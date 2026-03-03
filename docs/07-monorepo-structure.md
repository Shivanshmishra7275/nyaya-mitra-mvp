# 07 — Monorepo Structure
## Nyaya Mitra — Complete Folder Tree and File Organization

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. Top-Level Structure

```
nyaya-mitra/                          ← Monorepo root
├── docs/                             ← Architecture documents (01–16)
├── backend/                          ← FastAPI Python backend
├── nyaya-mitra-app/                  ← React Native (Expo) frontend
├── ml-pipeline/                      ← ETL + embedding pipeline
├── Raw_Data/                         ← Source legal PDFs (gitignored)
├── chroma_db/                        ← ChromaDB persistent store (gitignored)
├── .env                              ← Secrets (gitignored)
├── .env.example                      ← Template for secrets
├── .gitignore
├── README.md
└── new.code-workspace                ← VS Code multi-root workspace
```

---

## 2. Backend Structure

```
backend/
├── main.py                           ← FastAPI app factory, lifespan, CORS
├── config.py                         ← All config constants from environment
│
├── routers/
│   ├── __init__.py
│   ├── legal_query.py                ← POST /api/v1/legal-query
│   ├── document_draft.py             ← POST /api/v1/draft-document
│   └── health.py                     ← GET /health, GET /corpus-stats
│
├── services/
│   ├── __init__.py
│   ├── rag_service.py                ← ChromaDB query + chunk assembly
│   ├── gemini_service.py             ← Gemini API client + prompt builder
│   └── drafting_service.py           ← Template load + draft generation
│
├── models/
│   ├── __init__.py
│   ├── request_models.py             ← Pydantic request schemas
│   └── response_models.py            ← Pydantic response schemas
│
├── db/
│   ├── __init__.py
│   ├── chroma_client.py              ← ChromaDB PersistentClient singleton
│   └── sqlite_client.py              ← SQLite session/query local logging
│
├── templates/
│   ├── bail_application.txt          ← Drafting template
│   ├── anticipatory_bail.txt
│   ├── fir_draft.txt
│   ├── legal_notice.txt
│   └── complaint_letter.txt
│
├── tests/
│   ├── __init__.py
│   ├── test_rag_service.py
│   ├── test_gemini_service.py
│   ├── test_legal_query.py
│   └── test_document_draft.py
│
├── requirements.txt
└── .env.example
```

---

## 3. Frontend Structure

```
nyaya-mitra-app/
├── App.js                            ← Root navigator setup
├── app.json                          ← Expo config (name, icons, splash)
├── index.js                          ← Expo entry point
├── package.json
├── babel.config.js
│
├── screens/
│   ├── HomeScreen.js                 ← Landing + feature overview
│   ├── ChatScreen.js                 ← RAG Q&A chat (primary flow)
│   ├── DraftScreen.js                ← Document type picker + facts form
│   ├── DraftResultScreen.js          ← Draft preview + copy to clipboard
│   └── SettingsScreen.js             ← API URL, app version, tier
│
├── components/
│   ├── CitationPill.js               ← Pill tag for law citations
│   ├── NextStepItem.js               ← Numbered action item
│   ├── AiMessageCard.js              ← Full AI response card
│   ├── UserBubble.js                 ← User message bubble
│   ├── DisclaimerBanner.js           ← Legal disclaimer footer
│   └── LoadingDots.js                ← Animated loading indicator
│
├── services/
│   └── apiService.js                 ← All API calls (legal-query, draft-document)
│
├── constants/
│   ├── Colors.js                     ← Design token color palette
│   ├── ApiConfig.js                  ← BASE_URL + endpoint paths
│   └── DocumentTypes.js              ← Available draft document types
│
├── utils/
│   └── formatters.js                 ← Citation formatting, text truncation
│
├── assets/
│   ├── icon.png                      ← App icon (1024×1024)
│   ├── splash.png                    ← Splash screen (1284×2778)
│   └── adaptive-icon.png             ← Android adaptive icon
│
└── .expo/
    └── devices.json                  ← Expo Go device registry
```

---

## 4. ML Pipeline Structure

```
ml-pipeline/
├── etl_pipeline.py                   ← Main ETL: PDF → ChromaDB
├── validate_corpus.py                ← Verify chunk quality + stats
├── benchmark_retrieval.py            ← RAG retrieval accuracy benchmarks
└── README.md                         ← How to run the pipeline
```

---

## 5. Docs Structure

```
docs/
├── 01-PRD_Nyaya_Mitra.md
├── 02-MVP_Tech_Spec.md
├── 03-System_Design.md
├── 04-Software_Architecture.md
├── 05-database-schema.md
├── 06-api-contracts.md
├── 07-monorepo-structure.md          ← This file
├── 08-ai-drafting-engine-spec.md
├── 09-engineering-scope-definition.md
├── 10-development-phases.md
├── 11-environment-and-devops.md
├── 12-testing-strategy.md
├── 13-security-and-compliance.md
├── 14-ui-ux-design-system.md
├── 15-prompt-engineering-guidelines.md
└── 16-go-to-market-tech-strategy.md
```

---

## 6. .gitignore Specification

```gitignore
# Python
__pycache__/
*.py[cod]
venv/
.env

# ChromaDB data store (regenerated by ETL)
chroma_db/
vector_store_mock.json

# Raw PDF files (too large for git, deploy separately)
Raw_Data/*.pdf

# React Native
nyaya-mitra-app/node_modules/
nyaya-mitra-app/.expo/web/
nyaya-mitra-app/.expo/devices.json

# VS Code
.vscode/settings.json

# OS
.DS_Store
Thumbs.db
```

---

## 7. VS Code Workspace Configuration

```json
// new.code-workspace
{
  "folders": [
    {"path": ".", "name": "Root"},
    {"path": "backend", "name": "Backend (FastAPI)"},
    {"path": "nyaya-mitra-app", "name": "Frontend (React Native)"},
    {"path": "ml-pipeline", "name": "ML Pipeline"},
    {"path": "docs", "name": "Architecture Docs"}
  ],
  "settings": {
    "python.defaultInterpreterPath": "${workspaceFolder:Root}/venv/Scripts/python",
    "editor.formatOnSave": true
  }
}
```
