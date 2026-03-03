# 01 — Product Requirements Document (PRD)
## Nyaya Mitra — AI-Powered Legal Intelligence Platform for India

**Version:** 1.0.0  
**Date:** March 2026  
**Status:** MVP Active Development  
**Owner:** Product & Engineering

---

## 1. Executive Summary

Nyaya Mitra ("Legal Friend" in Hindi) is a **B2B2C Legal Tech SaaS platform** designed specifically for the Indian legal ecosystem. It leverages Retrieval-Augmented Generation (RAG) over India's core criminal law corpus — the Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), Bharatiya Sakshya Adhiniyam (BSA), and the Constitution of India — to deliver two distinct value propositions:

1. **Citizen Triage (Freemium B2C):** Plain-language legal Q&A for citizens who cannot afford counsel.
2. **Advocate Drafting Workspace (Premium B2B):** AI-assisted legal document drafting, case research, and argument structuring for law firms and independent advocates.

---

## 2. Problem Statement

| Stakeholder | Pain Point |
|---|---|
| Common Citizen | Cannot understand dense legal language; cannot afford a lawyer for basic queries |
| Junior Advocate | Spends hours manually searching BNS/BNSS for relevant sections |
| Law Firm (B2B) | No intelligent drafting tool tuned for Indian law; generic LLMs hallucinate on Indian statutes |
| Legal Aid NGO | No scalable, low-cost triage tool for high-volume intake of cases |

---

## 3. Business Model: Freemium B2B2C

```
┌─────────────────────────────────────────────────────────────────┐
│  FREE TIER (B2C Citizen)                                        │
│  • 5 legal queries/day via chat                                 │
│  • Plain-language explanations only                             │
│  • Citations to law sections (read-only)                        │
│  • Mobile-first (Expo React Native)                             │
├─────────────────────────────────────────────────────────────────┤
│  PRO TIER  ₹999/month (Individual Advocate)                     │
│  • Unlimited queries                                             │
│  • AI Document Drafting (FIR, Bail Application, Legal Notice)  │
│  • Export to PDF/DOCX                                           │
│  • Query history & bookmarks                                    │
├─────────────────────────────────────────────────────────────────┤
│  ENTERPRISE TIER  ₹15,000/month per seat (Law Firms / NGOs)    │
│  • Multi-user workspace with role-based access                  │
│  • Custom knowledge base ingestion (case files)                 │
│  • API access for integration with case management systems      │
│  • Dedicated SLA + onboarding                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Target Users

### Primary User — Citizen (B2C)
- Age: 18–55, Tier 2/3 cities
- Use case: "My landlord is threatening me, what can I do?"
- Device: Android smartphone, low bandwidth
- Language: Prefers Hindi / regional language explanations

### Secondary User — Advocate (B2B)
- Age: 25–45, metro cities
- Use case: Drafting bail applications, finding precedents
- Device: Laptop / iPad
- Expectation: Accuracy > Speed; citations must be verifiable

### Tertiary User — Law Firm Admin (Enterprise B2B)
- Use case: Deploying Nyaya Mitra for 10–50 associates
- Expectation: SSO, audit logs, usage analytics

---

## 5. Core Features (MVP Scope)

### 5.1 Legal Q&A Chat (RAG Engine)
- **Input:** Natural language query in English
- **Processing:** ChromaDB semantic search (K=15 chunks) → Gemini 2.5 Flash generation
- **Output:** Structured JSON `{explanation, citations, suggested_next_steps}`
- **Constraint:** Response grounded ONLY in ingested legal corpus (no hallucination of external laws)

### 5.2 Document Drafting Engine
- **Input:** Document type selection + user-provided facts
- **Processing:** Template + RAG context → Gemini generation
- **Output:** Draft legal document (markdown → exportable)
- **Supported Types (MVP):** FIR Draft, Bail Application, Legal Notice, Complaint Letter

### 5.3 Citation Engine
- Every AI claim must cite `{source_document} — Section {X}, Page {Y}`
- Citations displayed as tappable pills in UI
- Clicking a citation shows the raw legal text excerpt

---

## 6. Non-Functional Requirements

| Requirement | Target |
|---|---|
| Response Latency (P95) | < 4 seconds end-to-end |
| RAG Retrieval Accuracy | > 85% relevant chunk retrieval on test set |
| Hallucination Rate | < 5% on Indian law corpus |
| API Uptime | 99.5% (MVP); 99.9% (Enterprise) |
| Mobile Load Time | < 2s on 4G |
| Data Residency (Enterprise) | India region preferred (AWS Mumbai ap-south-1) |

---

## 7. Legal & Ethical Constraints

- Platform explicitly states it **does not provide legal advice** — it provides legal information.
- Every response includes a disclaimer: *"This is AI-generated legal information, not legal advice. Consult a qualified advocate for your specific situation."*
- Personal data (case facts entered by users) must NOT be used for model training without explicit consent.
- Sensitive personal information (Aadhaar, case details) must be encrypted at rest.

---

## 8. Success Metrics (MVP KPIs)

| KPI | 30-Day Target | 90-Day Target |
|---|---|---|
| DAU (Citizen) | 500 | 5,000 |
| Pro Subscriptions | 50 | 500 |
| Query Response Quality (thumbs up) | 70% | 85% |
| Avg Session Duration | 4 min | 7 min |
| P95 API Latency | < 4s | < 3s |
