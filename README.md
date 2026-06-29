# Nyaya Mitra ⚖️ — AI Legal Super-App for India

<div align="center">

![Nyaya Mitra Banner](https://capsule-render.vercel.app/api?type=shark&height=280&text=Nyaya%20Mitra%20%E2%9A%96%EF%B8%8F&fontSize=62&fontAlign=50&fontAlignY=50&color=0:0d1117,40:1a1033,100:2d1f00&fontColor=fbbf24&desc=AI%20Legal%20Intelligence%20for%20India%20%7C%20BNS%20%7C%20BNSS%20%7C%20BSA&descFontColor=f59e0b&descAlignY=70&animation=fadeIn)



<br/>

<p>
  <img src="https://img.shields.io/badge/Status-In_Development-f59e0b?style=for-the-badge" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white" />
  <img src="https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white" />
  <img src="https://img.shields.io/badge/Free_Forever-10b981?style=for-the-badge" />
  <img src="https://img.shields.io/badge/BYOK-Bring_Your_Own_Key-7C3AED?style=for-the-badge" />
</p>

> **Turn messy legal situations into clear, actionable strategies.**  
> **100% Free · Open Source · No Data Saved · Bring Your Own Key**

</div>

---

## 🎯 What Is Nyaya Mitra?

**Nyaya Mitra** ("Friend of Justice" in Hindi) is a specialized **AI Case Intelligence Assistant** built to make India's new criminal justice framework accessible to everyone — not just lawyers.

Most Indians can't afford legal consultations. Nyaya Mitra bridges this gap by letting anyone describe their situation in plain language and receiving expert-level legal analysis based on India's three new criminal laws:

- 📘 **Bharatiya Nyaya Sanhita (BNS)** — replaces IPC
- 📗 **Bharatiya Nagarik Suraksha Sanhita (BNSS)** — replaces CrPC
- 📙 **Bharatiya Sakshya Adhiniyam (BSA)** — replaces Indian Evidence Act

> 💡 **Pitched at ENTREPRENIA 2025** as a high-impact AI product for social good.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🗣️ **Natural Language Input** | Describe what happened in plain English — no legal jargon needed |
| ⚡ **Instant Legal Mapping** | Automatically maps your story to the correct BNS/BNSS/BSA sections |
| 🔍 **Case Weakness Detector** | Identifies gaps in your case (missing evidence, documents, witnesses) |
| 🗺️ **Strategy Paths** | 2–4 clear action options with pros/cons (file FIR, mediation, court, etc.) |
| 📄 **Lawyer Brief Generator** | Creates a formatted summary to hand to a human lawyer — saves time & fees |
| 🚨 **Raksha Mode** | Emergency logic system for urgent, time-sensitive legal situations |
| 🔒 **Zero Data Storage** | Nothing is saved on our servers — complete privacy |

---

## 🏗️ Architecture

```
User (Browser)
│
├── 🌐 Next.js Frontend  ──────────→  🐍 FastAPI Backend  ──────→  🤖 Google Gemini AI
│   (Vercel — Free)                  (Render — Free)                  (Your API Key)
│
│   BM25 Vector Search (local, free) ── pulls from ──→ BNS/BNSS/BSA legal corpus
```

### Why It Costs Nothing to Host
| Component | Service | Cost |
|---|---|---|
| Frontend | Vercel free tier | $0 |
| Backend | Render free tier (stateless) | $0 |
| AI | Google Gemini API (BYOK) | $0 on free tier |
| Database | BM25 local search (no cloud DB) | $0 |

---

## 🔒 Privacy & Security

- **No Chat History Saved** — conversations are never stored server-side
- **Session-Only Key Storage** — your Gemini API key lives in `sessionStorage` only; vanishes when you close the tab
- **XSS Protected** — strict CSP + input sanitization
- **Prompt Injection Hardened** — system prompts engineered against jailbreaks
- **Scope-Limited** — refuses to answer civil, corporate, or family law (prevents hallucinations)

---

## 🗂️ Project Structure

```
nyaya-mitra-mvp/
├── app/                      # FastAPI backend
│   └── main.py               # API routes, RAG pipeline
├── next-webapp/              # Next.js frontend
├── nyaya-mitra-app/          # Mobile app (in progress)
├── etl_pipeline.py           # Ingests BNS/BNSS/BSA PDFs → vector store
├── main.py                   # Backend entrypoint
├── requirements.txt          # Python dependencies
├── Dockerfile                # Container support
├── render.yaml               # Render deployment config
├── tests/                    # API + integration tests
├── .env.example              # Environment variable template
└── assets/                   # UI screenshots and images
```

---

## 🚀 Run Locally

### 1. Clone
```bash
git clone https://github.com/Shivanshmishra7275/nyaya-mitra-mvp.git
cd nyaya-mitra-mvp
```

### 2. Backend (Python FastAPI)
```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Ingest legal PDFs into vector store (run once)
python etl_pipeline.py

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Backend runs at: **http://localhost:8000**

### 3. Frontend (Next.js)
```bash
cd next-webapp
npm install
npm run dev
```
Frontend runs at: **http://localhost:3000**

---

## 🌐 Deploy for Free

### Frontend → Vercel
1. Push to GitHub
2. Import repo at [vercel.com](https://vercel.com)
3. Set Root Directory: `next-webapp`
4. Deploy ✅

### Backend → Render
1. New Web Service at [render.com](https://render.com)
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. Add env vars:
   - `APP_ENV=production`
   - `ALLOWED_ORIGINS=https://your-app.vercel.app`

---

## ⚠️ Legal Disclaimer

Nyaya Mitra provides **legal intelligence and structured case analysis** to help you understand your situation — it is **not legal advice**. Always consult a qualified, licensed lawyer for your specific legal matters.

---

## 📄 License

MIT License — free to use, modify, share, and deploy.

---

## 👤 Author

**Shivansh Mishra** — ML Builder & AI Product Explorer  
📍 Lucknow, India · [GitHub](https://github.com/Shivansh-mishraji) · [Portfolio](https://shivansh-mishraji.github.io/Portfolio-Website/) · [LinkedIn](https://www.linkedin.com/in/shivansh-mishra-132b97358)

---

<div align="center">
  <i>⚖️ Built to make India's new criminal justice framework accessible to 1.4 billion people.</i>
</div>
