# Implementation Plan: GeM AI/ML Bidder Compliance Verification Platform

## Overview

This implementation plan breaks down the 10-phase GeM AI/ML Based Bidder Compliance Verification Platform into concrete, executable coding tasks. The system automates procurement compliance verification across government e-Marketplace tenders using multi-source data verification, compliance rule engines, risk assessment, and officer decision support.

**Technology Stack:**
- Backend: Python 3.11+ (FastAPI, SQLAlchemy, Alembic, Pydantic)
- Frontend: React 18+ (TypeScript, Zustand/Redux, Axios)
- Database: PostgreSQL 14+
- Cache/Queue: Redis
- External APIs: DataGovIn, GSTIN Registry, MCA Portal, NSIC DB, Udyam Registry

**Total Estimated Tasks:** 75  
**Phases:** 10  
**Critical Path:** Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7

---

## Phase 1: Foundation & Authentication (8 tasks)

### 1.1 Database Schema Migration - Core Tables

- [ ] 1.1.1 Create initial Alembic migration for Organization, User, and Tender tables
  - **Acceptance Criteria:**
    - Migration file created at `backend/app/db/migrations/versions/0007_phase1_auth_schema.py`
    - Organization table with columns: id (UUID PK), legal_name, gstin, pan, cin, udyam_number, sector, turnover, address, created_at, updated_at
    - User table with columns: id (UUID PK), email (UNIQUE), password_hash, role (officer|bidder), organization_id (FK), created_at, updated_at
    - Tender table with columns: id (UUID PK), title, status (draft|published|closed), created_by (FK to User), organization_id (FK), created_at, updated_at
    - TenderVersion table with columns: id (UUID PK), tender_id (FK), version_number, source_document_path, published_at, created_at
    - Indexes: User(email), Organization(gstin, pan), Tender(status, created_by)
    - Foreign key constraints with ON DELETE CASCADE for cascade deletes
  - **File Path:** `backend/app/db/migrations/versions/0007_phase1_auth_schema.py`
  - **Requirements:** 1.1, 1.2, 1.3
  - **Effort:** M
  - **Dependencies:** None

- [ ] 1.1.2 Run migration and verify schema creation
  - **Acceptance Criteria:**
    - `alembic upgrade head` completes without errors
    - All tables created in test PostgreSQL database
    - All indexes present and queryable
    - Foreign key constraints enforced
  - **File Path:** `backend/app/db/base.py` (verify)
  - **Requirements:** 1.3
  - **Effort:** S
  - **Dependencies:** 1.1.1

### 1.2 User Authentication Service

- [ ] 1.2.1 Implement User registration endpoint (POST /api/auth/register)
  - **Acceptance Criteria:**
    - Endpoint accepts: email, password, role (officer|bidder), organization_id (bidder only)
    - Password hashed using Argon2 (passlib library with Argon2)
    - User record created in database
    - Validation: email must be valid, password >= 8 chars, role in [officer, bidder]
    - Returns: user_id, email, role, created_at
    - Duplicate email rejected with HTTP 400
    - Organization_id required for bidder role, optional for officer
  - **File Path:** `backend/app/security/auth.py` (new endpoints), `backend/app/schemas/auth.py` (request/response models)
  - **Requirements:** 1.1
  - **Effort:** M
  - **Dependencies:** 1.1.1

- [ ] 1.2.2 Implement User login endpoint (POST /api/auth/login)
  - **Acceptance Criteria:**
    - Endpoint accepts: email, password
    - Returns JWT token valid for 3600 seconds (1 hour)
    - JWT payload contains: user_id, email, role, organization_id
    - Uses HS256 algorithm with SECRET_KEY from environment
    - Invalid credentials return HTTP 401
    - Token included in response as: {"access_token": "...", "token_type": "bearer", "expires_in": 3600}
  - **File Path:** `backend/app/security/auth.py`
  - **Requirements:** 1.1
  - **Effort:** M
  - **Dependencies:** 1.2.1

- [ ] 1.2.3 Implement JWT token validation middleware
  - **Acceptance Criteria:**
    - Middleware extracts token from Authorization header (Bearer <token>)
    - Validates token signature and expiration
    - Rejects expired tokens with HTTP 401
    - Rejects missing/invalid format tokens with HTTP 401
    - Attaches user_id, role to request context
    - Skips validation for public endpoints (/api/auth/*, /api/bidder/tenders GET)
  - **File Path:** `backend/app/middleware/auth.py`
  - **Requirements:** 1.1, 1.4
  - **Effort:** M
  - **Dependencies:** 1.2.2

- [ ] 1.2.4 Implement Role-Based Access Control (RBAC) enforcement
  - **Acceptance Criteria:**
    - Decorator @require_role("officer") enforces officer-only access
    - Decorator @require_role("bidder") enforces bidder-only access
    - Officer endpoints: /api/officer/* accessible only to officers (HTTP 403 otherwise)
    - Bidder endpoints: /api/bidder/* accessible only to bidders (HTTP 403 otherwise)
    - Public endpoints return 200 for unauthenticated users
    - RBAC errors logged to audit trail
  - **File Path:** `backend/app/security/rbac.py` (enhance), `backend/app/middleware/auth.py`
  - **Requirements:** 1.1
  - **Effort:** M
  - **Dependencies:** 1.2.3

### 1.3 API Response Standardization

- [ ] 1.3.1 Implement global error handling and response formatting
  - **Acceptance Criteria:**
    - All API responses follow format: `{"detail": "message"}` for errors
    - HTTP 400 for validation errors with field-level error messages
    - HTTP 401 for authentication failures
    - HTTP 403 for authorization failures
    - HTTP 404 for resource not found
    - HTTP 500 for server errors
    - All errors logged with context: endpoint, user_id, timestamp, request_path
    - Custom exception classes: ValidationError, AuthenticationError, AuthorizationError, NotFoundError
  - **File Path:** `backend/app/main.py` (exception handlers), `backend/app/exceptions.py` (new)
  - **Requirements:** 1.4
  - **Effort:** S
  - **Dependencies:** None

- [ ] 1.3.2 Create request/response Pydantic models for consistency
  - **Acceptance Criteria:**
    - Base response model with status, data, message fields
    - Error response model with detail field
    - All endpoints use consistent response models
    - Pydantic validates all inputs before processing
    - Response timestamps in ISO 8601 format
  - **File Path:** `backend/app/schemas/common.py` (new), all endpoint schemas
  - **Requirements:** 1.4
  - **Effort:** S
  - **Dependencies:** None

### 1.4 User Profile and Organization Association

- [ ] 1.4.1 Implement GET /api/user/profile endpoint
  - **Acceptance Criteria:**
    - Returns authenticated user: id, email, role, organization (if linked)
    - Organization includes: id, legal_name, gstin, pan, udyam_number, sector, turnover, address
    - Bidders must have organization_id set, returns HTTP 400 if not
    - Officers return minimal organization info
  - **File Path:** `backend/app/security/auth.py` (add endpoint)
  - **Requirements:** 1.1, 1.2
  - **Effort:** S
  - **Dependencies:** 1.1.1, 1.2.1

- [ ] 1.4.2 Implement organization CRUD endpoints (GET /api/organizations/{org_id})
  - **Acceptance Criteria:**
    - GET retrieves organization with all fields
    - Fields: id, legal_name, gstin, pan, cin, udyam_number, sector, turnover, address, created_at
    - Only bidders can view their linked organization
    - Officers cannot view organization details (403)
    - Returns HTTP 404 if organization not found
  - **File Path:** `backend/app/services/organization_service.py` (new), routes in main.py
  - **Requirements:** 1.2
  - **Effort:** S
  - **Dependencies:** 1.1.1

### 1.5 Unit Tests for Authentication

- [ ]* 1.5.1 Write unit tests for authentication service
  - **Acceptance Criteria:**
    - Test user registration with valid/invalid inputs
    - Test password hashing with Argon2
    - Test login with correct/incorrect credentials
    - Test JWT token generation and validation
    - Test token expiration handling
    - Test RBAC enforcement (officer vs bidder access)
    - Minimum 90% code coverage for auth.py
  - **File Path:** `backend/tests/test_security_auth.py`
  - **Requirements:** 1.1
  - **Effort:** M
  - **Dependencies:** 1.2.1, 1.2.2, 1.2.3, 1.2.4

- [ ] 1.6 Checkpoint - Verify Authentication Foundation
  - Ensure all authentication tests pass: `pytest backend/tests/test_security_auth.py -v`
  - Verify database migrations: `alembic current`
  - Test manual endpoints: POST /api/auth/register, POST /api/auth/login, GET /api/user/profile
  - Check error handling for invalid inputs
  - Ask the user if questions arise.

---

## Phase 2: Tender Management & Bid Creation (10 tasks)

### 2.1 Tender Management Service

- [ ] 2.1.1 Create Alembic migration for Bid, Document, and related tables
  - **Acceptance Criteria:**
    - Migration file: `backend/app/db/migrations/versions/0008_phase2_bid_schema.py`
    - Bid table: id (UUID PK), tender_version_id (FK), bidder_org_id (FK), status (DRAFT|SUBMITTED|DECIDED), current_state, state_entered_at, state_metadata (JSON), submitted_at, created_at, updated_at
    - BidState table: id (UUID PK), bid_id (FK), state_exited, state_entered, exited_at, entered_at, metadata (JSON)
    - Document table: id (UUID PK), bid_id (FK), doc_type, file_path, file_hash (SHA256), ocr_status (PENDING|COMPLETED|FAILED), current_version, uploaded_at, deleted (boolean)
    - DocumentVersion table: id (UUID PK), document_id (FK), version_number, file_path, file_hash, ocr_status, extracted_text, uploaded_by (FK), uploaded_at, change_reason
    - Indexes: Bid(status), Bid(current_state), Bid(tender_version_id), Document(bid_id)
  - **File Path:** `backend/app/db/migrations/versions/0008_phase2_bid_schema.py`
  - **Requirements:** 2.1, 2.3, 3.1, 3.2
  - **Effort:** M
  - **Dependencies:** 1.1.1

- [ ] 2.1.2 Implement POST /api/officer/tenders endpoint (tender creation)
  - **Acceptance Criteria:**
    - Request body: {title: string, version_number?: string (default "1.0")}
    - Creates Tender record with status = "draft"
    - Creates TenderVersion record with published_at = NULL
    - Logs BID_CREATED audit event with officer_id and tender_id
    - Returns: {tender_id, title, version_number, status: "draft", created_at}
    - Tender created_by must match authenticated officer_id
    - Title required, max 500 chars
  - **File Path:** `backend/app/services/tender_service.py` (new)
  - **Requirements:** 2.1
  - **Effort:** M
  - **Dependencies:** 2.1.1

- [ ] 2.1.3 Implement POST /api/officer/tenders/{tender_id}/publish endpoint
  - **Acceptance Criteria:**
    - Requires officer role
    - Updates tender.status = "published", tender_version.published_at = current_timestamp
    - Logs TENDER_PUBLISHED audit event
    - Prevents publishing already-published tenders (idempotent, no state change)
    - Prevents title modification after publish
    - Returns: {tender_id, status: "published", published_at}
  - **File Path:** `backend/app/services/tender_service.py`
  - **Requirements:** 2.1
  - **Effort:** M
  - **Dependencies:** 2.1.2

- [ ] 2.1.4 Implement GET /api/officer/tenders endpoint (list officer's tenders)
  - **Acceptance Criteria:**
    - Returns all tenders created_by authenticated officer
    - Fields: id, title, status, version_number, published_at, clause_count, created_at
    - Filters by status optional (draft, published, closed)
    - Pagination supported: limit (default 20), offset (default 0)
    - Sorted by created_at DESC
  - **File Path:** `backend/app/services/tender_service.py`
  - **Requirements:** 2.1
  - **Effort:** S
  - **Dependencies:** 2.1.2

### 2.2 Tender Discovery for Bidders

- [ ] 2.2.1 Implement GET /api/bidder/tenders endpoint (public tender browse)
  - **Acceptance Criteria:**
    - Returns all tenders with status = "published"
    - Accessible to unauthenticated users (public endpoint)
    - Fields: id, title, organization_name, version_number, published_at, required_documents (array), clause_count
    - Pagination: limit (default 20), offset (default 0)
    - Filters: organization_id, status (optional)
    - Sorted by published_at DESC
  - **File Path:** `backend/app/services/tender_service.py`
  - **Requirements:** 2.2
  - **Effort:** S
  - **Dependencies:** 2.1.1

- [ ] 2.2.2 Implement GET /api/bidder/tenders/{tender_id} endpoint (tender details)
  - **Acceptance Criteria:**
    - Returns full tender details including clauses and requirements
    - Fields: id, title, organization, version_number, published_at, clauses (array), required_documents (array), evaluation_criteria (text), submission_deadline
    - Accessible to unauthenticated users
    - Returns HTTP 404 if tender not published
    - Clauses array: [{id, title, description, requirement_type}]
    - required_documents: ["GST_CERT", "PAN", "COI", ...]
  - **File Path:** `backend/app/services/tender_service.py`
  - **Requirements:** 2.2, 2.4
  - **Effort:** S
  - **Dependencies:** 2.1.1

### 2.3 Bid Creation and State Management

- [ ] 2.3.1 Implement POST /api/bidder/tenders/{tender_id}/bids endpoint (bid creation)
  - **Acceptance Criteria:**
    - Requires bidder role
    - Creates Bid record with status = "DRAFT", current_state = "DRAFT"
    - Links to authenticated bidder's organization_id
    - Links to latest published TenderVersion
    - Logs BID_CREATED audit event
    - Sets state_entered_at = current_timestamp, state_metadata = {}
    - Prevents multiple DRAFT bids per bidder per tender (returns HTTP 400)
    - Returns: {bid_id, tender_id, status: "DRAFT", created_at}
  - **File Path:** `backend/app/services/bid_service.py` (new)
  - **Requirements:** 2.3
  - **Effort:** M
  - **Dependencies:** 2.1.1

- [ ] 2.3.2 Implement GET /api/bidder/bids endpoint (list bidder's bids)
  - **Acceptance Criteria:**
    - Returns all bids for authenticated bidder's organization
    - Fields: id, tender_id, tender_title, status, current_state, compliance_status, risk_level, submitted_at, created_at
    - Pagination: limit (default 20), offset (default 0)
    - Filters by status optional (DRAFT, SUBMITTED, DECIDED)
    - Sorted by created_at DESC
  - **File Path:** `backend/app/services/bid_service.py`
  - **Requirements:** 2.3
  - **Effort:** S
  - **Dependencies:** 2.3.1

- [ ] 2.3.3 Implement state machine for bid lifecycle (BidStateMachine class)
  - **Acceptance Criteria:**
    - States: DRAFT → EVAL_STAGE1 → EVAL_STAGE2 → SUBMITTED → DECIDED
    - Validates state transitions (no invalid transitions allowed)
    - Records all state transitions in BidState table with exited_at, entered_at
    - Prevents direct submission without stage 1/2 verification
    - Stores state_metadata JSON with additional context
    - Returns: {previous_state, new_state, state_entered_at}
  - **File Path:** `backend/app/services/state_machine.py` (new)
  - **Requirements:** 10.2
  - **Effort:** M
  - **Dependencies:** 2.3.1

- [ ] 2.3.4 Write unit tests for bid creation and state management
  - **Acceptance Criteria:**
    - Test bid creation with valid/invalid inputs
    - Test multiple draft bids per bidder (should fail)
    - Test state transitions (valid and invalid)
    - Test audit logging for bid events
    - Minimum 85% coverage for bid_service.py
  - **File Path:** `backend/tests/test_bid_service.py`
  - **Requirements:** 2.3
  - **Effort:** M
  - **Dependencies:** 2.3.1, 2.3.3

### 2.4 Document Management Setup

- [ ] 2.4.1 Create documents directory and file storage configuration
  - **Acceptance Criteria:**
    - Directory structure: `/uploads/bids/{bid_id}/`
    - File naming: `{doc_type}_{uuid}.{extension}`
    - Environment variable: UPLOAD_DIR (default `/uploads`)
    - Ensure directory exists on startup
    - Verify write permissions
  - **File Path:** `backend/app/config.py`, `backend/app/main.py` (startup event)
  - **Requirements:** 3.1
  - **Effort:** S
  - **Dependencies:** None

- [ ] 2.4.2 Implement required_documents specification in Tender
  - **Acceptance Criteria:**
    - TenderVersion stores required_documents array: ["GST_CERT", "PAN", "COI", "BANK_STATEMENT", "ITR", "UDYAM", "CAPACITY_CERT"]
    - GET /api/bidder/tenders/{tender_id} returns required_documents list
    - Bidders can view which documents are required before bid creation
    - Officer can specify required_documents during tender creation
  - **File Path:** `backend/app/models/models.py` (add required_documents to TenderVersion), `backend/app/schemas/tender.py`
  - **Requirements:** 2.4, 3.3
  - **Effort:** S
  - **Dependencies:** 2.1.1

- [ ] 2.5 Checkpoint - Verify Tender and Bid Management
  - Test POST /api/officer/tenders (create tender)
  - Test POST /api/officer/tenders/{id}/publish
  - Test GET /api/bidder/tenders (browse published)
  - Test GET /api/bidder/tenders/{id} (view details)
  - Test POST /api/bidder/bids (create bid)
  - Test GET /api/bidder/bids (list bidder bids)
  - Verify state machine transitions
  - Ensure all tests pass
  - Ask the user if questions arise.

---

## Phase 3: Document Management & OCR Processing (12 tasks)

### 3.1 Document Upload and Hash Verification

- [ ] 3.1.1 Implement POST /api/bidder/bids/{bid_id}/documents endpoint (document upload)
  - **Acceptance Criteria:**
    - Accepts multipart form data: file (binary), doc_type (string from enum)
    - Validates file size < 10MB
    - Validates file type in [pdf, jpg, jpeg, png]
    - Validates doc_type in predefined list
    - Computes SHA256 file hash
    - Stores file to `/uploads/bids/{bid_id}/{doc_type}_{uuid}.{extension}`
    - Creates Document record: id (UUID), bid_id (FK), doc_type, file_path, file_hash, ocr_status = "PENDING", current_version = 1, uploaded_at
    - Returns: {document_id, version_number, file_hash, file_size, uploaded_at}
  - **File Path:** `backend/app/services/document_service.py` (new/enhance)
  - **Requirements:** 3.1
  - **Effort:** M
  - **Dependencies:** 2.4.1

- [ ] 3.1.2 Implement document file storage with integrity checks
  - **Acceptance Criteria:**
    - Files saved to disk with atomic writes (temp file → rename)
    - Directory permissions: 0o755 for directories, 0o644 for files
    - Prevent directory traversal attacks (sanitize file paths)
    - Verify file hash matches upload integrity
    - Clean up temp files on upload failure
    - Log file operations to audit trail
  - **File Path:** `backend/app/services/document_service.py`
  - **Requirements:** 3.1
  - **Effort:** M
  - **Dependencies:** 3.1.1

- [ ] 3.1.3 Implement duplicate file detection (same hash)
  - **Acceptance Criteria:**
    - Before storing file, check if file_hash already exists in same bid
    - If duplicate found, return HTTP 400 with message "Document already uploaded"
    - Allow same document to be uploaded as different versions (with version increment)
    - Log duplicate detection in audit trail
  - **File Path:** `backend/app/services/document_service.py`
  - **Requirements:** 3.1
  - **Effort:** S
  - **Dependencies:** 3.1.1

### 3.2 Document Versioning

- [ ] 3.2.1 Implement document re-upload as new version
  - **Acceptance Criteria:**
    - When uploading document with existing doc_type in same bid, create new DocumentVersion
    - Increment Document.current_version counter
    - Create DocumentVersion record: version_number, file_path, file_hash, ocr_status = "PENDING", uploaded_at, change_reason (optional)
    - Previous version remains in history (not deleted)
    - Returns new version number and previous version info
  - **File Path:** `backend/app/services/document_service.py`
  - **Requirements:** 3.2
  - **Effort:** M
  - **Dependencies:** 3.1.1

- [ ] 3.2.2 Implement GET /api/bidder/bids/{bid_id}/documents endpoint (list documents)
  - **Acceptance Criteria:**
    - Returns all documents for bid
    - Fields: id, doc_type, current_version, file_hash, uploaded_at, ocr_status
    - Returns current_version details by default
    - Optional query param: include_history=true to return all versions
  - **File Path:** `backend/app/services/document_service.py`
  - **Requirements:** 3.2
  - **Effort:** S
  - **Dependencies:** 3.1.1

- [ ] 3.2.3 Implement GET /api/bidder/documents/{document_id}/versions endpoint
  - **Acceptance Criteria:**
    - Returns all DocumentVersion records for document
    - Fields: version_number, file_hash, uploaded_at, uploaded_by, change_reason, ocr_status
    - Sorted by version_number ASC
    - Allows bidders to track document change history
  - **File Path:** `backend/app/services/document_service.py`
  - **Requirements:** 3.2
  - **Effort:** S
  - **Dependencies:** 3.2.1

### 3.3 Document Slot Validation (Stage 1 Verification)

- [ ] 3.3.1 Implement POST /api/bidder/bids/{bid_id}/verify-stage1 endpoint
  - **Acceptance Criteria:**
    - Checks if all required_documents uploaded for bid's tender
    - Returns: {passed: bool, slots: [{type: string, uploaded: bool}, ...], uploaded_mandatory: int, total_mandatory: int}
    - slots array lists each required doc_type and whether uploaded
    - Requires bidder role
    - Only DRAFT bids can proceed to stage 1
    - If passed=true, transitions bid state to EVAL_STAGE1
    - If passed=false, bid remains in DRAFT state
  - **File Path:** `backend/app/services/compliance_service.py` (or document_service.py)
  - **Requirements:** 3.3
  - **Effort:** M
  - **Dependencies:** 2.4.2, 3.1.1

- [ ] 3.3.2 Write unit tests for document validation
  - **Acceptance Criteria:**
    - Test missing required documents
    - Test all documents uploaded
    - Test partial upload scenarios
    - Test different document types
    - Minimum 85% coverage
  - **File Path:** `backend/tests/test_document_service.py`
  - **Requirements:** 3.3
  - **Effort:** S
  - **Dependencies:** 3.3.1

### 3.4 OCR Processing Integration

- [ ] 3.4.1 Create OCR Processor data model and job queue
  - **Acceptance Criteria:**
    - OCRJob table: id (UUID PK), document_version_id (FK), status (PENDING|PROCESSING|COMPLETED|FAILED), extracted_text (TEXT), error_message, created_at, completed_at
    - ExtractedFact table: id (UUID PK), document_version_id (FK), fact_type (name|address|date|phone|number), fact_value (string), confidence_score (0-100), extracted_at
    - Redis queue: ocr_jobs list for job distribution
    - Background worker polls queue and processes jobs
  - **File Path:** `backend/app/db/migrations/versions/0009_phase3_ocr_schema.py`, `backend/app/models/models.py`
  - **Requirements:** 3.4
  - **Effort:** M
  - **Dependencies:** 2.1.1

- [ ] 3.4.2 Implement OCR job enqueue on document upload
  - **Acceptance Criteria:**
    - When document uploaded, automatically enqueue OCRJob
    - Set status = "PENDING"
    - Store document_version_id reference
    - Add job to Redis queue with priority based on bid submission status
    - Returns immediately (async operation)
  - **File Path:** `backend/app/services/document_service.py`, `backend/app/services/ocr_service.py` (new)
  - **Requirements:** 3.4
  - **Effort:** M
  - **Dependencies:** 3.4.1

- [ ] 3.4.3 Implement OCR processor worker (background service)
  - **Acceptance Criteria:**
    - Worker retrieves OCRJob from Redis queue
    - Updates status = "PROCESSING"
    - Calls OCR library (pytesseract or similar) on document file
    - Extracts text from PDF/image
    - Creates ExtractedFact records for identified entities
    - Updates DocumentVersion.ocr_status = "COMPLETED"
    - On error, sets status = "FAILED" and stores error message
    - Logs OCR_COMPLETED or OCR_FAILED audit event
    - Returns to queue on failure (retry logic)
  - **File Path:** `backend/app/services/ocr_processor.py` (new), `backend/scripts/ocr_worker.py` (new)
  - **Requirements:** 3.4
  - **Effort:** L
  - **Dependencies:** 3.4.2

- [ ] 3.4.4 Implement entity extraction from OCR text
  - **Acceptance Criteria:**
    - Extract named entities: names, addresses, email, phone, PAN, GSTIN, bank account
    - Use regex patterns or NER library (spacy)
    - Create ExtractedFact records with fact_type and confidence_score
    - Confidence based on match quality (regex perfect=100, fuzzy match < 100)
    - Store extracted facts in ExtractedFact table
    - Indexable by bid_id for compliance rule evaluation
  - **File Path:** `backend/app/services/ocr_processor.py`
  - **Requirements:** 3.4, 4.1
  - **Effort:** M
  - **Dependencies:** 3.4.3

- [ ] 3.4.5 Implement OCR result retrieval endpoint
  - **Acceptance Criteria:**
    - GET /api/bidder/documents/{document_id}/ocr-status
    - Returns: {document_id, version_number, ocr_status, extracted_text (if completed), extracted_facts: [], error (if failed)}
    - Accessible to bidder and officers reviewing bid
    - Allows polling for OCR completion
  - **File Path:** `backend/app/services/document_service.py`, `backend/app/services/ocr_service.py`
  - **Requirements:** 3.4
  - **Effort:** S
  - **Dependencies:** 3.4.1, 3.4.3

- [ ] 3.5 Checkpoint - Document Upload and OCR Processing
  - Test POST /api/bidder/bids/{bid_id}/documents (upload)
  - Test file validation (size, type)
  - Test SHA256 hash computation
  - Test document versioning re-uploads
  - Test POST /api/bidder/bids/{bid_id}/verify-stage1 (doc slot check)
  - Test OCR job enqueuing
  - Verify background worker processes OCR
  - Test extracted facts creation
  - Ensure all tests pass
  - Ask the user if questions arise.

---

## Phase 4: Compliance Rule Engine (13 tasks)

### 4.1 Compliance Rule Definition and Storage

- [ ] 4.1.1 Create Alembic migration for Compliance tables
  - **Acceptance Criteria:**
    - ComplianceRule table: id (UUID PK), rule_name, rule_version, logic_type (deterministic), conditions (JSON), actions (JSON), created_at
    - ComplianceResult table: id (UUID PK), bid_id (FK), rule_name, rule_version, passed (bool), evidence_references (JSON array), explanation (text), evaluated_at
    - RiskSignal table: id (UUID PK), bid_id (FK), signal_type, severity (HIGH|MEDIUM|LOW), description (text), detected_at
    - Indexes: ComplianceResult(bid_id), RiskSignal(bid_id, signal_type)
  - **File Path:** `backend/app/db/migrations/versions/0010_phase4_compliance_schema.py`
  - **Requirements:** 4.1
  - **Effort:** M
  - **Dependencies:** 2.1.1

- [ ] 4.1.2 Implement compliance rules registry (in-memory with DB sync)
  - **Acceptance Criteria:**
    - Rules defined as deterministic logic: if condition, then PASS or FAIL
    - Supported rules: name_consistency, gstin_valid, pan_valid, cin_valid, udyam_valid, bank_consistency, financial_threshold, sector_eligible, blacklist_check, duplicate_bidder
    - Each rule has: rule_name, rule_version (e.g., "1.0"), description, severity_on_fail (HIGH|MEDIUM|LOW)
    - Rules stored in database for audit trail
    - Rules versioned to track changes over time
    - In-memory cache for performance
  - **File Path:** `backend/app/services/compliance_rules.py` (new)
  - **Requirements:** 4.1
  - **Effort:** M
  - **Dependencies:** 4.1.1

- [ ] 4.1.3 Implement rule condition language (simple DSL or JSON)
  - **Acceptance Criteria:**
    - Rule conditions expressed as JSON with operators: AND, OR, NOT, EQUAL, CONTAINS, MATCHES_REGEX
    - Example: `{"AND": [{"FIELD": "ocr_name", "EQUAL": "org_name"}, {"NOT": {"FIELD": "gstin", "EMPTY": true}}]}`
    - Evaluator executes JSON conditions against bid data
    - Returns: {passed: bool, reason: string}
  - **File Path:** `backend/app/services/compliance_rules.py`
  - **Requirements:** 4.1
  - **Effort:** M
  - **Dependencies:** 4.1.2

### 4.2 Compliance Evaluation Pipeline

- [ ] 4.2.1 Implement POST /api/bidder/bids/{bid_id}/verify-stage2 endpoint
  - **Acceptance Criteria:**
    - Requires EVAL_STAGE1 state (document slot validation passed)
    - Executes all applicable compliance rules
    - Returns compliance evaluation results
    - Transitions bid state to EVAL_STAGE2
    - Response: {compliance_status: COMPLIANT|NON_COMPLIANT, rule_results: [{rule: string, passed: bool, explanation: string}, ...]}
    - Logs COMPLIANCE_EVALUATED audit event
    - Takes up to 30 seconds (includes external verification calls)
  - **File Path:** `backend/app/services/compliance_orchestrator.py` (new)
  - **Requirements:** 4.2
  - **Effort:** L
  - **Dependencies:** 4.1.2

- [ ] 4.2.2 Implement compliance rule evaluation executor
  - **Acceptance Criteria:**
    - Evaluates each rule against bid data (documents, OCR extracts, organization data)
    - Extracts required data from: DocumentVersion.extracted_text, ExtractedFact table, Organization table, Bid.state_metadata
    - Creates ComplianceResult record for each rule: rule_name, passed, evidence_references, explanation
    - Collects all results and aggregates
    - Sets bid compliance_status = "COMPLIANT" (all pass) or "NON_COMPLIANT" (any fail)
  - **File Path:** `backend/app/services/compliance_service.py` (new)
  - **Requirements:** 4.2
  - **Effort:** L
  - **Dependencies:** 4.1.2

- [ ] 4.2.3 Implement individual compliance rules (name consistency, GSTIN, PAN)
  - **Acceptance Criteria:**
    - Rule 1: name_consistency - Compares Organization.legal_name vs OCR extracted name (case-insensitive, allow minor typos)
    - Rule 2: gstin_valid - Validates GSTIN format (15 chars alphanumeric) and checks against extracted GSTIN from documents
    - Rule 3: pan_valid - Validates PAN format (10 chars) and checks against Organization.pan
    - Rule 4: cin_valid - Validates CIN format (21 chars) if applicable
    - Each rule returns: {passed: bool, extracted_value: string, org_value: string, confidence_score: float}
    - Failed rules store evidence in ComplianceResult.evidence_references
  - **File Path:** `backend/app/services/compliance_service.py`
  - **Requirements:** 4.2
  - **Effort:** M
  - **Dependencies:** 4.2.2

- [ ] 4.2.4 Implement remaining compliance rules (financial, sector, blacklist)
  - **Acceptance Criteria:**
    - Rule 5: financial_threshold - Check Organization.turnover >= threshold (configurable, default 0)
    - Rule 6: sector_eligible - Check Organization.sector matches tender requirements
    - Rule 7: blacklist_check - Check bidder not in blacklist (from external source or manual entry)
    - Rule 8: duplicate_bidder - Check if same organization bidding multiple times in same tender (reject duplicates)
    - Each rule follows ComplianceResult pattern
  - **File Path:** `backend/app/services/compliance_service.py`
  - **Requirements:** 4.2
  - **Effort:** M
  - **Dependencies:** 4.2.3

### 4.3 Rule Evidence Traceability

- [ ] 4.3.1 Implement evidence linking in compliance results
  - **Acceptance Criteria:**
    - ComplianceResult.evidence_references stores: [{document_id, extracted_fact_id, text_excerpt}, ...]
    - Links failed rule back to source documents
    - Stores extracted_fact_id for entity-level traceability
    - Includes text_excerpt (50-100 chars) from document supporting/contradicting rule
  - **File Path:** `backend/app/services/compliance_service.py`, `backend/app/services/evidence_traceability.py` (new)
  - **Requirements:** 4.3
  - **Effort:** M
  - **Dependencies:** 4.2.2

- [ ] 4.3.2 Implement GET /api/officer/bids/{bid_id}/compliance-details endpoint
  - **Acceptance Criteria:**
    - Returns detailed compliance evaluation
    - Fields: rule_name, passed, evidence (array of documents with excerpts), explanation
    - Allows officer to drill into each failed rule
    - Returns linked document IDs for viewing
    - Public audit trail showing rule changes over time
  - **File Path:** `backend/app/services/compliance_service.py`
  - **Requirements:** 4.3
  - **Effort:** S
  - **Dependencies:** 4.3.1

- [ ] 4.3.3 Implement GET /api/officer/documents/{document_id}/evidence endpoint
  - **Acceptance Criteria:**
    - Returns document with highlighted extracts used in compliance rules
    - Shows which rules referenced this document
    - Returns: {document_id, ocr_text, extracts_used: [{rule_name, text_excerpt, match_type}]}
    - Helps officer understand document-to-rule linkage
  - **File Path:** `backend/app/services/evidence_traceability.py`
  - **Requirements:** 4.3
  - **Effort:** M
  - **Dependencies:** 4.3.1

### 4.4 Risk Signal Generation

- [ ] 4.4.1 Implement risk signal creation on rule failure
  - **Acceptance Criteria:**
    - When ComplianceResult.passed = false, create RiskSignal
    - RiskSignal fields: bid_id (FK), signal_type (= rule_name), severity (HIGH|MEDIUM|LOW), description (failure explanation), detected_at
    - Severity mapping: gstin_invalid (HIGH), pan_invalid (HIGH), name_mismatch (MEDIUM), financial_threshold_miss (MEDIUM), unverified_source (LOW)
    - Multiple signals possible per bid (one per failed rule)
    - RiskSignals stored for historical tracking (no deletion)
  - **File Path:** `backend/app/services/risk_service.py` (new)
  - **Requirements:** 4.4, 6.1
  - **Effort:** M
  - **Dependencies:** 4.2.2

- [ ] 4.4.2 Write comprehensive tests for compliance rules
  - **Acceptance Criteria:**
    - Test each rule with valid/invalid data
    - Test evidence linking and traceability
    - Test risk signal generation
    - Test compliance aggregation (COMPLIANT vs NON_COMPLIANT)
    - Minimum 90% coverage for compliance_service.py
  - **File Path:** `backend/tests/test_compliance_service.py`
  - **Requirements:** 4.1, 4.2
  - **Effort:** L
  - **Dependencies:** 4.2.4, 4.4.1

- [ ] 4.5 Checkpoint - Compliance Engine
  - Test POST /api/bidder/bids/{bid_id}/verify-stage2 (compliance evaluation)
  - Test individual rules with passing/failing data
  - Verify ComplianceResult records created
  - Verify RiskSignal records created on failures
  - Test evidence linking and document references
  - Test GET /api/officer/bids/{bid_id}/compliance-details
  - Ensure all tests pass
  - Ask the user if questions arise.

---

## Phase 5: External Data Verification (12 tasks)

### 5.1 Multi-Source Adapter Architecture

- [ ] 5.1.1 Create Alembic migration for Verification tables
  - **Acceptance Criteria:**
    - VerificationResult table: id (UUID PK), bid_id (FK), source_name, verified (bool), details (JSON), confidence_score, verified_at
    - VerificationAttempt table: id (UUID PK), bid_id (FK), source_name, query_data (JSON), result (JSON), success (bool), error_message, verified_at, retry_count
    - EntityResolutionResult table: id (UUID PK), bid_id (FK), source1_name, source2_name, match_type (exact|fuzzy), confidence_score, resolved_legal_name
    - Indexes: VerificationResult(bid_id), VerificationAttempt(bid_id, source_name)
  - **File Path:** `backend/app/db/migrations/versions/0011_phase5_verification_schema.py`
  - **Requirements:** 5.1
  - **Effort:** M
  - **Dependencies:** 2.1.1

- [ ] 5.1.2 Enhance adapter orchestrator for parallel verification
  - **Acceptance Criteria:**
    - AdapterOrchestrator.verify_multi_source(bid_id, sources_list) method
    - Executes all source queries in parallel using asyncio
    - Uses aiohttp for async HTTP requests
    - Manages connection pooling and timeout (30 seconds per source)
    - Retry logic: 3 retries with exponential backoff (1s, 2s, 4s)
    - Aggregates results from all sources
    - Returns: {results: [{source, verified, details}], overall_status: VERIFIED|PARTIAL|FAILED}
  - **File Path:** `backend/app/services/adapter_orchestrator.py` (enhance)
  - **Requirements:** 5.1
  - **Effort:** L
  - **Dependencies:** 5.1.1

- [ ] 5.1.3 Implement adapter base class and interface
  - **Acceptance Criteria:**
    - Base class: BaseAdapter with abstract methods: query(), parse_response(), validate_result()
    - Each adapter inherits: GST
INAdapter, PANAdapter, MCAAdapter, NSICAdapter, UdyamAdapter
    - Consistent interface: query(gstin/pan/cin/udyam) → VerificationResult
    - Error handling: ConnectionError, TimeoutError, InvalidResponseError
    - All adapters stored in `backend/app/adapters/real_adapters/`
  - **File Path:** `backend/app/adapters/base.py` (enhance), `backend/app/adapters/real_adapters/`
  - **Requirements:** 5.1
  - **Effort:** M
  - **Dependencies:** 5.1.1

### 5.2 GSTIN Verification

- [ ] 5.2.1 Implement GSTIN Adapter (GST registration verification)
  - **Acceptance Criteria:**
    - Extract GSTIN from: bid state_metadata, organization.gstin, or OCR extracted facts
    - Query DataGovIn GSTIN registry API endpoint
    - Request: gstin_number, optional bidder_name
    - Response parsing: matched_legal_name, matched_status (active|inactive|suspended), matched_gstin
    - Returns VerificationResult: verified (bool), details {matched_name, status}, confidence_score
    - GSTIN not found → verified = false
    - GSTIN found but inactive → verified = false with warning
    - GSTIN found and active → verified = true
    - Store VerificationAttempt record (query_data, result, success)
  - **File Path:** `backend/app/adapters/real_adapters/gstin_adapter.py`
  - **Requirements:** 5.2
  - **Effort:** M
  - **Dependencies:** 5.1.3

- [ ] 5.2.2 Implement GSTIN validation logic
  - **Acceptance Criteria:**
    - GSTIN format: 15 chars, 2-digit state code + 10-digit entity code + 1 check digit + 1 entity type
    - Validation steps: format check, check digit validation (Luhn algorithm)
    - Returns: {valid: bool, error_if_invalid: string}
    - Used before calling external API
    - Rejects malformed GSTINs immediately
  - **File Path:** `backend/app/services/compliance_service.py` or `backend/app/adapters/real_adapters/gstin_adapter.py`
  - **Requirements:** 5.2
  - **Effort:** S
  - **Dependencies:** 5.2.1

- [ ] 5.2.3 Handle GSTIN vs name mismatch as risk signal
  - **Acceptance Criteria:**
    - When GSTIN found but legal_name doesn't match extracted name → RiskSignal (gstin_name_mismatch, severity HIGH)
    - Stores both names in signal description
    - Evidence references GSTIN verification result and OCR extraction
  - **File Path:** `backend/app/services/risk_service.py`
  - **Requirements:** 5.2, 4.4
  - **Effort:** S
  - **Dependencies:** 5.2.1, 4.4.1

### 5.3 Entity Resolution and Name Matching

- [ ] 5.3.1 Implement name extraction from multiple sources
  - **Acceptance Criteria:**
    - Extract bidder name from: Organization.legal_name, OCR DocumentVersion.extracted_facts (fact_type=name), Bid.state_metadata
    - Create name_variants list with source attribution
    - Deduplicate exact duplicates
    - Returns: {legal_name_from_org, extracted_names: [{source, name, confidence}]}
  - **File Path:** `backend/app/services/compliance_service.py`, `backend/app/services/evidence_traceability.py`
  - **Requirements:** 5.3
  - **Effort:** M
  - **Dependencies:** 3.4.4

- [ ] 5.3.2 Implement fuzzy name matching (Levenshtein distance)
  - **Acceptance Criteria:**
    - Compare name variants using Levenshtein distance
    - Confidence score: (1 - normalized_distance) * 100
    - confidence >= 95% → EXACT match equivalent (allows minor typos)
    - confidence 80-95% → FUZZY match (suspicious, create risk signal if not explained)
    - confidence < 80% → NO match (flag as name_mismatch risk signal)
    - Use Python difflib or Levenshtein library
  - **File Path:** `backend/app/services/name_matching.py` (new)
  - **Requirements:** 5.3
  - **Effort:** M
  - **Dependencies:** 5.3.1

- [ ] 5.3.3 Implement entity resolution result storage
  - **Acceptance Criteria:**
    - Create EntityResolutionResult record: bid_id, source1_name, source2_name, match_type (exact|fuzzy), confidence_score, resolved_legal_name
    - Store resolved_legal_name as canonical name for future reference
    - Link to VerificationResult for audit trail
    - Create RiskSignal if confidence < 95%
  - **File Path:** `backend/app/services/compliance_service.py`
  - **Requirements:** 5.3
  - **Effort:** S
  - **Dependencies:** 5.3.2

### 5.4 Verification Result Aggregation

- [ ] 5.4.1 Implement verification summary generation
  - **Acceptance Criteria:**
    - After all source queries complete, aggregate VerificationResult records
    - Summary: total_sources_queried, sources_verified (count), sources_failed (count), unresolved_conflicts (count)
    - Overall verification status: VERIFIED (all critical sources passed), PARTIAL (some passed), FAILED (critical source failed)
    - Critical sources: GSTIN, PAN (must verify for compliance)
    - Non-critical sources: NSIC, Udyam (enhance but not mandatory)
    - Store summary in VerificationSummary entity or ComplianceResult.verification_summary (JSON)
  - **File Path:** `backend/app/services/adapter_orchestrator.py`
  - **Requirements:** 5.4
  - **Effort:** M
  - **Dependencies:** 5.1.2

- [ ] 5.4.2 Implement GET /api/officer/bids/{bid_id}/verification-summary endpoint
  - **Acceptance Criteria:**
    - Returns verification results grouped by source
    - Fields: source_name, verified (bool), details, confidence_score, verified_at
    - Overall status and conflict summary
    - Links to external source data (if public)
    - Audit trail of verification attempts and retries
  - **File Path:** `backend/app/services/adapter_orchestrator.py`
  - **Requirements:** 5.4
  - **Effort:** S
  - **Dependencies:** 5.4.1

- [ ] 5.4.3 Write tests for verification adapters
  - **Acceptance Criteria:**
    - Mock external APIs (DataGovIn, GSTIN registry)
    - Test successful verification scenarios
    - Test failed verification (not found, invalid format, API error)
    - Test retry logic with exponential backoff
    - Test parallel execution of multiple adapters
    - Test name matching with fuzzy logic
    - Minimum 85% coverage
  - **File Path:** `backend/tests/test_adapter_orchestrator.py`, `backend/tests/test_adapters/*.py`
  - **Requirements:** 5.1-5.4
  - **Effort:** L
  - **Dependencies:** 5.1.3, 5.2.1, 5.3.3, 5.4.1

- [ ] 5.5 Checkpoint - External Verification
  - Test POST /api/bidder/bids/{bid_id}/verify-stage2 with verification integration
  - Verify GSTIN adapter calls
  - Test name matching and entity resolution
  - Test fuzzy matching confidence scores
  - Verify RiskSignal generation on mismatches
  - Test verification summary generation
  - Verify audit trail of verification attempts
  - Ensure all tests pass
  - Ask the user if questions arise.

---

## Phase 6: Risk Assessment & Scoring (10 tasks)

### 6.1 Risk Signal Aggregation

- [ ] 6.1.1 Create Alembic migration for RiskAssessment table
  - **Acceptance Criteria:**
    - RiskAssessment table: id (UUID PK), bid_id (FK, UNIQUE), overall_risk_score (float 0-100), risk_level (LOW|MEDIUM|HIGH), signal_breakdown (JSON), assessed_at
    - signal_breakdown JSON: {high_count, medium_count, low_count, signals: [{type, severity}]}
    - Indexes: bid_id (unique), assessed_at
  - **File Path:** `backend/app/db/migrations/versions/0012_phase6_risk_schema.py`
  - **Requirements:** 6.1
  - **Effort:** S
  - **Dependencies:** 2.1.1

- [ ] 6.1.2 Implement risk signal aggregation logic
  - **Acceptance Criteria:**
    - After compliance evaluation, count RiskSignals by severity
    - Aggregation rules:
      - high_count >= 1 → risk_level = HIGH
      - medium_count >= 2 AND high_count == 0 → risk_level = MEDIUM
      - low_count >= 3 AND high_count == 0 AND medium_count <= 1 → risk_level = MEDIUM
      - Otherwise → risk_level = LOW
    - Create RiskAssessment record with aggregated data
    - Return signal_breakdown JSON with counts
  - **File Path:** `backend/app/services/risk_service.py`
  - **Requirements:** 6.1
  - **Effort:** M
  - **Dependencies:** 6.1.1, 4.4.1

- [ ] 6.1.3 Implement risk level dashboard query
  - **Acceptance Criteria:**
    - GET /api/officer/dashboard/risk-summary
    - Returns: {total_bids, by_risk_level: {LOW: count, MEDIUM: count, HIGH: count}, average_risk_score}
    - Filters: tender_id (optional), date_range (optional)
    - Helps officers prioritize review efforts
  - **File Path:** `backend/app/services/risk_service.py`
  - **Requirements:** 6.1
  - **Effort:** S
  - **Dependencies:** 6.1.2

### 6.2 Risk Scoring Algorithm

- [ ] 6.2.1 Implement configurable risk weights
  - **Acceptance Criteria:**
    - RiskWeight table: signal_type (PK), weight (int 1-50), description, active (bool), updated_at
    - Default weights: gstin_invalid (25), pan_invalid (20), name_mismatch (15), duplicate_bidder (40), blacklisted (50), unverified_source (10), financial_threshold_miss (20)
    - Weights configurable without code changes
    - Load weights at startup and cache in memory
    - Provide admin endpoint to update weights (future phase)
  - **File Path:** `backend/app/db/migrations/versions/0012_phase6_risk_schema.py`, `backend/app/models/models.py`
  - **Requirements:** 6.2
  - **Effort:** M
  - **Dependencies:** 6.1.1

- [ ] 6.2.2 Implement risk score calculation
  - **Acceptance Criteria:**
    - For each RiskSignal, retrieve weight
    - Score += weight * (count + 1)  [count of similar signals]
    - Cap total score at 100 (sum of weights may exceed)
    - Formula: min(100, sum of (weight * signal_count for each signal type))
    - Recalculate on each new RiskSignal or compliance re-evaluation
    - Store final score in RiskAssessment.overall_risk_score
  - **File Path:** `backend/app/services/risk_service.py`
  - **Requirements:** 6.2
  - **Effort:** M
  - **Dependencies:** 6.2.1, 6.1.2

- [ ] 6.2.3 Implement risk level determination
  - **Acceptance Criteria:**
    - IF overall_risk_score >= 70 → risk_level = HIGH
    - IF 40 <= overall_risk_score < 70 → risk_level = MEDIUM
    - IF overall_risk_score < 40 → risk_level = LOW
    - Thresholds configurable via environment variables
    - Return risk_level in all bid detail responses
  - **File Path:** `backend/app/services/risk_service.py`
  - **Requirements:** 6.2
  - **Effort:** S
  - **Dependencies:** 6.2.2

### 6.3 Risk Signal Decomposition

- [ ] 6.3.1 Implement GET /api/officer/bids/{bid_id}/risk-details endpoint
  - **Acceptance Criteria:**
    - Returns RiskAssessment with detailed breakdown
    - Fields: overall_risk_score, risk_level, signal_breakdown {high_count, medium_count, low_count}
    - For each RiskSignal: signal_type, severity, detected_at, contributing_factors, evidence (document references)
    - Allows officer to understand why bid is flagged
    - Shows contributing compliance failures and verification mismatches
  - **File Path:** `backend/app/services/risk_service.py`
  - **Requirements:** 6.3
  - **Effort:** M
  - **Dependencies:** 6.1.2, 6.2.2

- [ ] 6.3.2 Implement RiskSignalDecomposition entity
  - **Acceptance Criteria:**
    - RiskSignalDecomposition table: id (UUID PK), signal_id (FK), contributing_factor (text), factor_weight (int), evidence_reference (JSON)
    - Breaks down why signal was generated (e.g., "GSTIN not found in registry" + "name mismatch with org record")
    - Stores decision logic and contributing factors
    - Helps officers understand signal generation
  - **File Path:** `backend/app/db/migrations/versions/0012_phase6_risk_schema.py`, `backend/app/models/models.py`
  - **Requirements:** 6.3
  - **Effort:** M
  - **Dependencies:** 6.1.1

- [ ] 6.3.3 Write comprehensive tests for risk assessment
  - **Acceptance Criteria:**
    - Test risk score calculation with various signal combinations
    - Test risk level determination (LOW, MEDIUM, HIGH)
    - Test weight configuration and impact on scoring
    - Test risk summary dashboard queries
    - Test edge cases (no signals, all high severity, mixed)
    - Minimum 90% coverage for risk_service.py
  - **File Path:** `backend/tests/test_risk_service.py`
  - **Requirements:** 6.1-6.3
  - **Effort:** M
  - **Dependencies:** 6.2.2, 6.3.1

- [ ] 6.4 Checkpoint - Risk Assessment
  - Test POST /api/bidder/bids/{bid_id}/verify-stage2 generates RiskAssessment
  - Verify RiskSignals aggregated correctly
  - Test risk score calculation with various signal weights
  - Test GET /api/officer/bids/{bid_id}/risk-details
  - Test GET /api/officer/dashboard/risk-summary
  - Verify risk_level determined correctly
  - Ensure all tests pass
  - Ask the user if questions arise.

---

## Phase 7: Officer Decision Support & Approvals (11 tasks)

### 7.1 AI Recommendation Generation

- [ ] 7.1.1 Implement recommendation engine logic
  - **Acceptance Criteria:**
    - IF compliance_status = "COMPLIANT" AND risk_level = "LOW" → PROCEED_TO_SUBMISSION
    - IF compliance_status = "COMPLIANT" AND risk_level = "MEDIUM" → PROCEED_WITH_CAUTION
    - IF compliance_status = "COMPLIANT" AND risk_level = "HIGH" → MANUAL_REVIEW_REQUIRED
    - IF compliance_status = "NON_COMPLIANT" → DO_NOT_PROCEED
    - Stores recommendation in RiskAssessment or new AIRecommendation entity
    - Recommendation includes explanation of key factors
  - **File Path:** `backend/app/services/recommendation_engine.py` (new)
  - **Requirements:** 7.3
  - **Effort:** M
  - **Dependencies:** 6.1.2, 4.2.2

- [ ] 7.1.2 Implement GET /api/officer/bids/{bid_id} endpoint (bid detail view)
  - **Acceptance Criteria:**
    - Returns comprehensive bid view: bidder_org, documents, compliance_results, risk_assessment, verification_results, clarifications, ai_recommendation
    - Queries: Bid, Organization, Document, ComplianceResult, RiskSignal, RiskAssessment, VerificationResult, ClarificationRequest
    - Returns: {bid_id, bidder_info, documents: [{...}], compliance: [...], risk: {...}, verification: {...}, clarifications: [...], ai_recommendation}
    - Officer role required
    - Includes all data needed for decision making
  - **File Path:** `backend/app/services/bid_service.py`
  - **Requirements:** 7.1
  - **Effort:** L
  - **Dependencies:** 2.3.1, 4.2.2, 5.4.1, 6.1.2

### 7.2 Clarification Workflow

- [ ] 7.2.1 Create Alembic migration for Clarification tables
  - **Acceptance Criteria:**
    - ClarificationRequest table: id (UUID PK), bid_id (FK), posted_by (FK to User), question_text (text), category, status (OPEN|RESOLVED|REOPENED), posted_at, deadline (optional)
    - ClarificationResponse table: id (UUID PK), request_id (FK), response_text (text), responded_by (FK to User), responded_at
    - Indexes: ClarificationRequest(bid_id), ClarificationRequest(status)
  - **File Path:** `backend/app/db/migrations/versions/0013_phase7_clarification_schema.py`
  - **Requirements:** 7.4
  - **Effort:** S
  - **Dependencies:** 2.1.1

- [ ] 7.2.2 Implement POST /api/officer/bids/{bid_id}/clarifications endpoint
  - **Acceptance Criteria:**
    - Officer posts clarification question to bidder
    - Request body: {question_text: string, category: string (string|document|compliance)}
    - Creates ClarificationRequest record with status = "OPEN"
    - Logs CLARIFICATION_POSTED audit event
    - Sends notification to bidder
    - Returns: {request_id, question_text, posted_at, status: "OPEN"}
  - **File Path:** `backend/app/services/clarification_service.py` (new)
  - **Requirements:** 7.4
  - **Effort:** M
  - **Dependencies:** 7.2.1

- [ ] 7.2.3 Implement POST /api/bidder/clarifications/{request_id}/respond endpoint
  - **Acceptance Criteria:**
    - Bidder responds to open clarification request
    - Request body: {response_text: string, attachments?: [file_ids]}
    - Creates ClarificationResponse record
    - Updates ClarificationRequest status = "RESOLVED"
    - Logs CLARIFICATION_RESPONDED audit event
    - Sends notification to officer
    - Returns: {response_id, response_text, responded_at}
  - **File Path:** `backend/app/services/clarification_service.py`
  - **Requirements:** 7.4
  - **Effort:** M
  - **Dependencies:** 7.2.2

- [ ] 7.2.4 Implement GET /api/officer/bids/{bid_id}/clarifications endpoint
  - **Acceptance Criteria:**
    - Returns all ClarificationRequest and ClarificationResponse records for bid
    - Sorted by posted_at DESC
    - Shows question, response, status, timestamps
    - Helps officer review bid discussion history
  - **File Path:** `backend/app/services/clarification_service.py`
  - **Requirements:** 7.4
  - **Effort:** S
  - **Dependencies:** 7.2.1

### 7.3 Officer Decision Making

- [ ] 7.3.1 Create Alembic migration for Decision tables
  - **Acceptance Criteria:**
    - OfficerDecision table: id (UUID PK), bid_id (FK, UNIQUE), final_decision (VERIFIED|NON_COMPLIANT|PENDING), ai_recommendation, decided_by (FK to User), decided_at, notes (optional)
    - OfficerDecisionOverride table: id (UUID PK), decision_id (FK), override_reason (text), requires_approval (bool), status (PENDING_APPROVAL|APPROVED|REJECTED), approved_by (FK), approved_at
    - Indexes: OfficerDecision(bid_id), OfficerDecision(decided_at)
  - **File Path:** `backend/app/db/migrations/versions/0013_phase7_decision_schema.py`
  - **Requirements:** 8.1, 8.2
  - **Effort:** S
  - **Dependencies:** 2.1.1

- [ ] 7.3.2 Implement POST /api/officer/bids/{bid_id}/decision endpoint (make decision)
  - **Acceptance Criteria:**
    - Officer makes final decision: VERIFIED or NON_COMPLIANT
    - Request body: {final_decision: VERIFIED|NON_COMPLIANT, override_reason?: string, notes?: string}
    - If final_decision != ai_recommendation AND final_decision is HIGH_RISK override, requires override_reason
    - Creates OfficerDecision record
    - If override, creates OfficerDecisionOverride record
    - IF risk = HIGH AND override, sets requires_approval = true
    - Updates Bid status = "DECIDED", current_state = "DECIDED"
    - Logs BID_DECIDED audit event
    - Returns: {decision_id, final_decision, decided_at, override_status}
  - **File Path:** `backend/app/services/officer_decision_service.py` (new)
  - **Requirements:** 8.1, 8.2
  - **Effort:** M
  - **Dependencies:** 7.3.1, 7.1.1

- [ ] 7.3.3 Implement decision override approval workflow
  - **Acceptance Criteria:**
    - HIGH_RISK overrides require approval from higher authority (e.g., director, regional officer)
    - OfficerDecisionOverride status: PENDING_APPROVAL (waiting) → APPROVED or REJECTED
    - Approval endpoint: POST /api/officer/decisions/{decision_id}/approve or /reject
    - Only approved_role can approve (configurable)
    - Logs DECISION_APPROVED or DECISION_REJECTED audit event
  - **File Path:** `backend/app/services/officer_decision_service.py`
  - **Requirements:** 8.2
  - **Effort:** M
  - **Dependencies:** 7.3.2

### 7.4 Bid State Transition Management

- [ ] 7.4.1 Implement bid state transitions with validation
  - **Acceptance Criteria:**
    - DRAFT → EVAL_STAGE1 (document slots verified)
    - EVAL_STAGE1 → EVAL_STAGE2 (compliance evaluated)
    - EVAL_STAGE2 → SUBMITTED (bidder ready to submit, no more edits)
    - SUBMITTED → DECIDED (officer made final decision)
    - Prevent skipping stages
    - Each transition logs BidState record with exited_at, entered_at
    - state_metadata stores stage-specific context
  - **File Path:** `backend/app/services/state_machine.py` (enhance)
  - **Requirements:** 10.2
  - **Effort:** M
  - **Dependencies:** 2.3.3

- [ ] 7.4.2 Implement bid submission endpoint (transition to SUBMITTED)
  - **Acceptance Criteria:**
    - POST /api/bidder/bids/{bid_id}/submit
    - Requires EVAL_STAGE2 state
    - Validates compliance = "COMPLIANT"
    - Validates all required documents uploaded and OCR completed
    - Transitions to SUBMITTED state
    - Sets submitted_at = current_timestamp
    - Logs BID_SUBMITTED audit event
    - Notifies officer of new bid submission
    - Returns: {bid_id, status: "SUBMITTED", submitted_at}
  - **File Path:** `backend/app/services/bid_service.py`
  - **Requirements:** 10.2
  - **Effort:** M
  - **Dependencies:** 7.4.1

- [ ] 7.5 Checkpoint - Officer Decision Support
  - Test GET /api/officer/bids/{bid_id} (comprehensive bid view)
  - Test AI recommendation generation
  - Test clarification workflow (post → respond)
  - Test POST /api/officer/bids/{bid_id}/decision (make decision)
  - Test decision override approval
  - Verify state transitions and bid state history
  - Test bid submission endpoint
  - Ensure all tests pass
  - Ask the user if questions arise.

---

## Phase 8: Final Approval Workflow (6 tasks)

### 8.1 Multi-Level Approval

- [ ] 8.1.1 Create Alembic migration for Approval workflow
  - **Acceptance Criteria:**
    - ApprovalLevel table: id (integer), level_name (string), role (string), description, required (bool), sequence (int)
    - ApprovalRecord table: id (UUID PK), decision_id (FK), approval_level (FK), approver_id (FK to User), approval_status (PENDING|APPROVED|REJECTED), approved_at, notes, sequence_num
    - Indexes: ApprovalRecord(decision_id), ApprovalRecord(approval_status)
  - **File Path:** `backend/app/db/migrations/versions/0014_phase8_approval_schema.py`
  - **Requirements:** 8.2
  - **Effort:** M
  - **Dependencies:** 7.3.1

- [ ] 8.1.2 Implement approval workflow orchestration
  - **Acceptance Criteria:**
    - ApprovalOrchestrator service manages multi-level approvals
    - Workflow: OfficerDecision → OfficerReview (optional) → DepartmentHeadReview (if HIGH_RISK) → Final
    - Each level must approve before next level
    - Parallel approvals not allowed (sequential)
    - Skip optional levels if not applicable
    - Notifies next approver via email/in-app notification
  - **File Path:** `backend/app/services/approval_orchestrator.py` (new)
  - **Requirements:** 8.2
  - **Effort:** L
  - **Dependencies:** 8.1.1

- [ ] 8.1.3 Implement approval endpoints
  - **Acceptance Criteria:**
    - GET /api/officer/approvals/pending (list pending approvals for user)
    - POST /api/officer/approvals/{approval_id}/approve (approve)
    - POST /api/officer/approvals/{approval_id}/reject (reject with reason)
    - Returns pending approvals grouped by decision type (HIGH_RISK, override, etc.)
    - Approver role required
  - **File Path:** `backend/app/services/approval_orchestrator.py`
  - **Requirements:** 8.2
  - **Effort:** M
  - **Dependencies:** 8.1.2

### 8.2 Notification & Communication

- [ ] 8.2.1 Implement notification service (email + in-app)
  - **Acceptance Criteria:**
    - Notification table: id (UUID PK), user_id (FK), notification_type, message_template, context_data (JSON), created_at, sent_at, read_at
    - Sends on: bid events (submitted, verified, rejected), clarifications (new, answered), approvals (pending, approved, rejected)
    - Email via SMTP (configurable)
    - In-app via Notification table (polling/websocket ready)
    - Template system: {user_name}, {bid_id}, {action}, {reason}
    - Returns immediately, queued for async delivery
  - **File Path:** `backend/app/services/notification_service.py` (new)
  - **Requirements:** 9.2
  - **Effort:** M
  - **Dependencies:** None

- [ ] 8.2.2 Implement notification endpoints
  - **Acceptance Criteria:**
    - GET /api/user/notifications (list unread notifications)
    - POST /api/user/notifications/{notification_id}/read (mark read)
    - Real-time updates via WebSocket (future enhancement)
    - Notifications paginated, sorted by created_at DESC
  - **File Path:** `backend/app/services/notification_service.py`
  - **Requirements:** 9.2
  - **Effort:** M
  - **Dependencies:** 8.2.1

### 8.3 Final Decision Communication

- [ ] 8.3.1 Implement final decision notification to bidder
  - **Acceptance Criteria:**
    - When bid enters DECIDED state with final_decision = VERIFIED → email "Congratulations, bid verified"
    - When bid enters DECIDED state with final_decision = NON_COMPLIANT → email "Bid rejected, reasons: ..." + detailed violation list
    - Email includes: bid_id, tender_title, decision reason, next steps
    - Sends to bidder organization email and primary contact
    - In-app notification also created
  - **File Path:** `backend/app/services/notification_service.py`
  - **Requirements:** 9.2, 9.3
  - **Effort:** M
  - **Dependencies:** 8.2.1

- [ ] 8.4 Checkpoint - Approval Workflow
  - Test approval workflow for HIGH_RISK decisions
  - Test approval endpoints (pending, approve, reject)
  - Verify notification generation and delivery
  - Test final decision communication to bidder
  - Verify state transitions to DECIDED
  - Ensure all tests pass
  - Ask the user if questions arise.

---

## Phase 9: Bidder Feedback & Remediation (8 tasks)

### 9.1 Violation Feedback to Bidders

- [ ] 9.1.1 Implement detailed violation report generation
  - **Acceptance Criteria:**
    - When bid NON_COMPLIANT, generate ViolationReport (or store in decision notes)
    - Report includes: each failed compliance rule, evidence, explanation in plain language
    - For each violation: "GSTIN not found in active registry. Please verify GSTIN number in documents."
    - Includes: required actions to remediate, document references
    - Stored for bidder access via API
  - **File Path:** `backend/app/services/violation_report_service.py` (new)
  - **Requirements:** 9.1
  - **Effort:** M
  - **Dependencies:** 4.2.2, 7.3.2

- [ ] 9.1.2 Implement GET /api/bidder/bids/{bid_id}/decision endpoint
  - **Acceptance Criteria:**
    - Bidder views final decision on their bid
    - Fields: final_decision, decided_at, decision_explanation, violations: [{rule, reason, evidence, remediation_steps}], next_steps
    - Requires bidder role and bid ownership
    - Returns HTTP 404 if bid not in DECIDED state
  - **File Path:** `backend/app/services/bid_service.py`
  - **Requirements:** 9.1, 9.3
  - **Effort:** M
  - **Dependencies:** 9.1.1

- [ ] 9.1.3 Implement remediation guidance
  - **Acceptance Criteria:**
    - For each violation, provide guidance: "To resolve: Update your GST certificate if information is outdated, or contact GST authorities to update records"
    - Guidance database or hardcoded rules: {violation_type → remediation_steps (array of strings)}
    - Bidders can re-apply after fixing documented violations
  - **File Path:** `backend/app/services/violation_report_service.py`
  - **Requirements:** 9.1
  - **Effort:** S
  - **Dependencies:** 9.1.1

### 9.2 Re-submission and Status Tracking

- [ ] 9.2.1 Implement bid re-submission support (Phase 2 enhancement)
  - **Acceptance Criteria:**
    - After NON_COMPLIANT decision, bidder can re-submit for same tender (new DRAFT bid allowed for same bidder)
    - Previous bid remains in audit trail (not deleted)
    - New bid linked to same tender but separate bid record
    - Bidder can upload corrected documents
    - Goes through same verification flow
  - **File Path:** `backend/app/services/bid_service.py`
  - **Requirements:** 2.3
  - **Effort:** S
  - **Dependencies:** 2.3.1

- [ ] 9.2.2 Implement GET /api/bidder/bids/{bid_id}/status-history endpoint
  - **Acceptance Criteria:**
    - Returns all state transitions for a bid
    - Fields: state, entered_at, exited_at, reason (from state_metadata)
    - Shows: when moved to EVAL_STAGE1, when moved to EVAL_STAGE2, when submitted, when decided
    - Helps bidder understand bid progression
  - **File Path:** `backend/app/services/bid_service.py`
  - **Requirements:** 10.2
  - **Effort:** S
  - **Dependencies:** 7.4.1

### 9.3 Appeal/Review Request (Optional for Phase 9)

- [ ] 9.3.1 Implement appeal mechanism (optional)
  - **Acceptance Criteria:**
    - NON_COMPLIANT bidders can request review of decision
    - Request includes: appeal_reason, supporting_documents
    - Creates AppealRequest record with status = "SUBMITTED"
    - Assigned to appeals officer for re-evaluation
    - Optional for MVP, can be deferred
  - **File Path:** `backend/app/services/appeal_service.py` (new, optional)
  - **Requirements:** 9.1
  - **Effort:** M
  - **Dependencies:** 7.3.2

- [ ] 9.4 Checkpoint - Bidder Feedback
  - Test violation report generation for NON_COMPLIANT bids
  - Test GET /api/bidder/bids/{bid_id}/decision endpoint
  - Verify remediation guidance provided
  - Test bid re-submission after fix
  - Test status history tracking
  - Ensure all tests pass
  - Ask the user if questions arise.

---

## Phase 10: Audit Trail & System Integration (9 tasks)

### 10.1 Immutable Audit Logging

- [ ] 10.1.1 Create Alembic migration for Audit tables
  - **Acceptance Criteria:**
    - AuditEvent table: id (UUID PK), event_type (string), actor_id (FK), actor_role (string), entity_type (string), entity_id (UUID), details (JSON), timestamp (datetime, indexed), ip_address (string)
    - Events: USER_REGISTERED, BID_CREATED, BID_SUBMITTED, COMPLIANCE_EVALUATED, RISK_ASSESSED, DECISION_MADE, APPROVAL_APPROVED, APPROVAL_REJECTED, CLARIFICATION_POSTED, CLARIFICATION_RESPONDED
    - Immutable: no updates or deletes after creation
    - Indexed by: timestamp, event_type, entity_id, actor_id
  - **File Path:** `backend/app/db/migrations/versions/0015_phase10_audit_schema.py`
  - **Requirements:** 10.1
  - **Effort:** S
  - **Dependencies:** 2.1.1

- [ ] 10.1.2 Implement audit service for event logging
  - **Acceptance Criteria:**
    - AuditService.log(event_type, actor_id, entity_type, entity_id, details, ip_address)
    - Called on all user actions and system decisions
    - Captures: before/after state changes (in details JSON)
    - Includes: user action, system action, external API calls
    - Guaranteed write to database (no async, no loss)
    - Returns audit_id for traceability
  - **File Path:** `backend/app/services/audit_service.py` (enhance)
  - **Requirements:** 10.1
  - **Effort:** M
  - **Dependencies:** 10.1.1

- [ ] 10.1.3 Implement GET /api/officer/audit-log endpoint
  - **Acceptance Criteria:**
    - Returns audit events filtered by: entity_id, event_type, actor_id, date_range
    - Fields: timestamp, event_type, actor_role, details, changes
    - Pagination: limit, offset
    - Officer role required
    - Helps with compliance audits and investigations
  - **File Path:** `backend/app/services/audit_service.py`
  - **Requirements:** 10.1
  - **Effort:** S
  - **Dependencies:** 10.1.2

### 10.2 State History Tracking

- [ ] 10.2.1 Implement comprehensive state history for all entities
  - **Acceptance Criteria:**
    - BidState table populated on every state transition
    - Tracks: bid_id, state_exited, state_entered, exited_at, entered_at, metadata (reason, triggered_by)
    - Allows full replay of bid lifecycle
    - GET /api/officer/bids/{bid_id}/state-history returns all transitions
    - Immutable: no updates to history records
  - **File Path:** `backend/app/services/state_machine.py`
  - **Requirements:** 10.2
  - **Effort:** M
  - **Dependencies:** 7.4.1, 10.1.1

- [ ] 10.2.2 Implement version tracking for tender and document changes
  - **Acceptance Criteria:**
    - TenderVersion records store immutable snapshots (already done in Phase 2)
    - DocumentVersion records store immutable snapshots (already done in Phase 3)
    - Trace changes via version_number and created_at
    - Allows comparison of versions: GET /api/officer/tenders/{tender_id}/versions/diff?v1=1.0&v2=2.0
  - **File Path:** `backend/app/services/tender_service.py`, `backend/app/services/document_service.py`
  - **Requirements:** 10.2
  - **Effort:** M
  - **Dependencies:** 2.1.1, 3.2.1

### 10.3 Compliance and Audit Reports

- [ ] 10.3.1 Implement GET /api/officer/reports/bid-evaluation-audit endpoint
  - **Acceptance Criteria:**
    - Returns audit report for single bid: all events, state transitions, decisions
    - Timeline view: [timestamp, event, actor, details]
    - Includes: created → verified → submitted → evaluated → decided
    - For forensics/compliance investigations
    - Export as PDF or JSON
  - **File Path:** `backend/app/services/report_service.py` (new)
  - **Requirements:** 10.1
  - **Effort:** M
  - **Dependencies:** 10.1.2, 10.2.1

- [ ] 10.3.2 Implement GET /api/officer/reports/tender-summary endpoint
  - **Acceptance Criteria:**
    - Returns summary report for tender: total bids, by status, by risk level, compliance stats
    - Fields: tender_id, tender_title, total_bids, VERIFIED (count), NON_COMPLIANT (count), PENDING (count), avg_risk_score, high_risk_count
    - Filters: date_range, organization
    - Used for procurement planning and metrics
  - **File Path:** `backend/app/services/report_service.py`
  - **Requirements:** 10.1
  - **Effort:** M
  - **Dependencies:** 6.1.2

### 10.4 System Integration and Deployment

- [ ] 10.4.1 Implement environment configuration and secrets management
  - **Acceptance Criteria:**
    - Configuration via .env file with defaults in config.py
    - Environment variables: DATABASE_URL, REDIS_URL, SECRET_KEY, EMAIL_HOST, UPLOAD_DIR, LOG_LEVEL
    - Secrets NOT logged or exposed in error messages
    - Configuration validated on startup (fail if required values missing)
    - Support for development, staging, production configs
  - **File Path:** `backend/app/config.py`, `.env.example`, `backend/app/main.py` (startup)
  - **Requirements:** General
  - **Effort:** S
  - **Dependencies:** None

- [ ] 10.4.2 Implement health check and readiness endpoints
  - **Acceptance Criteria:**
    - GET /health (basic health check)
    - GET /ready (readiness check: database connected, Redis connected, migrations applied)
    - Returns: {status: "healthy"|"unhealthy", checks: {database, redis, ocr_worker}}
    - Used for Kubernetes liveness/readiness probes
  - **File Path:** `backend/app/main.py`
  - **Requirements:** General
  - **Effort:** S
  - **Dependencies:** None

- [ ] 10.4.3 Implement structured logging and monitoring
  - **Acceptance Criteria:**
    - JSON structured logging (loguru or python-json-logger)
    - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
    - Logs include: timestamp, level, logger_name, message, exception (if error), request_id
    - Request ID propagated through logs for traceability
    - Log files rotated daily, kept for 30 days
    - Centralized logging (optional: ELK or CloudWatch)
  - **File Path:** `backend/app/logger.py` (new), `backend/app/main.py`
  - **Requirements:** General
  - **Effort:** M
  - **Dependencies:** None

- [ ] 10.5 Checkpoint - Audit & System Integration
  - Test audit event logging for all operations
  - Verify GET /api/officer/audit-log endpoint
  - Test state history tracking
  - Test health and readiness endpoints
  - Verify structured logging
  - Test environment configuration
  - Generate sample audit reports
  - Ensure all tests pass
  - Ask the user if questions arise.

---

## Frontend Implementation Tasks (20 tasks)

### Frontend 1: Authentication UI

- [ ]* F.1.1 Implement login page component
  - **Acceptance Criteria:**
    - React component: LoginPage.tsx
    - Form fields: email, password
    - Submit to POST /api/auth/login
    - Error display on failed login
    - Redirect to dashboard on success
    - Store JWT token in localStorage
  - **File Path:** `frontend/src/pages/LoginPage.tsx`
  - **Requirements:** 1.1
  - **Effort:** M
  - **Dependencies:** Backend 1.2.2

- [ ]* F.1.2 Implement registration page component
  - **Acceptance Criteria:**
    - React component: RegisterPage.tsx
    - Form fields: email, password, password_confirm, role (officer|bidder), organization_id (if bidder)
    - Validation: email format, password strength, password match
    - Submit to POST /api/auth/register
    - Redirect to login on success
  - **File Path:** `frontend/src/pages/RegisterPage.tsx`
  - **Requirements:** 1.1
  - **Effort:** M
  - **Dependencies:** Backend 1.2.1

- [ ]* F.1.3 Implement JWT token management and axios interceptor
  - **Acceptance Criteria:**
    - ApiClient configured with axios
    - Interceptor adds Authorization header on all requests
    - Interceptor handles 401 errors (refresh or logout)
    - Token refresh logic (if applicable)
    - Persist token across page reloads
  - **File Path:** `frontend/src/api/client.ts`, `frontend/src/utils/auth.ts`
  - **Requirements:** 1.1
  - **Effort:** S
  - **Dependencies:** Backend 1.2.2

### Frontend 2: Officer Dashboard

- [ ]* F.2.1 Implement officer dashboard layout
  - **Acceptance Criteria:**
    - React component: OfficerDashboard.tsx
    - Layout: sidebar (nav), top bar (user info, logout), main content area
    - Navigation: Create Tender, View Tenders, Pending Bids, Risk Dashboard, Audit Log
    - Responsive design (mobile, tablet, desktop)
  - **File Path:** `frontend/src/pages/OfficerDashboard.tsx`, `frontend/src/components/OfficerLayout.tsx`
  - **Requirements:** 2.1, 7.1
  - **Effort:** L
  - **Dependencies:** Backend 1.1

- [ ]* F.2.2 Implement tender creation form
  - **Acceptance Criteria:**
    - React component: TenderCreateForm.tsx
    - Form fields: title, required_documents (multi-select), submission_deadline (date picker), evaluation_criteria (rich text)
    - Submit to POST /api/officer/tenders
    - Show success message and redirect to tender detail
  - **File Path:** `frontend/src/components/TenderCreateForm.tsx`
  - **Requirements:** 2.1, 2.4
  - **Effort:** M
  - **Dependencies:** Backend 2.1.2

- [ ]* F.2.3 Implement tender list and publish workflow
  - **Acceptance Criteria:**
    - React component: TenderListPage.tsx
    - Lists officer's tenders with status (draft, published, closed)
    - Action buttons: View, Publish, Close, Edit (draft only)
    - Publish button calls POST /api/officer/tenders/{id}/publish
    - Shows confirmation before publish
  - **File Path:** `frontend/src/pages/TenderListPage.tsx`, `frontend/src/components/TenderCard.tsx`
  - **Requirements:** 2.1
  - **Effort:** M
  - **Dependencies:** Backend 2.1.4

- [ ]* F.2.4 Implement pending bids queue and risk dashboard
  - **Acceptance Criteria:**
    - React component: PendingBidsPage.tsx
    - Displays all submitted bids for officer's tenders
    - Sortable columns: bid_id, bidder_name, submitted_at, compliance_status, risk_level, ai_recommendation
    - Risk level color-coded: LOW (green), MEDIUM (yellow), HIGH (red)
    - Click on bid → detail view
    - Filter by risk level, compliance status
  - **File Path:** `frontend/src/pages/PendingBidsPage.tsx`, `frontend/src/components/BidListTable.tsx`
  - **Requirements:** 7.1
  - **Effort:** L
  - **Dependencies:** Backend 7.1.2

### Frontend 3: Bid Evaluation UI

- [ ]* F.3.1 Implement comprehensive bid detail view
  - **Acceptance Criteria:**
    - React component: BidDetailPage.tsx
    - Tabs: Summary, Documents, Compliance, Risk, Verification, Clarifications
    - Summary tab: bidder org info, submission timeline, status badges
    - Documents tab: list with OCR status, download links
    - Compliance tab: table of rules with pass/fail, evidence links
    - Risk tab: risk score visualization, signal breakdown
    - Verification tab: source verification results
    - Clarifications tab: Q&A interface
  - **File Path:** `frontend/src/pages/BidDetailPage.tsx`, `frontend/src/components/BidDetail/*.tsx`
  - **Requirements:** 7.1
  - **Effort:** L
  - **Dependencies:** Backend 7.1.2

- [ ]* F.3.2 Implement clarification Q&A interface
  - **Acceptance Criteria:**
    - React component: ClarificationPanel.tsx
    - Officer can post question via modal form
    - Display Q&A thread with timestamps
    - Show response status (OPEN, RESOLVED)
    - Allow officer to re-open if needed
    - Real-time updates or polling
  - **File Path:** `frontend/src/components/ClarificationPanel.tsx`
  - **Requirements:** 7.4, 7.2
  - **Effort:** M
  - **Dependencies:** Backend 7.2.2, 7.2.3

- [ ]* F.3.3 Implement decision-making interface
  - **Acceptance Criteria:**
    - React component: DecisionMaker.tsx
    - Shows AI recommendation prominently
    - Officer selects final decision: VERIFIED or NON_COMPLIANT
    - If override, requires override_reason
    - Shows risk assessment and implications
    - Submit button with confirmation
    - Displays decision confirmation with audit trail
  - **File Path:** `frontend/src/components/DecisionMaker.tsx`
  - **Requirements:** 7.3, 8.1
  - **Effort:** M
  - **Dependencies:** Backend 7.3.2

### Frontend 4: Bidder Portal

- [ ]* F.4.1 Implement bidder dashboard layout
  - **Acceptance Criteria:**
    - React component: BidderDashboard.tsx
    - Layout: sidebar (nav), top bar (user info, logout), main content
    - Navigation: Browse Tenders, My Bids, My Organization, Profile
    - Show bidder organization info
  - **File Path:** `frontend/src/pages/BidderDashboard.tsx`, `frontend/src/components/BidderLayout.tsx`
  - **Requirements:** 2.2, 2.3
  - **Effort:** L
  - **Dependencies:** Backend 1.1

- [ ]* F.4.2 Implement tender browsing interface
  - **Acceptance Criteria:**
    - React component: TenderBrowsePage.tsx
    - Display published tenders in grid or list
    - Cards show: title, organization, required docs, submitted count, deadline
    - Search and filter by keyword, organization, sector
    - Click to view tender details and submit bid
  - **File Path:** `frontend/src/pages/TenderBrowsePage.tsx`, `frontend/src/components/TenderCard.tsx`
  - **Requirements:** 2.2
  - **Effort:** M
  - **Dependencies:** Backend 2.2.1, 2.2.2

- [ ]* F.4.3 Implement bid submission workflow
  - **Acceptance Criteria:**
    - React component: BidSubmissionWizard.tsx
    - Step 1: Select tender
    - Step 2: Upload documents (drag-drop interface)
    - Step 3: Document verification (stage 1) - show checklist
    - Step 4: Compliance evaluation (stage 2) - show results
    - Step 5: Review and submit
    - Progress bar showing completion
    - Resume draft functionality
  - **File Path:** `frontend/src/components/BidSubmissionWizard.tsx`, `frontend/src/pages/BidSubmissionPage.tsx`
  - **Requirements:** 2.3, 3.1, 3.3, 4.2
  - **Effort:** L
  - **Dependencies:** Backend 2.3.1, 3.1.1, 3.3.1, 4.2.1

- [ ]* F.4.4 Implement bid tracking and decision view
  - **Acceptance Criteria:**
    - React component: MyBidsPage.tsx
    - List bidder's bids with status, risk level, submitted date
    - Click to view bid status and final decision
    - Show violation report if NON_COMPLIANT
    - Show remediation guidance
  - **File Path:** `frontend/src/pages/MyBidsPage.tsx`, `frontend/src/components/BidTrackingCard.tsx`
  - **Requirements:** 9.1, 9.3
  - **Effort:** M
  - **Dependencies:** Backend 9.1.2, 2.3.2

### Frontend 5: Shared Components

- [ ]* F.5.1 Implement state management (Zustand/Redux)
  - **Acceptance Criteria:**
    - Store structure: auth (user, token), bids (current bid, bid list), tenders (current tender, tender list), ui (modal state, loading)
    - Actions: login, logout, fetchBids, submitBid, etc.
    - Persist auth state across reloads
    - Centralized API error handling
  - **File Path:** `frontend/src/store/`, `frontend/src/hooks/useAuth.ts`, etc.
  - **Requirements:** General
  - **Effort:** M
  - **Dependencies:** F.1.1

- [ ]* F.5.2 Implement reusable UI components
  - **Acceptance Criteria:**
    - Button, Input, Select, Modal, Card, Table, Alert, Badge, Spinner
    - Consistent styling via Tailwind CSS or MUI
    - Props for customization (size, color, state)
    - Accessibility: ARIA labels, keyboard navigation
  - **File Path:** `frontend/src/components/UI/*.tsx`
  - **Requirements:** General
  - **Effort:** M
  - **Dependencies:** None

- [ ]* F.5.3 Implement data visualization components
  - **Acceptance Criteria:**
    - RiskScore gauge (0-100 score with color zones)
    - ComplianceChart (pass/fail rule breakdown)
    - TimelineComponent (state history visualization)
    - Use recharts or similar library
  - **File Path:** `frontend/src/components/Visualizations/*.tsx`
  - **Requirements:** 6.1, 7.1, 10.2
  - **Effort:** M
  - **Dependencies:** Backend 6.1.1, 7.1.2

---

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": [
        "1.1.1",
        "1.3.1",
        "1.3.2",
        "10.4.1"
      ]
    },
    {
      "id": 1,
      "tasks": [
        "1.1.2",
        "1.2.1",
        "2.1.1",
        "3.4.1",
        "4.1.1",
        "5.1.1",
        "6.1.1",
        "8.1.1",
        "10.1.1"
      ]
    },
    {
      "id": 2,
      "tasks": [
        "1.2.2",
        "1.2.3",
        "1.4.1",
        "2.1.2",
        "2.4.1",
        "2.4.2",
        "3.4.4"
      ]
    },
    {
      "id": 3,
      "tasks": [
        "1.2.4",
        "1.4.2",
        "1.5.1",
        "2.1.3",
        "2.1.4",
        "2.2.1",
        "3.1.1",
        "3.1.2",
        "4.1.2",
        "5.1.3"
      ]
    },
    {
      "id": 4,
      "tasks": [
        "1.6",
        "2.2.2",
        "2.3.1",
        "3.1.3",
        "3.2.1",
        "3.4.2",
        "4.1.3",
        "5.2.1"
      ]
    },
    {
      "id": 5,
      "tasks": [
        "2.3.2",
        "2.3.3",
        "3.2.2",
        "3.2.3",
        "3.3.1",
        "4.2.1",
        "5.1.2",
        "5.2.2",
        "5.3.1"
      ]
    },
    {
      "id": 6,
      "tasks": [
        "2.3.4",
        "2.5",
        "3.3.2",
        "3.4.3",
        "4.2.2",
        "5.2.3",
        "5.3.2",
        "6.1.2",
        "6.2.1"
      ]
    },
    {
      "id": 7,
      "tasks": [
        "3.4.5",
        "3.5",
        "4.2.3",
        "4.3.1",
        "5.3.3",
        "5.4.1",
        "6.1.3",
        "6.2.2"
      ]
    },
    {
      "id": 8,
      "tasks": [
        "4.2.4",
        "4.3.2",
        "4.3.3",
        "4.4.1",
        "5.4.2",
        "5.4.3",
        "6.2.3",
        "6.3.1"
      ]
    },
    {
      "id": 9,
      "tasks": [
        "4.4.2",
        "4.5",
        "6.3.2",
        "6.3.3",
        "7.1.1",
        "7.1.2",
        "7.2.1",
        "5.5"
      ]
    },
    {
      "id": 10,
      "tasks": [
        "7.2.2",
        "7.2.3",
        "7.2.4",
        "7.3.1",
        "7.3.2",
        "8.1.1",
        "8.2.1"
      ]
    },
    {
      "id": 11,
      "tasks": [
        "7.3.3",
        "7.4.1",
        "7.4.2",
        "8.1.2",
        "8.2.2",
        "8.2.3",
        "9.1.1"
      ]
    },
    {
      "id": 12,
      "tasks": [
        "7.5",
        "8.1.3",
        "8.3.1",
        "9.1.2",
        "9.1.3",
        "10.1.2"
      ]
    },
    {
      "id": 13,
      "tasks": [
        "8.4",
        "9.2.1",
        "9.2.2",
        "9.3.1",
        "10.1.3",
        "10.2.1",
        "10.2.2"
      ]
    },
    {
      "id": 14,
      "tasks": [
        "9.4",
        "10.3.1",
        "10.3.2",
        "10.4.2",
        "10.4.3"
      ]
    },
    {
      "id": 15,
      "tasks": [
        "10.5"
      ]
    },
    {
      "id": 16,
      "tasks": [
        "F.1.1",
        "F.1.2",
        "F.1.3",
        "F.5.1",
        "F.5.2"
      ]
    },
    {
      "id": 17,
      "tasks": [
        "F.2.1",
        "F.2.2",
        "F.4.1",
        "F.4.2",
        "F.5.3"
      ]
    },
    {
      "id": 18,
      "tasks": [
        "F.2.3",
        "F.2.4",
        "F.3.1",
        "F.3.2",
        "F.3.3",
        "F.4.3",
        "F.4.4"
      ]
    }
  ]
}
```

---

## Notes

- All tasks require unit tests with minimum 80% code coverage (marked with `*` postfix are optional)
- Database migrations must be idempotent and reversible (alembic downgrade support)
- API endpoints follow RESTful conventions with consistent response formats (Requirement 1.4)
- Authentication required for all sensitive endpoints; public endpoints marked explicitly
- External API calls implement retry logic with exponential backoff (Requirement 5.1)
- All user actions logged to AuditEvent table for forensics (Requirement 10.1)
- State transitions use state machine pattern with validation (Requirement 10.2)
- Risk scoring weights configurable without code changes (Requirement 6.2)
- Evidence traceability maintained for all compliance decisions (Requirement 4.3)
- Frontend components use TypeScript for type safety and accessibility (WCAG)
- Dependencies indicate prerequisite tasks; parallel execution allowed for same wave

---

## Execution Guidelines

1. **Sequential Phases:** Complete phases 1-10 in order for maximum integration
2. **Parallel Tasks:** Tasks in same wave can execute in parallel (no dependencies)
3. **Testing:** Run unit tests after completing each phase checkpoint
4. **Integration:** After each checkpoint, verify cross-component interactions
5. **Code Review:** Each task should be reviewed before marking complete
6. **Documentation:** Update API docs on new endpoints, internal docs on design changes
7. **Performance:** Profile database queries and API response times at each checkpoint
8. **Security:** Validate authentication, authorization, and input validation at each phase

