# Nyaya Mitra — Legal AI for Indian Law

A free-to-build, free-to-run AI legal assistant for Indian law covering:
- **BNS** — Bharatiya Nyaya Sanhita
- **BNSS** — Bharatiya Nagarik Suraksha Sanhita
- **BSA** — Bharatiya Sakshya Adhiniyam
- **Constitution of India**

> ⚠️ **Disclaimer**: Nyaya Mitra provides legal information, not legal advice. Always consult a qualified lawyer for your specific situation.

---

## Architecture

```
Backend:   Python · FastAPI · BM25 (rank_bm25) · google-genai SDK
Frontend:  React Native · Expo SDK 55
Retrieval: Hybrid BM25 (always) + Qdrant semantic (optional)
Deploy:    Render (free tier) · Docker · Local
```

---

## Quick Start — Backend

### 1. Clone and set up environment
```bash
git clone <repo-url>
cd "Project Nyaya Mitra"
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and optionally add your GEMINI_API_KEY
# Or leave it blank and use BYOK from the app
```

### 3. Run the ETL pipeline (builds the search index)
```bash
python etl_pipeline.py
# Output: vector_store_mock.json (~2.5 MB, 2000+ chunks)
# Add more PDFs to Raw_Data/ and re-run anytime
```

### 4. Start the backend
```bash
# Development (with auto-reload):
uvicorn app.main:app --reload

# Production:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### 5. Verify it's running
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0","retrieval_mode":"BM25-only","chunks_loaded":2005}
```

---

## Quick Start — Frontend

### 1. Install dependencies
```bash
cd nyaya-mitra-app
npm install
npm install @react-native-async-storage/async-storage
```

### 2. Configure API URL
Create `nyaya-mitra-app/.env`:
```
# Android emulator:
EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000
# Physical device (replace with your LAN IP):
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000
# Production:
EXPO_PUBLIC_API_BASE_URL=https://nyaya-mitra-api.onrender.com
```

### 3. Run the app
```bash
npx expo start
# Press 'a' for Android emulator, 'i' for iOS simulator
# Scan QR code with Expo Go app for physical device
```

---

## Testing BYOK Flow

1. Start the backend **without** `GEMINI_API_KEY` in `.env`
2. Run the app and tap the 🔑 icon
3. Enter your Gemini API key (get free key at https://aistudio.google.com/app/apikey)
4. Tap "Test Connection" — should show ✓ Connected
5. Ask a legal question — it should work

**Security verification:**
```bash
# Check that the raw key never appears in backend logs
uvicorn app.main:app --reload 2>&1 | grep -v "AIza"
# Should show masked key like: Key=AIza...abcd
```

---

## Running Tests
```bash
pytest tests/ -v
```

---

## Deploy to Render (Free)
1. Push repo to GitHub
2. Create new "Web Service" on render.com
3. Connect your GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Set environment variables in Render dashboard (from `.env.example`)
7. Deploy!

Alternatively, use `render.yaml` for infrastructure-as-code deployment.

---

## Project Structure

```
Project Nyaya Mitra/
├── app/                          # FastAPI application
│   ├── main.py                   # App factory + lifespan
│   ├── core/config.py            # Env-driven settings
│   ├── models/schemas.py         # Pydantic request/response models
│   ├── api/routes/
│   │   ├── health.py             # /health, /version
│   │   └── query.py              # /api/v1/legal-query (BYOK)
│   ├── retrieval/
│   │   ├── bm25_retriever.py     # BM25 lexical retrieval
│   │   └── hybrid_retriever.py   # Hybrid orchestrator
│   └── services/
│       └── llm_service.py        # Gemini SDK, key masking
├── nyaya-mitra-app/              # React Native frontend
│   ├── src/
│   │   ├── config/api.js         # Env-driven base URL
│   │   ├── services/api.js       # Fetch service layer
│   │   ├── hooks/useChat.js      # Chat state + persistence
│   │   ├── components/
│   │   │   ├── ChatBubble.js     # User + AI message cards
│   │   │   └── ApiKeyModal.js    # BYOK key entry modal
│   │   ├── screens/ChatScreen.js # Main chat UI
│   │   └── theme/colors.js       # Color palette
│   └── App.js                    # Thin entry point
├── tests/test_api.py             # Backend test suite
├── etl_pipeline.py               # PDF → JSON ingestion
├── Raw_Data/                     # Legal PDFs (not in git)
├── vector_store_mock.json        # BM25 store (generated)
├── requirements.txt
├── .env.example
├── Dockerfile
└── render.yaml
```

---

## Security Notes
- Raw API keys are **never logged** — only `AIza...abcd` masked format
- CORS is **env-driven** — use `ALLOWED_ORIGINS=*` for dev, real URLs for prod
- `allow_credentials` is disabled when `ALLOWED_ORIGINS=*` (browser spec compliance)
- Keys are **request-scoped** — never stored, cached, or returned
- Input is **validated and length-limited** — max 1000 chars per query
- Docs UI is **disabled in production** (`APP_ENV=production`)
