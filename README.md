# Nyaya Mitra ⚖️ — AI Legal Guide for Indian Law

> **100% Free · Open Source · Zero Running Cost · Bring Your Own Key**

Nyaya Mitra is an AI-powered legal assistant for Indian law, covering the **Bharatiya Nyaya Sanhita (BNS)**, **Bharatiya Nagarik Suraksha Sanhita (BNSS)**, **Bharatiya Sakshya Adhiniyam (BSA)**, and the **Constitution of India**.

---

## 🏗️ Architecture — Zero Cost by Design

```
Users
├── 📱 Mobile App (Expo / React Native)   ──┐
└── 🌐 Web App (Pure HTML/CSS/JS)         ──┤──→ FastAPI Backend ──→ Google Gemini API
                                             │       (Render Free Tier)    (User's Own Key)
                                             └── BM25 Retrieval (in-memory, free)
```

### Why Zero Cost?
| Component        | Cost          | How                              |
|-----------------|---------------|----------------------------------|
| Backend API      | **Free**      | Render.com free tier             |
| Mobile App       | **Free**      | Expo (no build server needed)    |
| Web App          | **Free**      | GitHub Pages / Netlify / Vercel  |
| AI (Gemini)      | **User pays** | BYOK — user's own API key        |
| Vector DB (BM25) | **Free**      | In-memory, no external service   |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/Shivanshmishra7275/nyaya-mitra-mvp.git
cd nyaya-mitra-mvp
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Optional: copy and edit .env
copy .env.example .env       # Windows
# cp .env.example .env       # Mac/Linux
# → Edit .env if you want a server-side fallback key (not required for BYOK)

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API is now live at: **http://localhost:8000**
- Swagger docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 3. Web App (No Build Needed!)
```bash
# Just open the file in your browser:
start webapp/index.html      # Windows
# open webapp/index.html     # Mac

# Or serve it with any static server:
# npx serve webapp/
```

### 4. Mobile App (Expo)
```bash
cd nyaya-mitra-app
npm install

# For Android emulator:
npx expo start --android

# For iOS simulator (Mac only):
npx expo start --ios

# For browser preview:
npx expo start --web
```

---

## 🔑 Bring Your Own Key (BYOK)

Users provide their own **Google Gemini API key** — free to get, no credit card required.

1. Visit [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Create a free API key
3. Enter it in the app's key modal — it's sent only to your backend, never stored on any server

**Security guarantees:**
- Key is sent per-request via `Authorization: Bearer` header
- Never logged, cached, or stored on the server
- Backend discards it immediately after each Gemini API call
- BYOK can be stored locally (mobile: `expo-secure-store`; web: `localStorage`, opt-in)

---

## 📱 Physical Device Setup (Mobile)

Physical devices can't reach `localhost`. You need to set your machine's LAN IP:

```bash
# 1. Find your LAN IP
ipconfig                 # Windows → look for "IPv4 Address"
ifconfig en0             # Mac → look for "inet"

# 2. Create nyaya-mitra-app/.env
echo EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000 > nyaya-mitra-app/.env

# 3. Start backend on all interfaces
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start Expo (restart after .env change)
cd nyaya-mitra-app && npx expo start
```

---

## 🧪 Running Tests
```bash
# All 12 tests (backend)
pytest tests/ -v

# Quick smoke test
python test_api.py
```

---

## 🚢 Deploy to Production (Free)

### Backend — Render.com
1. Push this repo to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Connect your GitHub repo
4. Render detects `render.yaml` automatically — just click Deploy
5. Set `ALLOWED_ORIGINS` to your web app URL in Render's Environment settings

### Web App — GitHub Pages
```bash
# Enable GitHub Pages in repo settings → Source: "Deploy from branch: main, /webapp"
# Your web app will be live at: https://yourusername.github.io/nyaya-mitra-mvp/webapp/
```

After deploying backend, update `DEFAULT_API_BASE` in `webapp/app.js` to your Render URL.

---

## 📁 Project Structure

```
nyaya-mitra-mvp/
├── app/                          # FastAPI backend (modular)
│   ├── api/routes/               # health, query, admin endpoints
│   ├── core/config.py            # All config from env vars
│   ├── models/schemas.py         # Pydantic request/response models
│   ├── retrieval/                # BM25 + Qdrant hybrid retriever
│   └── services/llm_service.py  # Gemini API integration
├── webapp/                       # Web app (pure HTML/CSS/JS — no framework)
│   ├── index.html
│   ├── style.css
│   └── app.js
├── nyaya-mitra-app/              # Mobile app (Expo / React Native)
│   └── src/
│       ├── components/           # ChatBubble, ApiKeyModal, ErrorBoundary
│       ├── hooks/                # useChat, useServerHealth
│       ├── screens/              # ChatScreen
│       ├── services/             # api.js, keyStorage.js
│       └── theme/                # colors.js
├── tests/                        # 12 backend pytest tests
├── etl_pipeline.py               # PDF → JSON chunk store (run once)
├── vector_store_mock.json        # Pre-built BM25 retrieval store
├── requirements.txt
├── Dockerfile
├── render.yaml                   # One-click Render deployment
└── README.md
```

---

## ⚠️ Legal Disclaimer

Nyaya Mitra provides **legal information, not legal advice**. Always consult a qualified lawyer for your specific situation. The information provided is based on publicly available legal texts and may not reflect the most recent amendments.

---

## 📄 License

MIT License — free to use, modify, and deploy.

---

*Built with ❤️ for making Indian law accessible to everyone.*
