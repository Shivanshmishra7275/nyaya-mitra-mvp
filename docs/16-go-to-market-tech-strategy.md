# 16 — Go-To-Market Tech Strategy
## Nyaya Mitra — Technical Requirements to Demo and Sell to Law Firms

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. GTM Technical Readiness Checklist

Before approaching any law firm for a sales demo or pilot, the following technical bar must be met:

### Minimum Viable Demo (MVP)
```
✅ Working Android APK installable on any Android 10+ phone
✅ ChatScreen demo with 5 curated showcase queries (under 3s each)
✅ DraftScreen demo: Bail application draft generated in < 5s
✅ Citations pointing to real BNS/BNSS sections
✅ DisclaimerBanner visible on every AI response
✅ No crashes during a 20-minute live demo
✅ Works on tethered hotspot (no office WiFi dependency)
```

### For Paid Pilot (Law Firm)
```
✅ Cloud deployment (not localhost) — accessible from firm's office
✅ HTTPS endpoint (SSL certificate)
✅ Basic authentication (even simple API key header)
✅ No hardcoded data shown during demo
✅ Uptime > 99% during pilot period
✅ Query logs available for pilot feedback analysis
```

---

## 2. Demo Environment Setup

### Canned Showcase Queries (Pre-tested, high-quality responses)
```python
SHOWCASE_QUERIES = [
    # Citizen-focused (B2C demo)
    "What is the punishment for theft under the new BNS law?",
    "Can police arrest someone without a warrant under BNSS?",
    "What are my rights if I am arrested and detained?",
    
    # Advocate-focused (B2B demo)
    "What are the grounds for bail under BNSS Section 480?",
    "What evidence is admissible under the Bharatiya Sakshya Adhiniyam?",
]

# Verify these every week before demos
# Each must return: 
#   - explanation > 100 words
#   - at least 2 citations
#   - at least 2 next steps
#   - latency < 3 seconds
```

### Demo Script for Law Firm Sales Call
```
1. Open Nyaya Mitra app (or web demo)
2. Ask Showcase Query #5 (advocate-focused bail query)
3. Highlight citations — "Every answer cites the exact section and page number"
4. Tap on the DraftScreen tab
5. Select "Bail Application", enter sample client name "Rahul Sharma"
6. Enter 2-3 lines of facts in the text field
7. Press Generate — show the complete draft appearing in < 5 seconds
8. Highlight disclaimer at bottom — "We tell every user this is information, not advice"
9. Say: "This draft saves 2-3 hours of initial research per application"
```

---

## 3. Technical Stack for Sales Demo

### Option A: Expo Go Demo (Fastest — Works Today)
```powershell
# Presenter's laptop runs the backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Attendee devices join same WiFi or hotspot
# Update API_URL in ApiConfig.js to presenter's LAN IP
# Distribute via Expo Go QR code (expo start --tunnel)
```

### Option B: Hosted Demo URL (Professional)
```
Deploy backend to:   https://demo.nyayamitra.in/api  (AWS EC2 t3.micro)
Serve web version:   https://demo.nyayamitra.in      (Expo Web build)
SSL:                 Let's Encrypt via Certbot

# Client demo link — shareable before meeting:
https://demo.nyayamitra.in
```

### Option C: APK/TestFlight for Leave-Behind
```
EAS Build command:
  npx eas build --platform android --profile preview

Outputs: .apk file installable on any Android device
Share via Google Drive or direct download link
```

---

## 4. Target Law Firm Segments (B2B GTM)

| Segment | Size | Pain Point | Entry Point |
|---|---|---|---|
| Independent Criminal Advocates | 1–3 lawyers | Spends hours on BNS/BNSS research | Pro plan ₹999/mo |
| Mid-size Criminal Law Firms | 5–25 advocates | NJunior advocates inconsistent research quality | Enterprise ₹15,000/mo |
| Legal Aid NGOs | 5–20 paralegals | High volume of citizen intake with limited staff | Enterprise (NGO pricing) |
| Law College Clinics | 3–10 students + faculty | Practice tool for mock courts | EDU pricing ₹499/mo |
| Corporate Legal Departments | 10–50 in-house counsel | Need quick reference on employee criminal liability | Phase 3 (after BNSS coverage) |

---

## 5. Pilot Program Technical Requirements

For a 30-day paid pilot with a law firm (₹5,000 onboarding fee):

### Technical Deliverables
```
1. Dedicated subdomain: lawfirm-name.nyayamitra.in
2. Branded splash screen (firm name + logo) in app
3. Basic analytics dashboard (queries per day, top topics)
4. Weekly PDF report: query volume, response quality scores
5. Pilot feedback form integrated in app (thumbs up/down → form)
```

### Pilot Success Metrics
```
Primary:    Advocates use it > 3 times/week during pilot
Secondary:  > 60% thumbs-up rate on responses  
Tertiary:   At least 1 documented time saving ("saved 2 hours on bail draft")
Conversion: > 30% of pilots convert to paid annual subscription
```

---

## 6. Technical Competitive Differentiation

When talking to law firms, these are the technical differentiators to emphasize:

| Claim | Technical Proof |
|---|---|
| "Grounded in Indian law, no hallucinations" | ChromaDB retrieval + system prompt constraints + citation links to page numbers |
| "Cites exact section and page" | metadata.source + metadata.page in every ChromaDB chunk |
| "Understands the NEW Indian laws" | Trained on BNS/BNSS/BSA 2023, not old IPC/CrPC |
| "Works offline in court" | Phase 2: on-device ChromaDB via SQLite + edge embeddings |
| "Never shares your client data" | Local ChromaDB in MVP; data residency SLA in enterprise |
| "Customized for your firm's practice areas" | Enterprise: upload custom PDFs to ChromaDB collection |

---

## 7. Integration Requirements for Enterprise Sales

Law firms will ask about integration with their existing tools:

### Case Management Integration (Phase 3)
```
LeadMinds / MyAdvo API:
  - Import client matters as drafting context
  - Export generated drafts back to case file

Court NCMS Integration:
  - Look up case number → import charges as context
  
Email Integration:
  - Send draft via email directly from DraftResultScreen
```

### API Access for Enterprise
```
# Enterprise clients get a dedicated API key:
POST https://api.nyayamitra.in/api/v1/legal-query
Authorization: Bearer <enterprise_api_key>
X-Org-ID: law-firm-uuid

# Rate limits: 10,000 queries/month per seat
# SLA: 99.9% uptime, < 3s P95 latency
# Dedicated support Slack channel
```

---

## 8. Revenue Projections (Technical Scale Requirements)

| Users | Monthly Queries | Gemini Cost Est. | Infra Cost | Revenue |
|---|---|---|---|---|
| 100 Free + 10 Pro | ~5,000 | ~₹1,500 | ₹2,000 (EC2) | ₹9,990 |
| 1,000 Free + 100 Pro | ~50,000 | ~₹15,000 | ₹5,000 | ₹99,900 |
| 10K Free + 500 Pro + 5 Enterprise | ~500,000 | ~₹1,50,000 | ₹20,000 | ₹12,24,900 |

*Gemini 2.5 Flash estimated cost: ~₹0.30 per 1,000 input tokens + ₹1.20 per 1,000 output tokens*

At ₹10L+ MRR, infrastructure must be scaled to:
- Load-balanced EC2 (3×t3.medium)  
- PGVector on RDS (db.t3.medium)
- CloudFront CDN for web assets
- ElastiCache Redis for rate limiting + response caching
