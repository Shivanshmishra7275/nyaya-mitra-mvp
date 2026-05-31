# Nyaya Mitra ⚖️ — Indian Criminal Case Intelligence Assistant

> **From messy facts to structured legal strategy.** 
> **100% Free · Open Source · Bring Your Own Key**

Nyaya Mitra is not just another legal chatbot. It is a structured **Case Intelligence Assistant** specifically built for India's new criminal laws: the **Bharatiya Nyaya Sanhita (BNS)**, **Bharatiya Nagarik Suraksha Sanhita (BNSS)**, and **Bharatiya Sakshya Adhiniyam (BSA)**.

Instead of generic Q&A, Nyaya Mitra converts a user's raw story into a structured legal action plan.

---

## 🎯 The Wedge: Why Nyaya Mitra is Unique

While most legal AI tools compete on database size and act like generic search engines, Nyaya Mitra focuses on **Decision Support Quality**:

1. **Intelligent Case Intake:** Accepts messy, incomplete human stories instead of requiring precise legal queries.
2. **Legal GPS & Mapping:** Instantly maps your facts to the applicable BNS/BNSS sections.
3. **Weakness Scanner:** Identifies what might weaken your matter (e.g., lack of documents, missing evidence, contradictions).
4. **Strategy Paths:** Generates 2-4 strategic options (e.g., Complaint Route, Settlement Route) comparing Benefits and Risks.
5. **Lawyer Brief Export:** Produces a structured, professional summary of your facts and goals, ready to be handed to a human lawyer.

---

## 🏗️ Architecture — Zero Cost by Design

```
Users
├── 📱 Mobile App (Expo / React Native)   ──┐
└── 🌐 Web App (Pure HTML/CSS/JS)         ──┤──→ FastAPI Backend ──→ Google Gemini API
                                             │       (Render Free Tier)    (User's Own Key)
                                             └── BM25/Qdrant Hybrid Retrieval
```

### Why Zero Cost?
| Component        | Cost          | How                              |
|-----------------|---------------|----------------------------------|
| Backend API      | **Free**      | Render.com free tier             |
| Mobile App       | **Free**      | Expo (no build server needed)    |
| Web App          | **Free**      | GitHub Pages / Netlify / Vercel  |
| AI (Gemini)      | **User pays** | BYOK — user's own API key        |
| Vector DB        | **Free**      | In-memory BM25 / Local Qdrant    |

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

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API is now live at: **http://localhost:8000**
- Health check: http://localhost:8000/health

### 3. Mobile App (Expo)
```bash
cd nyaya-mitra-app
npm install

# For browser preview (Fastest for testing UI):
npx expo start --web

# For Android emulator / iOS simulator:
npx expo start
```

---

## 🔑 Bring Your Own Key (BYOK)

Nyaya Mitra is entirely free because users provide their own **Google Gemini API key**.

1. Visit [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Create a free API key (No credit card required).
3. Enter it directly in the app.

**Security guarantees:**
- The key is sent via the `Authorization: Bearer` header.
- It is never logged, cached, or stored on the backend.
- The server discards it immediately after generating the strategic response.

---

## 📁 Project Structure

```
nyaya-mitra-mvp/
├── app/                          # FastAPI Backend
│   ├── api/routes/               # health, query, admin endpoints
│   ├── models/schemas.py         # Advanced structured JSON definitions
│   ├── retrieval/                # BM25 + Qdrant Reciprocal Rank Fusion (RRF)
│   └── services/llm_service.py   # Strict schema extraction prompt
├── nyaya-mitra-app/              # Mobile App (React Native)
│   └── src/
│       ├── components/           # Intelligence Dashboard UI (AiCard)
│       └── hooks/                # Server Health & Chat State
├── tests/                        # Pytest suite
└── etl_pipeline.py               # Data ingestion script
```

---

## ⚠️ Legal Disclaimer

Nyaya Mitra provides **legal intelligence and structured case analysis, not legal advice**. It is designed to prepare users for a productive consultation with a qualified human lawyer. Always consult a legal professional for your specific situation.

---

## 📄 License

MIT License — free to use, modify, and deploy.

---

*Built to make Indian legal strategy accessible to everyone.*
