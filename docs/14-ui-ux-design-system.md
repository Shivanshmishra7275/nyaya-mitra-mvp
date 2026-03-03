# 14 — UI/UX Design System
## Nyaya Mitra — Color Palette, Typography, and React Native Component Guidelines

**Version:** 1.0.0  
**Date:** March 2026

---

## 1. Design Philosophy

Nyaya Mitra serves two personas with very different contexts:
- **Citizen (B2C):** Intimidated by legal complexity; needs clarity, simplicity, reassurance
- **Advocate (B2B):** Needs information density, efficiency, professional credibility

The design system uses **deep blues** (trust, authority, law) with **clean whites** (clarity, accessibility) to serve both personas from a single design language.

---

## 2. Color System

```javascript
// constants/Colors.js
export const Colors = {
  // ── Brand Palette ────────────────────────────────────────────
  brandDark:      '#0D2B55',   // Deep navy — header backgrounds, screen top
  brandMid:       '#1A4F8A',   // Mid-navy — user chat bubbles, primary actions
  brandAccent:    '#2979FF',   // Bright blue — CTAs, active states, send button
  brandLight:     '#E8F0FE',   // Tint — subtle backgrounds behind sections
  
  // ── Surface Palette ──────────────────────────────────────────
  screenBg:       '#F0F4F8',   // Page/screen background (light gray-blue)
  cardBg:         '#FFFFFF',   // Card surfaces, AI response cards
  inputBg:        '#FFFFFF',   // Text inputs
  inputBorder:    '#CBD5E1',   // Input borders (neutral)
  divider:        '#E2E8F0',   // Section dividers, separators
  
  // ── Text Palette ─────────────────────────────────────────────
  textPrimary:    '#0F172A',   // Main body text (near-black)
  textSecondary:  '#475569',   // Subtext, helper text, labels
  textDisabled:   '#94A3B8',   // Disabled states
  textOnDark:     '#FFFFFF',   // Text on dark brand backgrounds
  textOnBrand:    '#E2EDFF',   // Soft white on mid-navy (user bubble text)
  
  // ── Semantic Colors ──────────────────────────────────────────
  citationBg:     '#EEF3FF',   // Citation pill background
  citationBorder: '#2979FF',   // Citation pill border
  citationText:   '#1A4F8A',   // Citation pill text
  stepBg:         '#F1F5F9',   // Next-step item background
  stepBorder:     '#CBD5E1',   // Next-step item border
  errorBg:        '#FEF2F2',   // Error message background
  errorText:      '#B91C1C',   // Error message text
  errorBorder:    '#FECACA',   // Error message border
  successBg:      '#F0FDF4',   // Success state background
  successText:    '#15803D',   // Success state text
  warningBg:      '#FFFBEB',   // Warning / disclaimer background
  warningText:    '#92400E',   // Warning text
  warningBorder:  '#FCD34D',   // Warning border
};
```

---

## 3. Typography

```javascript
// Based on React Native system fonts + expo-google-fonts (Phase 2)
export const Typography = {
  // Headers
  h1: { fontSize: 28, fontWeight: '700', color: Colors.textPrimary, lineHeight: 36 },
  h2: { fontSize: 22, fontWeight: '700', color: Colors.textPrimary, lineHeight: 30 },
  h3: { fontSize: 18, fontWeight: '600', color: Colors.textPrimary, lineHeight: 26 },
  
  // Body
  bodyLarge:   { fontSize: 16, fontWeight: '400', color: Colors.textPrimary, lineHeight: 24 },
  bodyMedium:  { fontSize: 14, fontWeight: '400', color: Colors.textPrimary, lineHeight: 22 },
  bodySmall:   { fontSize: 12, fontWeight: '400', color: Colors.textSecondary, lineHeight: 18 },
  
  // UI Elements
  label:       { fontSize: 13, fontWeight: '600', color: Colors.textSecondary, lineHeight: 18 },
  button:      { fontSize: 16, fontWeight: '600', color: Colors.textOnDark, lineHeight: 22 },
  citation:    { fontSize: 12, fontWeight: '700', color: Colors.citationText, lineHeight: 18 },
  disclaimer:  { fontSize: 11, fontWeight: '400', color: Colors.textSecondary, lineHeight: 16, fontStyle: 'italic' },
};
```

---

## 4. Spacing System

```javascript
// 4px base unit grid
export const Spacing = {
  xs:   4,    // Tight padding inside small elements
  sm:   8,    // Default item padding
  md:   12,   // Card internal padding
  lg:   16,   // Screen horizontal padding
  xl:   20,   // Section gaps
  xxl:  24,   // Large section gaps
  xxxl: 32,   // Screen-level breathing room
};

export const BorderRadius = {
  sm:   6,    // Small chips, inputs
  md:   10,   // Cards, message bubbles
  lg:   16,   // Modal sheets, large cards
  full: 999,  // Pill-shaped citation tags
};
```

---

## 5. Component Specifications

### 5.1 `CitationPill`
```jsx
// Visual appearance:
// ┌─────────────────────────────────┐
// │ ● BNS — Section 303, Page 87   │  ← citationBg fill, citationBorder stroke
// └─────────────────────────────────┘

const styles = {
  citationPill: {
    backgroundColor: Colors.citationBg,
    borderColor: Colors.citationBorder,
    borderWidth: 1,
    borderRadius: BorderRadius.full,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    marginRight: Spacing.sm,
    marginBottom: Spacing.sm,
    flexDirection: 'row',
    alignItems: 'center',
  },
  citationPillText: {
    ...Typography.citation,
  },
};
```

### 5.2 `AiMessageCard`
```jsx
// Visual structure:
// ┌──────────────────────────────────────────────┐
// │ 🤖 Nyaya Mitra                               │ ← brandDark header
// ├──────────────────────────────────────────────┤
// │ LEGAL EXPLANATION                            │ ← h3 label
// │ Under BNS Section 303, theft is defined...   │ ← bodyMedium
// ├──────────────────────────────────────────────┤
// │ SOURCES                                      │ ← label
// │ [BNS — Section 303] [BNS — Section 304]      │ ← CitationPills (wrap)
// ├──────────────────────────────────────────────┤
// │ SUGGESTED NEXT STEPS                         │ ← label
// │  1. File an FIR at...                        │ ← NextStepItems
// │  2. Consult an advocate...                   │
// ├──────────────────────────────────────────────┤
// │ ⚠ This is AI-generated legal information...  │ ← disclaimer, warningBg
// └──────────────────────────────────────────────┘

const styles = {
  card: {
    backgroundColor: Colors.cardBg,
    borderRadius: BorderRadius.lg,
    overflow: 'hidden',
    marginBottom: Spacing.lg,
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.08,
    shadowRadius: 8,
    shadowOffset: { width: 0, height: 2 },
  },
};
```

### 5.3 `UserBubble`
```jsx
// Visual:
// ───────────────────────────────────────────────────────
//                            What is punishment for theft? │
//                                               ┌─────────┐│
//                                               │ brandMid ││
//                                               └─────────┘│
const styles = {
  userBubble: {
    backgroundColor: Colors.brandMid,
    borderRadius: BorderRadius.md,
    borderBottomRightRadius: 2,  // Chat bubble "tail"
    maxWidth: '75%',
    alignSelf: 'flex-end',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    marginBottom: Spacing.sm,
  },
  userBubbleText: {
    ...Typography.bodyMedium,
    color: Colors.textOnBrand,
  },
};
```

### 5.4 `DisclaimerBanner`
```jsx
const styles = {
  disclaimerBanner: {
    backgroundColor: Colors.warningBg,
    borderColor: Colors.warningBorder,
    borderWidth: 1,
    borderRadius: BorderRadius.sm,
    padding: Spacing.md,
    marginTop: Spacing.sm,
  },
  disclaimerText: {
    ...Typography.disclaimer,
    color: Colors.warningText,
  },
};
```

---

## 6. Screen Layout Specifications

### 6.1 ChatScreen Layout
```
SafeAreaView (screenBg)
├── Header View (brandDark, height: 60)
│   ├── Back button (textOnDark)
│   └── Title "Nyaya Mitra — Legal Assistant" (h3, textOnDark)
├── FlatList (flex: 1, paddingHorizontal: lg)
│   ├── [UserBubble] × n
│   └── [AiMessageCard] × n
│       └── Loading: [ActivityIndicator, brandAccent]
└── Input Row (cardBg, paddingHorizontal: lg, paddingVertical: md)
    ├── TextInput (inputBg, bodyMedium, borderRadius: md)
    └── Send Button (brandAccent, borderRadius: full, 44×44)
```

### 6.2 DraftScreen Layout
```
SafeAreaView (screenBg)
├── Header (brandDark)
│   └── Title "Draft Legal Document"
└── ScrollView
    ├── Section: "Select Document Type"
    │   └── Document type picker cards (2-column grid)
    │       Each card: icon + label + cardBg + active:brandLight border
    ├── Section: "Case Details"
    │   ├── TextInput: Accused Name
    │   ├── TextInput: Court Name
    │   └── TextArea: Describe the facts (min-height: 120)
    └── Submit Button (brandAccent, full-width, height: 52)
```

---

## 7. B2B Dashboard Design (Phase 3 — React Web)

For the Enterprise admin dashboard (React + web, not React Native):

```
Color additions:
  sidebarBg:    '#0D2B55'    (same brandDark)
  sidebarText:  '#8BAFD4'
  sidebarActive:'#FFFFFF'
  tableHeaderBg:'#F8FAFC'
  tableRowHover: '#F1F5F9'

Layout:
  Left sidebar (240px): org name, navigation links
  Top bar (64px): breadcrumb, user avatar, notifications
  Main content (flex): data tables, charts (Recharts)
  
Key screens:
  /dashboard    — query volume chart, top query topics
  /users        — seat management, usage per user
  /queries      — searchable query history table
  /analytics    — RAG quality metrics, feedback scores
  /settings     — API keys, knowledge base, SSO config
```

---

## 8. Accessibility Guidelines

| Guideline | Implementation |
|---|---|
| Minimum touch target | 44×44 points (all buttons) |
| Color contrast ratio | > 4.5:1 (WCAG AA) for all text |
| Text size | Minimum 12px, respects system font scale |
| Screen reader | `accessibilityLabel` on all interactive elements |
| Keyboard navigation | Full tab-order support on web dashboard |
| Loading states | Always show indicator — never leave user guessing |
