# GeM Sentinel — AI-Powered Bid Compliance Verification Platform
SIH 2026 · PS #26100 · Ministry of Petroleum & Natural Gas / CPCL

An evidence-grounded compliance and risk verification layer for GeM bid
evaluation. The AI extracts and explains; a deterministic rule engine
decides PASS/FAIL/WAIVED/REVIEW; the procurement officer makes the final
call. Every finding traces back to a document, page, or verification
source — nothing is asserted without evidence.

## What's included

- **Deterministic rule engine** (`backend/app/services/rules/`) — evaluates
  tender clauses expressed as AND/OR/exception logic trees, not flat rules.
  Handles the exact cases most systems get wrong: OR conditions, MSME
  exemption waivers, mandatory-failure hard-gating regardless of overall
  pass rate.
- **Risk engine** (`backend/app/services/risk/`) — transparent, versioned,
  weighted signal scoring, kept independent from compliance status.
- **Adapter layer** (`backend/app/adapters/`) — `PortalAdapter` interface
  with mock GSTN/MCA/NSIC/Udyam/DigiLocker/Blacklist implementations.
  Swapping mock for real integrations is a one-line change in
  `registry.py`, nothing else. API downtime always resolves to
  `UNAVAILABLE`, never a false failure.
- **Evaluation orchestrator** (`backend/app/services/evaluation.py`) — wires
  documents, live adapter checks, the rule engine, and the risk engine into
  one bid evaluation.
- **FastAPI app** (`backend/app/main.py`) — officer + bidder API surfaces.
  Runs on an in-memory demo dataset (`app/demo_data.py`) so there's zero
  infra setup for the hackathon; `db/schema.sql` is the real Postgres
  schema this would run against in production.
- **React frontend** (`frontend/`) — officer dashboard, bid detail with
  evidence drill-down, audit trail, and bidder pre-submission readiness
  check.
- **23 automated tests** covering the rule engine, risk/LLM-independence
  guarantee, and adapter contracts (including a deliberately flaky adapter
  proving API outages never become auto-fails).

## Demo scenarios seeded

| Bidder | Demonstrates |
|---|---|
| Northline Engineering | Clean pass — all mandatory clauses PASS, low risk |
| Coastal Agro Supplies | Fails the turnover/experience OR-clause; EMD correctly WAIVED via MSME exemption |
| Meridian Textiles | GSTIN identity contradiction — bid claims one company, GSTN registry shows another, caught live via the adapter |

## Running it

### Backend
```bash
cd backend
pip install -r requirements.txt --break-system-packages
python -m pytest tests/ -v          # confirm 23/23 pass
python -m uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

Sign in as either role with any email/password (demo auth). Officer sees
the bid queue at `/officer`; bidder sees the readiness check at
`/bidder/readiness`.

## What's real vs. mocked (stated honestly, not hidden)

- Rule engine, risk engine, adapter contract, audit-log shape: fully real,
  fully tested.
- GSTN/MCA/NSIC/Udyam/DigiLocker verification: mock data, per PS26100's
  own allowance ("dummy bidder and tender datasets may be used"). Adapter
  interface is architecture-ready for real integration.
- Document OCR/entity extraction and LLM clause extraction: not yet
  wired into this build — facts are seeded directly in `demo_data.py`
  in the exact shape the real pipeline would produce.
- Forged-document forensics, multilingual/handwritten OCR, fraud-prediction
  ML: explicitly out of scope, not attempted.

See the planning conversation for the full architecture review, schema
design, API contracts, and AI pipeline design this build follows.
