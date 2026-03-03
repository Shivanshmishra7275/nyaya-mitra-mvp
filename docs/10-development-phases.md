# 10 — Development Phases
## Nyaya Mitra — Step-by-Step Roadmap from MVP to Enterprise

**Version:** 1.0.0  
**Date:** March 2026

---

## Phase Timeline Overview

```
Phase 1: MVP                     Weeks 1–4      (NOW — Q1 2026)
Phase 2: Product-Market Fit      Weeks 5–12     (Q2 2026)
Phase 3: Scale & Monetize        Weeks 13–24    (Q3–Q4 2026)
Phase 4: Enterprise Platform     Months 7–12    (2027)
```

---

## Phase 1: MVP — Core RAG Platform (Weeks 1–4)

### Goals
- Deployable ChromaDB RAG pipeline with Gemini 2.5 Flash
- Working React Native chat interface
- AI document drafting (5 document types)
- Demo-ready for law firms and investors

### Week 1: Infrastructure & Data Pipeline
```
Day 1-2: Set up Python venv, install all dependencies
Day 3:   Place PDFs in Raw_Data/, run ETL pipeline
Day 4:   Verify ChromaDB populated (~1700 chunks)
Day 5:   Test semantic search quality manually
```

### Week 2: Backend Development
```
Day 1:   Rewrite main.py with ChromaDB integration
Day 2:   Implement /health and /legal-query endpoints
Day 3:   Implement /draft-document endpoint + templates
Day 4:   Add Pydantic validation + error handling
Day 5:   Manual API testing with curl/Postman
```

### Week 3: Frontend Development
```
Day 1:   Refactor App.js into screens/ and components/
Day 2:   Build ChatScreen with new response structure
Day 3:   Build DraftScreen + DraftResultScreen
Day 4:   Build HomeScreen onboarding
Day 5:   Connect all screens to apiService.js
```

### Week 4: Integration & QA
```
Day 1:   End-to-end testing (Android emulator)
Day 2:   Physical device testing (Expo Go)
Day 3:   Fix bugs from device testing
Day 4:   Performance optimization (cold start, query latency)
Day 5:   Demo preparation — prepare 5 showcase queries
```

**Phase 1 Deliverables:**
- ✅ Working RAG Q&A on ChromaDB
- ✅ Working document drafting (5 types)
- ✅ React Native app (Android + iOS)
- ✅ All 16 architecture documents in /docs

---

## Phase 2: Product-Market Fit (Weeks 5–12)

### Goals
- Monetizable product with auth + payments
- 500 beta users from law colleges + NGOs
- Measure query quality and iterate on prompts

### Week 5–6: Authentication Layer
```
- Implement JWT authentication (FastAPI + python-jose)
- User registration: email + phone OTP via Twilio/MSG91
- Login screen in React Native
- Session persistence (AsyncStorage on mobile)
```

### Week 7–8: Subscription & Payments
```
- Integrate Razorpay subscription API
- Free tier: 5 queries/day rate limiting (Redis)
- Pro tier: ₹999/month, unlimited queries
- Payment screen in React Native
- Webhook handler for subscription status
```

### Week 9–10: Query Quality Improvements
```
- Add thumbs up/down feedback on each AI response
- Implement hybrid retrieval: BM25 + ChromaDB (RRF)
- Add query history screen (fetch from PostgreSQL)
- Improve citation display: clickable → shows raw legal text
- A/B test prompt variants on sample queries
```

### Week 11–12: PostgreSQL Migration + Cloud Prep
```
- Migrate SQLite → PostgreSQL on AWS RDS
- Set up AWS EC2 t3.medium (FastAPI) + RDS
- Set up S3 bucket for PDF storage
- Basic Nginx reverse proxy + HTTPS
- Set up CloudWatch basic monitoring
```

**Phase 2 Deliverables:**
- Working auth + payments
- 500 beta users
- 70%+ positive feedback on query quality
- Cloud deployment (AWS Mumbai)

---

## Phase 3: Scale & Monetize (Weeks 13–24)

### Goals
- B2B enterprise sales to 10 law firms
- Hindi language support
- PDF export of drafted documents

### Week 13–16: Enterprise B2B Features
```
- Multi-tenant PostgreSQL (org_id isolation)
- Enterprise admin dashboard (React Native Web / React)
- Seat management + usage analytics
- Custom knowledge base: upload additional PDFs per org
- API key issuance for server-to-server integration
```

### Week 17–20: Hindi + Multilingual
```
- Multilingual embedding model: intfloat/multilingual-e5-large
- Hindi query → English retrieval → Hindi response pipeline
- Gemini instruction: "Respond in the same language as the query"
- Test on 50 Hindi queries, iterate on quality
```

### Week 21–24: Export + Sharing
```
- PDF generation: WeasyPrint or ReportLab
- Law firm letterhead injection for Enterprise tier
- WhatsApp share integration (Meta Business API)
- "Book an Advocate" feature (affiliate link to Bar Council registered advocates)
```

**Phase 3 Deliverables:**
- 10 paying enterprise customers
- Hindi support live
- PDF export working
- ₹10L+ ARR

---

## Phase 4: Enterprise Platform (Months 7–12)

### Goals
- Full enterprise-grade platform
- Kubernetes deployment
- Supreme Court + High Court judgment database

### Infrastructure Scale-Up
```
- Migrate ChromaDB → Pinecone (serverless) or pgvector
- Kubernetes on EKS (auto-scaling FastAPI pods)
- CDN for React Native Web (CloudFront)
- Elasticsearch for full-text judgment search
```

### Advanced AI Features
```
- Indian Kanoon API integration (case law database)
- Fine-tuned embedding model on Indian legal corpus
- Streaming responses via Server-Sent Events
- Voice input (Whisper API → text → RAG query)
- Legal calendar assistant (court dates, deadlines)
```

### Compliance & Governance
```
- SOC 2 Type II readiness
- ISO 27001 prep
- Data residency guarantee (all data in India)
- Full DPDP Act 2023 compliance audit
```

---

## Sprint Velocity Assumptions

- Team: 1 Senior Backend, 1 Senior Frontend, 1 ML Engineer, 1 Product Manager
- Sprint: 2 weeks
- Velocity: 40 story points / sprint

| Phase | Duration | Sprints | Estimated Cost (Team Salaries) |
|---|---|---|---|
| Phase 1 (MVP) | 4 weeks | 2 sprints | ₹2L |
| Phase 2 | 8 weeks | 4 sprints | ₹4L |
| Phase 3 | 12 weeks | 6 sprints | ₹6L |
| Phase 4 | 6 months | 12 sprints | ₹20L |
