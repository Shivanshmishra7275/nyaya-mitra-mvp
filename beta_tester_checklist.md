# Nyaya Mitra Beta Tester Checklist

Thank you for testing Nyaya Mitra! We are launching a controlled beta MVP to validate our legal retrieval architecture. 

Please follow this checklist and report your findings to the development team.

## 1. Setup & Connection 🔌
- [ ] Open the app on your device (Android/iOS).
- [ ] Tap the Key Icon (🔑) in the top right.
- [ ] Enter your Gemini API Key.
- [ ] Tap "Test Connection". Did it show "✓ Connected"? 
- [ ] Does the UI feel responsive?

## 2. Core Legal Queries ⚖️
Ask the following types of questions and note the quality of the response:

- [ ] **Direct Fact Question:** *"What is the punishment for theft under the Bharatiya Nyaya Sanhita (BNS)?"*
  - *Quality Check:* Did it correctly identify Section 303 of BNS? Was the tone neutral?
- [ ] **Procedural Question:** *"Under BNSS, how is a search warrant issued?"*
  - *Quality Check:* Did it cite the correct sections and outline steps?
- [ ] **Edge Case/Out of Scope:** *"What is the capital of France?"*
  - *Quality Check:* Did the bot refuse to answer or state it couldn't find legal context?

## 3. Transparency & Citations 📜
- [ ] Check the "CITED SOURCES" pills below an answer. Are they readable and relevant?
- [ ] Check the "SUGGESTED NEXT STEPS". Are they actionable and non-prescriptive (e.g., "Consult a lawyer")?
- [ ] Use the "Copy" (⎘) button. Paste the result into your notes app. Did it format correctly?

## 4. Privacy & Persistence 🔒
- [ ] Close the app completely (swipe it away).
- [ ] Reopen the app. 
- [ ] Are your previous messages still visible? (Chat history should persist).
- [ ] Can you ask a new question immediately? (API Key should securely persist).

## Feedback / Bug Report
If you encountered any errors (red cards), please copy the text and send it to the team. 
- General thoughts on the UI/UX:
- Missing features you expected:
- Any hallucinated (fake) laws detected?
