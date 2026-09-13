# Phase 0: Database Persistence + Authentication/RBAC

## Overview

Phase 0 establishes the foundational infrastructure for GeM Sentinel:
- **Database Persistence**: PostgreSQL replaces all in-memory dictionaries
- **Authentication**: JWT token-based authentication with bcrypt password hashing
- **Authorization**: Role-based access control (RBAC) - bidder, officer, admin
- **Audit Trail**: Immutable, hash-chained audit events with full traceability

## Architecture

### Database Layer
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic for version control
- **Database**: PostgreSQL (required for Phase 0+)
- **Connection Pooling**: Automatic via SQLAlchemy

**Tables Created**:
- organizations, users, tenders, tender_versions, clauses, bids, documents
- extracted_facts, entity_resolution_results, verification_results, compliance_results
- risk_signals, risk_assessments, officer_decisions, audit_events

### Authentication Layer
- **Framework**: python-jose (JWT), passlib (password hashing)
- **Algorithm**: HS256 for JWT signing
- **Expiration**: Configurable (default 60 minutes)
- **Password Hashing**: Argon2 (salt-based, non-reversible)

### Authorization Layer
- **Middleware**: JWT validation on all protected endpoints
- **Decorator**: `@require_role(*allowed_roles)` for endpoint protection
- **Roles**: bidder, officer, admin
- **Enforcement**: Server-side (not frontend-only)

### API Structure

#### Public Endpoints (No Auth Required)
```
POST   /api/auth/login                    - Authenticate and get JWT token
GET    /health                            - Health check
GET    /api/tenders                       - List published tenders
```

#### Officer Endpoints (`@require_role("officer")`)
```
POST   /api/officer/tenders               - Create tender (DRAFT)
POST   /api/officer/tenders/{id}/publish  - Publish tender (PUBLISHED)
GET    /api/officer/bids                  - List all bids
GET    /api/officer/bids/{bid_id}         - View bid details & documents
```

#### Bidder Endpoints (`@require_role("bidder")`)
```
GET    /api/bidder/bids                   - List own bids
POST   /api/bidder/tenders/{id}/bids      - Create bid for tender (DRAFT)
GET    /api/bidder/bids/{bid_id}          - View own bid details
POST   /api/bidder/bids/{id}/documents/*  - Upload document
GET    /api/bidder/bids/{id}/documents    - List documents
DELETE /api/bidder/bids/{id}/documents/*  - Delete document
POST   /api/bidder/bids/{id}/submit       - Submit bid (DRAFT → SUBMITTED)
```

#### Audit Endpoints (All Roles)
```
GET    /api/audit                         - Get full audit trail
GET    /api/bids/{bid_id}/audit           - Get bid-specific audit trail
```

## Workflows

### Officer Creates & Publishes Tender

```
1. Officer logs in
   POST /api/auth/login
   {"email": "officer@gem.gov", "password": "officer123"}
   → Returns JWT token

2. Officer creates tender (DRAFT)
   POST /api/officer/tenders
   {"title": "Procurement RFP", "version_number": "1.0"}
   → Audit logged: TENDER_CREATED

3. Officer publishes tender (DRAFT → PUBLISHED)
   POST /api/officer/tenders/{tender_id}/publish
   → Audit logged: TENDER_PUBLISHED
   → Tender now visible to bidders
```

### Bidder Creates Bid & Uploads Documents

```
1. Bidder logs in
   POST /api/auth/login
   {"email": "abc@bidder.com", "password": "password123"}
   → Returns JWT token

2. Bidder sees published tenders
   GET /api/tenders
   → Lists all PUBLISHED tenders

3. Bidder creates bid (DRAFT state)
   POST /api/bidder/tenders/{tender_id}/bids
   → Audit logged: BID_CREATED
   → Bid linked to bidder's organization

4. Bidder uploads documents
   POST /api/bidder/bids/{bid_id}/documents/GST_CERT
   → File stored on disk (backend/uploads/{bid_id}/)
   → Document metadata stored in DB
   → File hash calculated and stored
   → Audit logged: DOCUMENT_UPLOADED
   → OCR status: PENDING (Phase 3)

5. Bidder submits bid (DRAFT → SUBMITTED)
   POST /api/bidder/bids/{bid_id}/submit
   → Audit logged: BID_SUBMITTED
   → Bid visible to officers in queue
```

### Officer Reviews Submitted Bid

```
1. Officer sees submitted bids
   GET /api/officer/bids
   → Returns all bids with current status

2. Officer views bid details
   GET /api/officer/bids/{bid_id}
   → Includes documents, file hashes, OCR status
   → Can drill down to audit trail

3. Officer views audit trail for bid
   GET /api/bids/{bid_id}/audit
   → Shows full history: who did what, when
   → Hash chain proves integrity
```

## Security Principles

### 1. Authentication
- ✅ Passwords hashed with Argon2 (salt-based, never reversible)
- ✅ JWT tokens signed with HS256 algorithm
- ✅ Tokens expire after JWT_EXPIRATION_MINUTES (default 60)
- ✅ Tokens cannot be forged (secret key required)

### 2. Authorization
- ✅ Role-based access control enforced on every endpoint
- ✅ Bidder cannot access officer endpoints (403 Forbidden)
- ✅ Officer cannot access bidder-only endpoints (403 Forbidden)
- ✅ Bidder can only see their own organization's bids
- ✅ Officer can see all bids

### 3. Data Integrity
- ✅ User ID derived from JWT token (not from request body)
- ✅ Organization ID derived from authenticated user (not from request body)
- ✅ All state changes audit-logged with actor, timestamp, details
- ✅ Audit events hash-chained for tamper detection

### 4. Persistence
- ✅ All state in PostgreSQL (no in-memory dictionaries)
- ✅ Transactional: changes committed or rolled back atomically
- ✅ Connection pooling prevents resource exhaustion

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+psycopg2://gemsentinel:gemsentinel@localhost:5432/gemsentinel
TEST_DATABASE_URL=postgresql+psycopg2://gemsentinel:gemsentinel@localhost:5432/gemsentinel_test

# JWT
JWT_SECRET_KEY=dev-secret-change-in-production-12345
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Logging
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL
```bash
# Create user and database (as PostgreSQL admin)
createuser gemsentinel -P  # Enter password: gemsentinel
createdb gemsentinel -O gemsentinel
```

### 3. Run Migrations
```bash
# Apply all migrations
alembic upgrade head

# Check migration status
alembic current
```

### 4. Start Server
```bash
python -m uvicorn app.main:app --reload
```

Server starts on `http://localhost:8000`

### 5. Verify Setup

**Health check**:
```bash
curl http://localhost:8000/health
# Expected: {"status": "ok", "version": "0.1.0", "phase": "0"}
```

**Officer login**:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"officer@gem.gov","password":"officer123"}'
# Expected: {"access_token":"...", "token_type":"bearer", "expires_in":3600}
```

**Access protected endpoint**:
```bash
OFFICER_TOKEN="<token_from_login>"
curl http://localhost:8000/api/officer/bids \
  -H "Authorization: Bearer $OFFICER_TOKEN"
# Expected: [] (empty array, no bids yet)
```

## Demo Users (Seeded on Startup)

### Officers
- Email: `officer@gem.gov`
- Password: `officer123`
- Role: officer

### Bidders
| Email | Password | Organization |
|-------|----------|---|
| abc@bidder.com | password123 | ABC Manufacturing |
| xyz@bidder.com | password123 | XYZ Traders |
| ghi@bidder.com | password123 | GHI Services |
| pqr@bidder.com | password123 | PQR Consultants |
| stu@bidder.com | password123 | STU Solutions |

## Testing

### Run Tests
```bash
# All tests
pytest tests/ -v

# Core tests (rule engine, adapters, risk - no DB required)
pytest tests/test_rule_engine.py tests/test_adapters.py -v

# Phase 0 tests (requires PostgreSQL)
pytest tests/test_auth_phase0.py tests/test_db_phase0.py -v

# End-to-end workflows (requires PostgreSQL)
pytest tests/test_workflows_phase0.py -v
```

### Expected Results
- **Existing tests**: 23/23 passing (rule engine, adapters, risk engines unchanged)
- **Phase 0 auth tests**: 20+ passing (JWT, RBAC, passwords)
- **Phase 0 DB tests**: 20+ passing (CRUD, persistence, state transitions)
- **Phase 0 workflow tests**: 8+ passing (end-to-end bidder/officer scenarios)

## Acceptance Criteria

✅ **Database Persistence**
- All state in PostgreSQL (no in-memory dicts)
- Transactions ensure consistency
- Data persists across server restarts

✅ **Authentication**
- Officer and bidders can log in with credentials
- JWT tokens returned on success
- Invalid credentials return 401

✅ **Authorization**
- Bidder cannot access officer endpoints (403)
- Officer cannot access bidder endpoints (403)
- Bidder can only see own org's bids
- Officer can see all bids

✅ **Audit Trail**
- Every action logged: actor, timestamp, entity, action
- Hash chaining proves integrity
- Full workflow history available

✅ **No Regressions**
- Existing rule engine tests: 13/13 passing
- Existing adapter tests: 9/9 passing
- Existing risk engine tests: 1/1 passing

## Known Limitations

1. **SQLite Support**: Phase 0 tests use SQLite for isolation; production uses PostgreSQL
2. **OCR Not Wired**: Documents uploaded with `ocr_status=PENDING` (Phase 3 feature)
3. **Email Notifications**: Not implemented (Phase 13)
4. **AI Agents**: Not implemented (Phase 12, after deterministic pipeline stable)
5. **Document Storage**: Files stored on local disk; S3 planned for production

## Next Steps

After Phase 0 is stable:
- **Phase 1**: State machine transitions (DRAFT → SUBMITTED → VERIFYING → DECIDED)
- **Phase 2**: Evidence traceability (drill-down from compliance result to source)
- **Phase 3**: OCR/extraction pipeline (extract fields from documents)
- **Phase 4+**: Verification, compliance, risk, clarification workflows

## Troubleshooting

### "Connection refused" on startup
- Verify PostgreSQL is running: `psql -U postgres -d postgres -c "SELECT 1"`
- Check DATABASE_URL in .env

### "JSONB type not supported" in tests
- Tests using SQLite don't support JSONB columns (Phase 1+ feature)
- Run PostgreSQL tests separately when database available

### Tokens not working
- Check JWT_SECRET_KEY matches between generation and validation
- Verify tokens not expired (check JWT_EXPIRATION_MINUTES)
- Confirm Authorization header format: "Bearer {token}"

## References

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc7519)
- [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
