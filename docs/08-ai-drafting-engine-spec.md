# 08 — AI Drafting Engine Specification
## Nyaya Mitra — Document Generation Logic and Prompt Architecture

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. Overview

The AI Drafting Engine is the Premium (Pro/Enterprise) feature that generates full legal documents by combining:
1. **User-provided facts** (names, dates, charges, court)
2. **RAG-retrieved legal provisions** (relevant BNS/BNSS/BSA sections)
3. **Structured templates** (court-compliant formatting)
4. **Gemini 2.5 Flash generation** (language and reasoning)

---

## 2. Supported Document Types (MVP)

| Document Type | Key Input Fields | Primary Law Sources | Avg Output Length |
|---|---|---|---|
| `bail_application` | accused_name, facts, court, sections_charged | BNSS §480, §483 | 800–1200 words |
| `anticipatory_bail` | accused_name, facts, court, apprehension_reason | BNSS §482 | 700–1000 words |
| `fir_draft` | complainant_name, incident_facts, accused_name, date | BNS applicable sections | 400–600 words |
| `legal_notice` | sender_name, recipient_name, grievance_facts, demand | Relevant BNS/civil | 500–700 words |
| `complaint_letter` | complainant_name, authority, officer_name, facts | BNSS §175, §173 | 300–500 words |

---

## 3. Drafting Pipeline — Step by Step

```
┌─────────────────────────────────────────────────────────────────┐
│                   AI DRAFTING ENGINE FLOW                       │
│                                                                 │
│  1. REQUEST VALIDATION                                          │
│     ├── Validate document_type is in supported list            │
│     ├── Validate facts length (50–5000 chars)                  │
│     └── Check user tier: Pro/Enterprise only                   │
│                                                                 │
│  2. LEGAL CONTEXT RETRIEVAL                                     │
│     ├── Build semantic query from document_type + facts         │
│     │   e.g. "bail application conditions BNSS Section 480"    │
│     ├── ChromaDB.query(K=10)                                   │
│     └── Filter by law_code relevance (BNSS for bail)           │
│                                                                 │
│  3. TEMPLATE LOADING                                            │
│     ├── Load /templates/{document_type}.txt                    │
│     ├── Parse {{PLACEHOLDER}} fields                           │
│     └── Inject known values (accused_name, court, date)        │
│                                                                 │
│  4. GEMINI PROMPT ASSEMBLY                                      │
│     ├── System prompt: judicial drafting persona               │
│     ├── Legal context block (K=10 chunks)                      │
│     ├── Template with filled placeholders                       │
│     ├── User facts                                              │
│     └── Output format instructions                              │
│                                                                 │
│  5. GENERATION (Gemini 2.5 Flash)                               │
│     ├── temperature=0.3 (slightly creative for language)       │
│     ├── max_output_tokens=4096                                  │
│     └── Response = complete draft document string              │
│                                                                 │
│  6. POST-PROCESSING                                             │
│     ├── Extract citations from generated text                   │
│     ├── Append mandatory disclaimer                             │
│     └── Return DraftDocumentResponse                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Template Format (Bail Application Example)

```
{# templates/bail_application.txt #}

IN THE {{COURT_NAME}}

BAIL APPLICATION
Under Section 480 of the Bharatiya Nagarik Suraksha Sanhita, 2023

IN THE MATTER OF:
State vs. {{ACCUSED_NAME}}

RESPECTFULLY SHOWETH:

1. That the applicant {{ACCUSED_NAME}} was arrested on {{ARREST_DATE}} 
   by {{ARRESTING_AUTHORITY}}.

2. That the applicant has been charged under the following sections:
   {{SECTIONS_CHARGED}}

3. GROUNDS FOR BAIL:
   {{AI_GENERATES_GROUNDS_HERE}}

4. RELEVANT LEGAL PROVISIONS:
   {{AI_INSERTS_RELEVANT_SECTIONS_HERE}}

5. PRAYER:
   In light of the above, it is most humbly prayed that this Hon'ble Court 
   may be pleased to grant bail to the applicant {{ACCUSED_NAME}} on such 
   terms and conditions as this Court may deem fit and proper.

Date: {{TODAY_DATE}}
Place: {{COURT_CITY}}

Respectfully submitted,
Advocate for the Applicant
```

---

## 5. Gemini Drafting Prompt

```python
DRAFTING_SYSTEM_PROMPT = """You are a senior Indian advocate with 20 years of 
experience drafting legal documents in accordance with Indian procedural law. 
You draft documents exclusively based on the provided legal provisions and facts.

STRICT RULES:
1. Use formal legal language appropriate for Indian courts.
2. Only cite sections/provisions that appear in the LEGAL CONTEXT below.
3. Fill in all {{PLACEHOLDER}} fields using the provided facts.
4. Do NOT invent facts, dates, names, or case numbers not provided.
5. Do NOT include any statements you cannot ground in the provided legal context.
6. Format the document with proper headings and numbered paragraphs.
7. Output ONLY the draft document text — no commentary, no markdown code blocks."""

DRAFTING_USER_PROMPT = """
LEGAL CONTEXT (Retrieved Provisions):
{legal_context}

DOCUMENT TEMPLATE:
{template_content}

USER-PROVIDED FACTS:
{user_facts}

Additional Details:
- Accused Name: {accused_name}
- Court: {court_name}
- Sections Charged: {sections_charged}
- Today's Date: {today_date}

Generate the complete, filled-in legal document now.
"""
```

---

## 6. Citation Extraction (Post-Processing)

```python
import re

def extract_citations_from_draft(draft_text: str) -> list[str]:
    """
    Extracts law citations from generated draft text.
    Patterns matched:
      - "Section 480 of BNSS"
      - "BNS Section 303"  
      - "Article 21 of the Constitution"
    """
    patterns = [
        r'(?:BNS|BNSS|BSA)\s+(?:Section|Sec\.?)\s+\d+[A-Z]?',
        r'Section\s+\d+[A-Z]?\s+of\s+(?:the\s+)?(?:BNS|BNSS|BSA|Constitution)',
        r'Article\s+\d+[A-Z]?\s+of\s+the\s+Constitution',
    ]
    citations = []
    for pattern in patterns:
        matches = re.findall(pattern, draft_text, re.IGNORECASE)
        citations.extend(matches)
    return list(set(citations))
```

---

## 7. Quality Guardrails

| Guardrail | Implementation |
|---|---|
| Hallucinated sections | Only retrieve from ChromaDB; system prompt forbids citing unlisted sections |
| Fabricated names | Template system pre-fills names; Gemini instructed not to invent |
| Missing mandatory fields | Template validator checks required placeholders before Gemini call |
| Too-short output | `min_output_tokens=200`; retry once if output < 200 words |
| Inappropriate content | Gemini safety filters active; output checked for legal coherence |

---

## 8. Phase 2 Enhancements

- **PDF Generation:** `WeasyPrint` or `reportlab` to convert draft markdown → court-ready PDF
- **Letterhead Templates:** Law firm logo + address injection for Enterprise tier
- **Precedent Matching:** Search past Supreme Court/HC judgments for similar bail grants
- **Hindi Draft Mode:** Translate draft to Hindi using Gemini translation capability
