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
Frontend:  React Native · Expo SDK 55 · expo-secure-store
Retrieval: Hybrid BM25 (always) + Qdrant semantic (optional, free, local)
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

### 3. Run the ETL pipeline (builds the BM25 search index)
```bash
# BM25-only (fast, no extra deps):
python etl_pipeline.py
# Output: vector_store_mock.json (~2.5 MB, 2000+ chunks)
# Add more PDFs to Raw_Data/ and re-run anytime
```

### 3b. Optional: Enable semantic retrieval with Qdrant
```bash
# Start Qdrant (free, requires Docker):
docker run -p 6333:6333 qdrant/qdrant

# Ingest with real embeddings (downloads ~22 MB model on first run):
python etl_pipeline.py --qdrant

# Then set in .env:
# QDRANT_ENABLED=true
# Restart server — retrieval_mode will show "Hybrid (BM25 + Semantic)"
```

### 4. Start the backend
```bash
# Development (with auto-reload):
uvicorn app.main:app --reload

# Production (all interfaces for physical devices and hosting):
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

### 5. Verify it's running
```bash
curl http://localhost:8000/health
# Expected: {"status":"ok","version":"1.0.0","retrieval_mode":"BM25-only","chunks_loaded":2005}
# With Qdrant: retrieval_mode will be "Hybrid (BM25 + Semantic)"
```

---

## Quick Start — Frontend

### 1. Install dependencies
```bash
cd nyaya-mitra-app
npm install
# expo-secure-store and @react-native-async-storage/async-storage are already in package.json
```

### 2. Configure API URL for your device
```bash
# Copy the frontend env example:
cp nyaya-mitra-app/.env.example nyaya-mitra-app/.env

# Edit nyaya-mitra-app/.env:
# Android emulator:
EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000

# Physical device (REQUIRED — find your LAN IP with `ipconfig` on Windows):
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000

# Production:
EXPO_PUBLIC_API_BASE_URL=https://nyaya-mitra-api.onrender.com
```

> **Physical device note**: The backend must also be started with `--host 0.0.0.0`
> (not just `127.0.0.1`) for physical devices to reach it over LAN.

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

## Deploy to Render (Free Tier)
1. Commit your code and push the repository to GitHub.
2. Sign in to [Render](https://render.com/) and click **New > Web Service**.
3. Connect your GitHub repository.
4. Render will automatically detect the `render.yaml` Blueprint file and ask you to apply it.
5. In the Render Dashboard, go to your new Web Service > **Environment**.
6. Set the required environment variables:
   - `APP_ENV`: `production`
   - `ALLOWED_ORIGINS`: (Set this to your frontend URL later once deployed)
   - `QDRANT_ENABLED`: `false` (Render free tier does not support Docker compose. Stick to BM25 or use a managed Qdrant cloud URL).
7. Click **Deploy**.

> **Note**: Free instances spin down after 15 minutes of inactivity, which causes a 50-second delay on the next request. This is normal for a beta MVP.

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
│   │   ├── qdrant_retriever.py   # Semantic retrieval (Qdrant + sentence-transformers)
│   │   └── hybrid_retriever.py   # Hybrid orchestrator (BM25 + Qdrant, fallback)
│   └── services/
│       └── llm_service.py        # Gemini SDK, key masking
├── nyaya-mitra-app/              # React Native frontend
│   ├── src/
│   │   ├── config/api.js         # Env-driven base URL (physical device ready)
│   │   ├── services/
│   │   │   ├── api.js            # Fetch service layer
│   │   │   └── keyStorage.js     # expo-secure-store wrapper for API key
│   │   ├── hooks/useChat.js      # Chat state + AsyncStorage persistence
│   │   ├── components/
│   │   │   ├── ChatBubble.js     # User + AI message cards
│   │   │   └── ApiKeyModal.js    # BYOK key entry modal
│   │   ├── screens/ChatScreen.js # Main chat UI
│   │   └── theme/colors.js       # Color palette
│   └── App.js                    # Thin entry point
├── tests/test_api.py             # Backend test suite (12 tests)
├── etl_pipeline.py               # PDF → JSON + optional Qdrant ingestion
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
- BYOK key stored using **expo-secure-store** (Keychain/EncryptedSharedPreferences), not plain AsyncStorage
- CORS is **env-driven** — use `ALLOWED_ORIGINS=*` for dev, real URLs for prod
- `allow_credentials` is disabled when `ALLOWED_ORIGINS=*` (browser spec compliance)
- Keys are **request-scoped** — never stored on server, never returned in response
- Input is **validated and length-limited** — max 1000 chars per query
- Docs UI is **disabled in production** (`APP_ENV=production`)

---

## Migration Notes (v1 → v2)

### API Key Storage (BYOK)
If you were using a previous version that stored the API key in AsyncStorage under `@nyaya_mitra_saved_api_key`, the key will not auto-migrate. The user will need to re-enter their API key once — it will then be saved securely.

### Semantic Retrieval (Qdrant)
This is additive. Existing BM25-only deployments continue to work unchanged.
To upgrade to hybrid retrieval:
```bash
docker run -p 6333:6333 qdrant/qdrant
python etl_pipeline.py --qdrant
# Set QDRANT_ENABLED=true in .env
# Restart server
```
