# Sudhaar

Sudhaar is a consent-first AI agent for loan journeys inside a Paytm-style app (fictional lender: Nimbus Finance).
When a loan moment breaks (a failed e-mandate, an EMI debited after closure, a dropped video KYC call), it explains the cause in the customer's language and proposes one fix.
Deterministic rules pick the fix, the model only words the message, and nothing runs until the customer taps yes.

> Concept prototype for the Paytm Build for India AI Hackathon. Not the Paytm app.

## Run it locally

You need Python 3.9+ with [uv](https://docs.astral.sh/uv/) and Node 18+.

### Backend (FastAPI, port 8000)

```bash
cd backend
uv sync
uv run uvicorn src.app:app --reload --port 8000
```

Without uv: `python -m venv .venv && source .venv/bin/activate && pip install -e .`, then run the same `uvicorn` command.

- Health check: <http://127.0.0.1:8000/api/health> (shows the active `demo_mode`)
- API docs: <http://127.0.0.1:8000/docs>
- Tests: `uv run pytest` (always run in offline mode, no API key needed)

Cases and the audit trail are stored in `backend/sudhaar.db` (SQLite, created on first start, git-ignored).

### Frontend (Next.js, port 3000)

```bash
cd frontend
npm install
npm run dev
```

- Customer phone view: <http://localhost:3000>
- Operator console: <http://localhost:3000/console>

The frontend calls `http://127.0.0.1:8000/api` by default. Set `NEXT_PUBLIC_API_URL` to point it elsewhere.

### Configuration

Put these in a `.env` file at the repo root or in `backend/` (both are git-ignored), or export them in your shell. Shell values win over `.env`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `GEMINI_API_KEY` | empty | Enables live message drafting by Gemini |
| `GEMINI_MODEL` | `gemini-3.5-flash-lite` | Model used for drafting |
| `DEMO_MODE` | `live` if a key is set, otherwise `offline` | See below |

## `DEMO_MODE=offline`

```bash
DEMO_MODE=offline uv run uvicorn src.app:app --port 8000
```

In offline mode the backend never calls Gemini. Every message comes from the approved templates in `backend/data/templates/{mr,hi,en}.json`, and the trace shows the row `TEMPLATE_FALLBACK · Approved template used` instead of an AI draft. Rules, the consent gate, actions and the audit trail behave exactly as in live mode, so the whole demo works with no network and no key.

In live mode the fallback chain is:

1. Gemini drafts the message (4 s timeout). The validator checks it.
2. If the validator rejects the draft, one retry within a 6 s total budget.
3. If Gemini is down, rate limited or rejected twice: the last validated draft for that persona and language, from `backend/data/llm_cache.json`.
4. If there is no cached draft: the approved template.

## The three personas

Mock customers live in `backend/data/personas/`. Each one has a trigger event and a playbook in `backend/data/playbooks/`.

| Persona | Who | Language | Moment (event, code) | Fix proposed by the rules |
| --- | --- | --- | --- | --- |
| Rohit Kamble | Delivery rider, Pune | Marathi | `MANDATE_FAILED`, NPCI code `AP15`: HDFC account ending 9012 lacked the required balance | `retry_mandate` on his SBI account ending 4521 |
| Asha Sharma | Senior accountant, Mumbai | Hindi | `EMI_DEBITED_AFTER_CLOSURE`, `LMS_POST_CLOSURE_DEBIT`: loan closed 4 Nov 2026, ₹4,500 debited 5 Nov | `create_ticket`: one consent returns three reference IDs (refund ticket, NOC request, credit bureau check) |
| Sunita Deshmukh | High school teacher, Nashik | Marathi | `VKYC_DROPPED`, `VKYC_NET_DROP`: video KYC call dropped at step 2 of 3 | `send_vkyc_resume_link` to her mobile ending 3210, valid 72 hours |

## Control boundary

These rules are enforced in code, not left to the prompt.

1. **Rules decide.** The proposed action, its parameters and the list of allowed actions come from deterministic Python (`backend/src/rules.py`), playbooks (YAML) and exact code-table lookups (`backend/data/code_tables.json`). No amount, date or decision originates in the model.
2. **AI only speaks.** Gemini receives a PII-masked context packet and writes the explanation and button label. Every draft passes `backend/src/validator.py` before a customer sees it: each number and date must exist in the case facts, the action must be in the allowed list, no banned claims ("guaranteed", "pre-approved" and their Hindi and Marathi equivalents), and the script must match the requested language. A rejected draft is never shown.
3. **Consent before any action.** `POST /api/events` only ever produces a proposal (`status: PROPOSED`). An action runs only through `POST /api/consent` with `consent_given: true`, and only if it is in the global allowlist and in that case's allowed actions. The customer ID is taken from the stored case, not from the request. An idempotency key makes a double tap return the first receipt instead of running twice. A decline is recorded and nothing runs.
4. **Never moves money.** The allowlist has seven actions: `retry_mandate`, `send_vkyc_resume_link`, `create_ticket`, `request_noc`, `request_bureau_correction`, `set_reminder`, `book_callback`. None of them debits, credits, waives a charge or edits KYC. A refund is a ticket raised for the lender, not a transfer.

Every stage (event, playbook, facts, code lookup, rules, draft, validator, consent, action) is written to the audit trail with a flag saying whether AI was involved. The operator console reads that trail.

## What is real vs mocked

| Area | Real in this repo | Mocked or simulated |
| --- | --- | --- |
| Product surface | Working Next.js phone view and operator console | Paytm-style look only. This is not the Paytm app and uses no Paytm system |
| Lender | | Nimbus Finance is fictional |
| Customers and data | PII masking of PAN and account numbers before anything reaches the model | Rohit, Asha and Sunita, their loans, ledgers and bank balances are JSON fixtures |
| Events | Event ingestion endpoint and playbook matching | Events are fired by the demo UI. There is no Paytm, NPCI or lender event feed |
| Error codes | Exact code-table lookup. `AP15` and `AP10` are tagged `NPCI_OFFICIAL` in the table | `LMS_*` and `VKYC_*` codes are invented and tagged `MOCK` |
| Rules | Deterministic Python rules and YAML playbooks | They evaluate mock facts |
| AI | Live Gemini API call with timeout, retry, cache and template fallback | Nothing when a key is set. With `DEMO_MODE=offline` no model is called at all |
| Validator | Real checks on every AI draft: numbers, dates, action, banned phrases, language | |
| Consent gate | Real allowlist, per-case permission check and idempotency | |
| Actions | | All seven are simulated. Reference IDs (`MND-…`, `TKT-REF-…`, `NOC-REQ-…`, `VKYC-SMS-…`) are generated locally. No mandate is registered, no ticket reaches a lender, no SMS or WhatsApp message is sent, no bureau is contacted |
| Money | | Nothing moves. Refund amounts and timelines on receipts are illustrative |
| Audit trail | Real SQLite persistence of cases and every pipeline stage | Local file only. No retention, access control or tamper protection |
| Voice | "Listen" uses the browser's built-in speech synthesis | Voice quality and language support depend on the browser |
| Auth and security | | None. CORS is open and there is no login. Local demo use only |
