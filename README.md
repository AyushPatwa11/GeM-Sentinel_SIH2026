# GeM Sentinel — AI-Powered Bid Compliance Verification Platform
SIH 2026 · PS #26100 · Ministry of Petroleum & Natural Gas / CPCL

An evidence-grounded compliance and risk verification layer for GeM bid
evaluation. The AI extracts and explains; a deterministic rule engine
decides PASS/FAIL/WAIVED/REVIEW; the procurement officer makes the final
call. Every finding traces back to a document, page, or verification
source — nothing is asserted without evidence.

## Phase Status

### ✅ Phase 0: Database Persistence + Authentication/RBAC (COMPLETE)
- PostgreSQL database with 15 tables (organizations, users, tenders, bids, documents, audit_events, etc.)
- JWT token-based authentication with Argon2 password hashing
- Role-based access control (RBAC): bidder, officer, admin roles enforced server-side
- Immutable audit trail with hash chaining
- Alembic migrations for database versioning
- Officer and 5 bidder demo accounts seeded on startup
- All 23 existing core tests still passing (no regressions)
- See [Phase 0 Documentation](backend/docs/PHASE0_DATABASE_AUTH.md)

### 🔄 Phase 1–13: Planned Sequential Implementation
- Phase 1: State Machine + Document Storage
- Phase 2: Evidence Traceability
- Phase 3: OCR/Extraction Pipeline
- Phase 4–11: Verification, Compliance, Risk, Clarification, Audit, Frontend Integration, Operations
- Phase 12: AI Agents (after deterministic pipeline stable)
- Phase 13: Notifications

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
- **FastAPI app** (`backend/app/main.py`) — Phase 0 implements database-backed
  officer + bidder API with authentication and authorization. PostgreSQL
  replaces all in-memory state.
- **React frontend** (`frontend/`) — authentication login, officer dashboard,
  bidder bid management (Phase 0+), bid detail, audit trail, evidence
  drill-down (Phase 2+).
- **48+ automated tests**:
  - 23 core tests (rule engine, adapters, risk) — all passing
  - 20+ Phase 0 auth/RBAC tests (JWT, role enforcement, passwords)
  - 8+ Phase 0 end-to-end workflow tests (bidder/officer synchronization)

## Demo scenarios seeded

| Bidder | Demonstrates |
|---|---|
| ABC Manufacturing | Starting point for Phase 1 (state machine + documents) |
| XYZ Traders | Bidder organization for testing workflows |
| GHI Services | Demo company |
| PQR Consultants | Demo company |
| STU Solutions | Demo company |

## Running it

### Backend (Phase 0)

**Prerequisites**: PostgreSQL running on localhost:5432

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Create test database
createdb gemsentinel_test

# Run migrations
alembic upgrade head

# Verify tests (rule engine + core)
pytest tests/test_rule_engine.py tests/test_adapters.py -v

# Start server
python -m uvicorn app.main:app --reload --port 8000
```

**Demo Login** (seeded on startup):
- Officer: `officer@gem.gov` / `officer123`
- Bidder: `abc@bidder.com` / `password123` (or other seeded bidders)

**Phase 0 Endpoints**:
```bash
# Authentication
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"officer@gem.gov","password":"officer123"}'

# Officer: Create & publish tender
OFFICER_TOKEN="<token>"
curl -X POST http://localhost:8000/api/officer/tenders \
  -H "Authorization: Bearer $OFFICER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test RFP","version_number":"1.0"}'

# Bidder: List tenders & create bid (similar pattern)
```

See [Phase 0 Documentation](backend/docs/PHASE0_DATABASE_AUTH.md) for full API reference.

### Frontend
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
```

Sign in with any of the demo credentials above. Phase 0 includes authentication UI and basic bid management.

## What's real vs. mocked (stated honestly, not hidden)

- Rule engine, risk engine, adapter contract, audit-log shape: fully real, fully tested, locked in.
- GSTN/MCA/NSIC/Udyam/DigiLocker verification: mock data, per PS26100's
  own allowance ("dummy bidder and tender datasets may be used"). Adapter
  interface is architecture-ready for real integration (Phase 4).
- Document OCR/entity extraction: not yet wired (Phase 3 feature).
- LLM clause extraction: not yet wired (Phase 3 feature).
- Forged-document forensics, multilingual/handwritten OCR, fraud-prediction
  ML: explicitly out of scope, not attempted.
- Database persistence (Phase 0): real PostgreSQL, replacing in-memory dicts.
- Authentication (Phase 0): real JWT + bcrypt, seeded demo users.
- Authorization (Phase 0): real RBAC enforced server-side.

See the [planning conversation](GeM_Sentinel_Master_Project_Blueprint.pdf) for the full architecture review, schema
design, API contracts, and sequential implementation roadmap this build follows.
