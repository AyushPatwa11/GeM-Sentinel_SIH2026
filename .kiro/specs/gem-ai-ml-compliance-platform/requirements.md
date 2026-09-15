# Requirements Document
## GeM AI/ML Based Bidder Compliance Verification Platform

**Feature Name:** gem-ai-ml-compliance-platform  
**Document Type:** Complete 10-Phase System Specification  
**Project:** SIH 2026 | PS #26100 | Ministry of Petroleum & Natural Gas  
**Last Updated:** 2026-09-12  

---

## Introduction

The GeM AI/ML Based Bidder Compliance Verification Platform is a comprehensive solution designed to automate and streamline the procurement compliance verification process across Government e-Marketplace (GeM) tenders. The platform spans 10 integrated phases that collectively enable government officers to efficiently verify bidder compliance, detect fraudulent entities, assess risk profiles, and make informed procurement decisions.

This system serves two primary user roles:
- **Government Officers:** Create tenders, review bids, evaluate compliance, manage verifications, and make final decisions
- **Bidders (Organizations):** Discover tenders, submit bids, upload supporting documents, track compliance status, and receive feedback

The platform integrates with multiple government data sources (DataGovIn, GSTIN registry, MCA portal, NSIC database, Udyam registry) to verify bidder credentials and detect anomalies. Machine learning models assess risk profiles based on compliance violations, entity matching failures, and document anomalies.

---

## Glossary

### Core Entities

- **Government Officer:** User with "officer" role; authorized to create tenders, evaluate bids, manage verifications, and make final decisions
- **Bidder (Organization):** Entity registered on GeM; submits bids for government tenders through authorized representatives
- **Tender:** Government procurement document published by an officer specifying requirements, clauses, evaluation criteria, and submission deadlines
- **Tender Version:** Immutable snapshot of a tender at a point in time; supports version tracking and clause diffs
- **Bid:** Bidder's response to a tender; contains bidder entity metadata, uploaded documents, compliance status, and decision record
- **Clause:** Individual requirement or condition within a tender; evaluated against bidder documents and data
- **Compliance Rule:** Deterministic logic that evaluates a clause or bidder attribute against evidence; produces pass/fail result
- **Compliance Result:** Output of a compliance rule evaluation; includes result, evidence references, and violation explanation
- **Document:** File uploaded by bidder (GST certificate, PAN, COI, etc.); immutably versioned and OCR-processed
- **Document Version:** Immutable snapshot of a document; includes file hash, OCR output, and extraction metadata

### Verification Entities

- **Verification Source:** External data source (DataGovIn, GSTIN, MCA, NSIC, Udyam); provides authoritative data for bidder verification
- **Verification Result:** Output from querying an external source; includes verified data, mismatches, and confidence scores
- **Verification Attempt:** Record of a verification query; tracks source, timestamp, result, and retry logic
- **Entity Resolution:** Process of matching extracted bidder name from documents against authoritative registries; produces match confidence scores
- **Name Match Result:** Output of entity resolution; includes matched entities, confidence, and disambiguation data

### Risk & Decision Entities

- **Risk Signal:** Single anomaly detected during bid evaluation (e.g., name mismatch, GSTIN/PAN mismatch, duplicate bidder, blacklist hit)
- **Risk Assessment:** Aggregated risk profile for a bid; includes individual signals, total risk score, and derived risk level (LOW/MEDIUM/HIGH)
- **Risk Signal Decomposition:** Breakdown of why a specific risk signal was generated; includes contributing factors and evidence
- **Officer Decision:** Final procurement decision made by a government officer; includes decision code (VERIFIED/NON_COMPLIANT/PENDING), override reason if applicable, and timestamp
- **Officer Decision Override:** Record that an officer overrode AI recommendation; includes original recommendation, override reason, and approval timestamp

### State & Process Entities

- **Bid State:** Current state of a bid in its lifecycle (DRAFT/EVAL_STAGE1/EVAL_STAGE2/SUBMITTED/DECIDED); immutably tracked with state_entered_at and metadata
- **BidState:** Database model tracking state transitions; includes bid_id, current_state, state_entered_at, and state_metadata (JSON)
- **Audit Event:** Immutable log entry recording all system actions (CREATED, SUBMITTED, EVALUATED, VERIFIED_SOURCE, DECIDED); includes actor, timestamp, action details
- **Clarification Request:** Question posed by an officer to a bidder during evaluation; includes bid reference and question text
- **Clarification Response:** Bidder's answer to a clarification request; includes response text and document attachments
- **Notification:** Message sent to bidder (email or in-app) informing of status changes, clarifications, or decisions

### System Components

- **Compliance Orchestrator:** Service coordinating compliance evaluation; chains multiple compliance rules
- **Adapter Orchestrator:** Service coordinating external data source queries; manages parallel verification requests
- **OCR Processor:** Batch processing system for document text extraction; includes quality scoring
- **Risk Scoring Engine:** ML model evaluating risk signals and computing risk scores
- **State Machine:** Service managing bid lifecycle transitions with validation and side effects
- **Audit Service:** Immutable logging of all system actions
- **Evidence Traceability:** Service mapping compliance violations back to source documents and data
- **Notification Service:** Sends messages to users via email and in-app system

### Data Flows

- **Submission Pipeline:** Bidder uploads docs → OCR processing → Compliance evaluation → Risk assessment → Officer queues
- **Verification Pipeline:** Extract bidder data → Query multiple sources in parallel → Aggregate results → Generate verification report
- **Decision Pipeline:** Officer reviews bid → Views AI assessment → Makes decision → Audit logged → Bidder notified

---

## Requirements by Phase

---

## PHASE 1: FOUNDATION & AUTHENTICATION

### Requirement 1.1: User Registration and Role Management

**User Story:** As a government officer, I want to securely create an account and authenticate with my official credentials, so that I can access the procurement system and manage tenders.

#### Acceptance Criteria

1. THE System SHALL support two user roles: "officer" (government) and "bidder" (organization representative)
2. WHEN a new user registers with valid email and password, THE System SHALL create a User record with Argon2-hashed password
3. WHEN a user logs in with correct credentials, THE System SHALL return a JWT access token valid for 3600 seconds
4. WHEN a user logs in with incorrect credentials, THE System SHALL reject the login and return HTTP 401
5. THE System SHALL store user role, email, and organization_id in User table for RBAC enforcement
6. WHEN an officer accesses `/api/officer/*` endpoints, THE System SHALL verify role == "officer" and reject with HTTP 403 if insufficient permission
7. WHEN a bidder accesses `/api/bidder/*` endpoints, THE System SHALL verify role == "bidder" and reject with HTTP 403 if insufficient permission
8. THE System SHALL include JWT token in Authorization header as "Bearer <token>" for all authenticated API requests
9. WHEN an authentication token expires, THE System SHALL return HTTP 401 and require re-login

### Requirement 1.2: Bidder Organization Association

**User Story:** As a bidder, I want my account linked to my organization's GeM registration, so that my bids are automatically associated with my company.

#### Acceptance Criteria

1. WHEN a bidder user is created, THE System SHALL require organization_id to be linked from Organization table
2. WHEN fetching bidder profile, THE System SHALL return organization metadata including legal_name, gstin, pan, udyam_number, address, sector, turnover
3. THE System SHALL prevent a bidder from creating or modifying bids for organizations other than their linked organization
4. WHEN an organization is retrieved, THE System SHALL include all legally registered business attributes from initial registration

### Requirement 1.3: Database Schema Foundation

**User Story:** As a system administrator, I want the database schema to support all core entities and relationships, so that data integrity is maintained.

#### Acceptance Criteria

1. THE System SHALL create Organization table with columns: id (UUID PK), legal_name, gstin, pan, cin, udyam_number, sector, turnover, address, created_at, updated_at
2. THE System SHALL create User table with columns: id (UUID PK), email (UNIQUE), password_hash, role (officer|bidder), organization_id (FK to Organization), created_at, updated_at
3. THE System SHALL create Tender table with columns: id (UUID PK), title, status (draft|published|closed), created_by (FK to User), organization_id (FK to Organization), created_at, updated_at
4. THE System SHALL create TenderVersion table with columns: id (UUID PK), tender_id (FK to Tender), version_number, source_document_path, published_at, precedence_policy_version, created_at
5. THE System SHALL create Bid table with columns: id (UUID PK), tender_version_id (FK to TenderVersion), bidder_org_id (FK to Organization), status (draft|submitted|decided), current_state, state_entered_at, state_metadata (JSON), submitted_at, created_at, updated_at
6. THE System SHALL enforce foreign key constraints with CASCADE delete where appropriate
7. THE System SHALL create indexes on frequently queried columns: User(email), Tender(status), Bid(status, current_state), Organization(gstin, pan)

### Requirement 1.4: API Response Standardization

**User Story:** As a frontend developer, I want consistent API response formats and error codes, so that I can reliably parse responses and handle errors.

#### Acceptance Criteria

1. WHEN an API request succeeds, THE System SHALL return HTTP 200-201 with response body containing requested data
2. WHEN an API request fails validation, THE System SHALL return HTTP 400 with error response format: `{"detail": "error message"}`
3. WHEN an API request lacks authentication, THE System SHALL return HTTP 401 with error response format: `{"detail": "Unauthorized"}`
4. WHEN an API request lacks authorization, THE System SHALL return HTTP 403 with error response format: `{"detail": "Forbidden"}`
5. WHEN a requested resource does not exist, THE System SHALL return HTTP 404 with error response format: `{"detail": "Resource not found"}`
6. WHEN a server error occurs, THE System SHALL return HTTP 500 with error response format: `{"detail": "Internal server error"}`
7. ALL error messages SHALL be logged with context (endpoint, user_id, timestamp) for debugging

---

## PHASE 2: TENDER MANAGEMENT & BID CREATION

### Requirement 2.1: Officer Tender Creation and Publishing

**User Story:** As a government officer, I want to create tenders with detailed requirements and publish them for bidders to discover, so that I can initiate procurement processes.

#### Acceptance Criteria

1. WHEN an officer calls POST /api/officer/tenders with title and optional version_number, THE System SHALL create a Tender in "draft" status
2. WHEN a tender is created, THE System SHALL create a TenderVersion record with version_number (default "1.0") and published_at = NULL
3. WHEN an officer publishes a draft tender via POST /api/officer/tenders/{tender_id}/publish, THE System SHALL set tender.status = "published" and tender_version.published_at = current_timestamp
4. WHEN a tender is published, THE System SHALL log TENDER_PUBLISHED audit event with officer_id and tender_id
5. WHEN an officer lists tenders via GET /api/officer/tenders, THE System SHALL return all tenders created_by that officer with status, version_number, and published_at
6. THE System SHALL prevent publishing a tender that is already published (idempotent operation allowed but no state change)
7. THE System SHALL prevent modification of tender title after publication (immutable after publish)

### Requirement 2.2: Tender Discovery by Bidders

**User Story:** As a bidder, I want to browse published tenders and view their requirements, so that I can decide whether to submit a bid.

#### Acceptance Criteria

1. WHEN a bidder calls GET /api/bidder/tenders, THE System SHALL return all tenders with status = "published"
2. THE System SHALL return for each tender: id, title, organization, version, clause_count, required_documents list, published_at
3. WHEN a bidder calls GET /api/bidder/tenders/{tender_id}, THE System SHALL return tender details including clauses, requirements, and evaluation criteria
4. THE System SHALL make tender discovery endpoints accessible to both authenticated bidders and unauthenticated users (public browse mode)
5. WHEN querying published tenders, THE System SHALL return only the latest published TenderVersion for each Tender (filter by published_at IS NOT NULL)

### Requirement 2.3: Bid Creation and Initial State

**User Story:** As a bidder, I want to create a bid for a published tender and begin the submission process, so that I can respond to government procurement requests.

#### Acceptance Criteria

1. WHEN a bidder calls POST /api/bidder/tenders/{tender_id}/bids, THE System SHALL create a Bid record with status = "DRAFT" and current_state = "DRAFT"
2. WHEN a bid is created, THE System SHALL require the bidder's organization_id to be linked to the bidder's User record
3. WHEN a bid is created, THE System SHALL log BID_CREATED audit event with bidder_id and bid_id
4. WHEN a bid is created, THE System SHALL set bid.state_entered_at = current_timestamp and bid.state_metadata = {}
5. THE System SHALL associate the bid with the latest published TenderVersion (bid.tender_version_id = latest_version.id)
6. THE System SHALL prevent a bidder from creating multiple draft bids for the same tender (only one DRAFT bid allowed per bidder per tender)
7. WHEN a bidder calls GET /api/bidder/bids, THE System SHALL return all bids for their organization with status, current_state, submitted_at, and created_at

### Requirement 2.4: Required Documents Specification

**User Story:** As a government officer, I want to specify required documents for a tender, so that bidders know what to upload.

#### Acceptance Criteria

1. WHEN a tender is created, THE System SHALL define required_documents list (e.g., ["GST_CERT", "PAN", "COI"])
2. WHEN a bidder views tender details, THE System SHALL display required_documents list
3. THE System SHALL validate document types against predefined list: GST_CERT, PAN, COI, UDYAM, BANK_STATEMENT, ITR, CAPACITY_CERT
4. WHEN a bidder attempts to submit a bid, THE System SHALL verify all required_documents have been uploaded (Requirement 3.3)

---

## PHASE 3: DOCUMENT MANAGEMENT & VERSIONING

### Requirement 3.1: Document Upload with Hash Verification

**User Story:** As a bidder, I want to upload supporting documents for my bid, so that government can verify my compliance.

#### Acceptance Criteria

1. WHEN a bidder calls POST /api/bidder/bids/{bid_id}/documents with file and doc_type, THE System SHALL accept file upload
2. WHEN a document is uploaded, THE System SHALL compute SHA256 file hash and store in Document.file_hash
3. WHEN a document is uploaded, THE System SHALL store file to `/uploads/bids/{bid_id}/{doc_type}_{uuid}.{extension}`
4. WHEN a document is uploaded, THE System SHALL create Document record with: id (UUID), bid_id (FK), doc_type, file_path, file_hash, ocr_status = "PENDING", current_version = 1, uploaded_at = current_timestamp
5. WHEN a document upload succeeds, THE System SHALL return: document_id, version_number, file_hash, uploaded_at
6. THE System SHALL validate file size < 10MB and file type in [pdf, jpg, jpeg, png]
7. WHEN file size > 10MB or type not allowed, THE System SHALL reject with HTTP 400

### Requirement 3.2: Document Version History

**User Story:** As a bidder, I want to upload revised versions of documents without losing the original, so that my submission is auditable.

#### Acceptance Criteria

1. WHEN a bidder uploads a new version of an existing document (same doc_type, same bid_id), THE System SHALL create new DocumentVersion record with version_number incremented
2. WHEN a new version is uploaded, THE System SHALL set Document.current_version = new_version_number
3. WHEN a version is created, THE System SHALL record: document_id (FK), version_number, file_path, file_hash, ocr_status = "PENDING", uploaded_by (FK to User), uploaded_at = current_timestamp, change_reason (optional)
4. WHEN an officer queries a bid's documents, THE System SHALL return current version of each document (current_version field)
5. WHEN retrieving document version history, THE System SHALL return all DocumentVersion records for a document in ascending version_number order
6. THE System SHALL prevent deletion of documents (logical soft delete only by marking as deleted = true)

### Requirement 3.3: Document Slot Validation

**User Story:** As a government officer, I want to verify that all required documents have been uploaded for a bid, so that I can proceed with compliance evaluation.

#### Acceptance Criteria

1. WHEN a bidder calls POST /api/bidder/bids/{bid_id}/verify-stage1, THE System SHALL check for all required documents
2. THE System SHALL return response: `{"passed": true|false, "slots": [{"type": "GST|PAN|COI", "uploaded": true|false}], "uploaded_mandatory": 2, "total_mandatory": 3}`
3. WHEN all required documents are present, THE System SHALL set passed = true
4. WHEN any required document is missing, THE System SHALL set passed = false
5. THE System SHALL allow progressing to Stage 2 only if passed = true

### Requirement 3.4: OCR Processing Integration

**User Story:** As a compliance officer, I want documents to be automatically processed for text extraction, so that I can evaluate compliance without manual reading.

#### Acceptance Criteria

1. WHEN a document is uploaded, THE System SHALL enqueue OCRJob with status = "PENDING"
2. WHEN OCRJob is processed, THE System SHALL extract text from document PDF/image and store in OCRJob.extracted_text
3. WHEN OCR completes, THE System SHALL update DocumentVersion.ocr_status = "COMPLETED" or "FAILED"
4. WHEN OCR completes, THE System SHALL create ExtractedFact records for identified entities (name, address, dates, numbers)
5. IF OCR fails (format unsupported, corrupted file), THE System SHALL set DocumentVersion.ocr_status = "FAILED" and store error message
6. WHEN OCR completes, THE System SHALL log OCR_COMPLETED or OCR_FAILED audit event

---

## PHASE 4: COMPLIANCE RULE ENGINE

### Requirement 4.1: Compliance Rule Definition and Storage

**User Story:** As a system architect, I want to define deterministic compliance rules, so that bidder eligibility can be evaluated consistently.

#### Acceptance Criteria

1. THE System SHALL support compliance rules evaluating the following criteria:
   - Name consistency across documents (from OCR extraction)
   - GSTIN validity and correctness (verified via external source)
   - PAN validity and correctness (verified via external source)
   - CIN validity and correctness (verified via external source)
   - Udyam number validity (verified via external source)
   - Bank account details consistency
   - Financial threshold requirements (minimum turnover)
   - Sector eligibility requirements
   - Blacklist checks (suspended vendors, fraud records)
   - Duplicate bidder detection (same entity bidding twice)

2. EACH compliance rule SHALL have deterministic logic: if condition X, then result PASS or FAIL
3. EACH compliance rule SHALL produce ComplianceResult with: id (UUID), bid_id (FK), rule_name, rule_version, passed (boolean), evidence_references (JSON array of document_ids), explanation (failure reason), evaluated_at
4. THE System SHALL version compliance rules (rule_version) to track changes over time
5. THE System SHALL support clause-specific rule chains (e.g., Clause 1 requires PASS on [rule_1, rule_2, rule_3])

### Requirement 4.2: Compliance Evaluation Pipeline

**User Story:** As a government officer, I want automatic compliance evaluation, so that I can focus on edge cases rather than routine checks.

#### Acceptance Criteria

1. WHEN a bidder calls POST /api/bidder/bids/{bid_id}/verify-stage2, THE System SHALL execute all applicable compliance rules for the bid
2. WHEN a rule is evaluated, THE System SHALL extract required data from uploaded documents (via OCR) and external verification results
3. WHEN a rule fails, THE System SHALL store failure reason in ComplianceResult.explanation and reference document in evidence_references
4. WHEN all rules are evaluated, THE System SHALL aggregate results and set bid.compliance_status = "COMPLIANT" (all pass) or "NON_COMPLIANT" (any fail)
5. WHEN compliance evaluation completes, THE System SHALL return response with clause_results list: `[{"rule": "gstin_valid", "passed": true|false}, ...]`
6. THE System SHALL log COMPLIANCE_EVALUATED audit event with bid_id and compliance_status
7. WHEN compliance fails, THE System SHALL generate human-readable violation summary for officer review

### Requirement 4.3: Rule Evidence Traceability

**User Story:** As a government officer, I want to see which documents support each compliance decision, so that I can audit the evaluation logic.

#### Acceptance Criteria

1. WHEN a compliance rule is evaluated, THE System SHALL store in ComplianceResult.evidence_references array: document_ids and extracted_facts that supported the evaluation
2. WHEN an officer views bid details, THE System SHALL display for each failed rule: rule name, failure reason, evidence documents, and link to view document
3. THE System SHALL provide traceability from compliance result back to: document_id → DocumentVersion → ExtractedFact → original document file
4. WHEN an officer clicks "View Evidence", THE System SHALL display the document text excerpt that triggered the rule failure

### Requirement 4.4: Risk Signal Generation During Compliance Evaluation

**User Story:** As a system analyst, I want compliance violations to be flagged as risk signals, so that risk assessment can aggregate them.

#### Acceptance Criteria

1. WHEN a compliance rule fails, THE System SHALL create a RiskSignal with: id (UUID), bid_id (FK), signal_type (rule name), severity (HIGH|MEDIUM|LOW), description, detected_at, rule_explanation
2. WHEN rule "gstin_invalid" fails, THE System SHALL create RiskSignal with severity = "HIGH"
3. WHEN rule "name_mismatch" fails, THE System SHALL create RiskSignal with severity = "MEDIUM"
4. THE System SHALL NOT delete existing RiskSignals; instead create new ones on each evaluation (for historical tracking)
5. WHEN multiple risks are detected, THE System SHALL create separate RiskSignal records for each (not aggregated at signal level)

---

## PHASE 5: EXTERNAL DATA VERIFICATION

### Requirement 5.1: Multi-Source Verification Architecture

**User Story:** As a compliance officer, I want to verify bidder data against government registries, so that fraudulent entities can be detected.

#### Acceptance Criteria

1. THE System SHALL query the following external verification sources in parallel:
   - GSTIN Registry (via DataGovIn API)
   - PAN Registry (via DataGovIn API)
   - MCA Portal (Company House equivalent)
   - NSIC Database (Micro/Small/Medium Enterprise status)
   - Udyam Registry (Micro/Small/Medium Enterprise registration)

2. WHEN a compliance rule requires external verification, THE System SHALL call AdapterOrchestrator.verify_multi_source(bid_id, [sources])
3. THE System SHALL execute all source queries in parallel using async/await to minimize latency
4. WHEN a source query completes, THE System SHALL store VerificationAttempt record: source_name, bid_id, query_data (JSON), result (JSON), verified_at, success (boolean)
5. IF a source query fails (timeout, API error, invalid data), THE System SHALL retry up to 3 times with exponential backoff (1s, 2s, 4s)
6. IF all retries fail, THE System SHALL create VerificationAttempt with success = false and store error message

### Requirement 5.2: GSTIN Verification

**User Story:** As a bidder, I want my GSTIN to be automatically verified, so that I can confirm my tax registration is correct.

#### Acceptance Criteria

1. WHEN a compliance rule "gstin_valid" is evaluated, THE System SHALL extract GSTIN from bid state_metadata or OCR extracted facts
2. WHEN GSTIN is extracted, THE System SHALL query external GSTIN registry with: gstin_number, bidder_name (from extracted facts or organization record)
3. WHEN query returns matched GSTIN record, THE System SHALL store VerificationResult with: source = "GSTIN", verified = true, matched_legal_name, matched_status (active|inactive|suspended), confidence_score
4. WHEN GSTIN is not found or inactive, THE System SHALL set verified = false and explanation = "GSTIN not found in registry"
5. WHEN GSTIN is found but legal_name doesn't match extracted name, THE System SHALL set verified = false and create RiskSignal "gstin_name_mismatch" with severity = "HIGH"
6. WHEN GSTIN is verified, THE System SHALL return to compliance rule: verification_status, matched_details, confidence

### Requirement 5.3: Entity Resolution and Name Matching

**User Story:** As a system analyst, I want extracted bidder names to be matched against registry names, so that name spoofing can be detected.

#### Acceptance Criteria

1. WHEN compliance evaluation starts, THE System SHALL extract all bidder name variants from: Organization.legal_name, OCR extracted name, bid state_metadata bidder_org_name
2. WHEN multiple name sources exist, THE System SHALL compare for exact match; IF no exact match, compute Levenshtein distance and fuzzy match
3. WHEN fuzzy match confidence < 95%, THE System SHALL create RiskSignal "name_mismatch" with severity = "MEDIUM" and store both names in signal description
4. WHEN names match (confidence >= 95%), THE System SHALL store EntityResolutionResult with: bid_id (FK), source1_name, source2_name, match_type (exact|fuzzy), confidence_score, resolved_legal_name
5. WHEN a name is resolved, THE System SHALL create VerificationNameMatch record storing both entity references for audit

### Requirement 5.4: Verification Result Aggregation

**User Story:** As a government officer, I want a summary of all verification results, so that I can quickly assess the credibility of a bidder.

#### Acceptance Criteria

1. WHEN compliance evaluation completes, THE System SHALL aggregate all VerificationResult records for the bid
2. THE System SHALL create verification_summary with fields: total_sources_queried, sources_verified (count), sources_failed (count), unresolved_conflicts (count), overall_verification_status (VERIFIED|PARTIAL|FAILED)
3. WHEN all sources verify successfully, THE System SHALL set overall_verification_status = "VERIFIED"
4. WHEN some sources fail and others succeed, THE System SHALL set overall_verification_status = "PARTIAL" and list which sources failed
5. WHEN critical source (GSTIN, PAN) fails to verify, THE System SHALL set overall_verification_status = "FAILED"
6. THE System SHALL store verification_summary in ComplianceResult or separate VerificationSummary entity

---

## PHASE 6: RISK ASSESSMENT & SCORING

### Requirement 6.1: Risk Signal Aggregation

**User Story:** As a compliance officer, I want to see overall risk level at a glance, so that I can prioritize bid review efforts.

#### Acceptance Criteria

1. WHEN compliance evaluation completes, THE System SHALL aggregate all RiskSignals for the bid
2. THE System SHALL count signals by severity: high_count, medium_count, low_count
3. THE System SHALL create RiskAssessment record with: bid_id (FK), overall_risk_score (0-100), risk_level (LOW|MEDIUM|HIGH), assessed_at, signal_breakdown (JSON)
4. WHEN high_count >= 1, THE System SHALL set risk_level = "HIGH"
5. WHEN medium_count >= 2 AND high_count == 0, THE System SHALL set risk_level = "MEDIUM"
6. WHEN low_count >= 3 AND high_count == 0 AND medium_count <= 1, THE System SHALL set risk_level = "MEDIUM"
7. WHEN no signals detected, THE System SHALL set risk_level = "LOW"

### Requirement 6.2: Risk Scoring Algorithm

**User Story:** As a data scientist, I want configurable risk weights, so that risk scoring can be tuned for different procurement scenarios.

#### Acceptance Criteria

1. THE System SHALL define risk weights for each signal type: gstin_invalid (weight 25), pan_invalid (weight 20), name_mismatch (weight 15), duplicate_bidder (weight 40), blacklisted (weight 50), unverified_source (weight 10), financial_threshold_miss (weight 20)
2. WHEN computing overall_risk_score, THE System SHALL calculate: sum of (signal.weight * signal.count) with maximum cap of 100
3. WHEN overall_risk_score >= 70, THE System SHALL set risk_level = "HIGH"
4. WHEN overall_risk_score >= 40 AND overall_risk_score < 70, THE System SHALL set risk_level = "MEDIUM"
5. WHEN overall_risk_score < 40, THE System SHALL set risk_level = "LOW"
6. THE System SHALL store risk weights in configuration table to enable tuning without code changes

### Requirement 6.3: Risk Signal Decomposition

**User Story:** As a government officer, I want to understand why a bid is flagged as high-risk, so that I can decide whether to override the recommendation.

#### Acceptance Criteria

1. WHEN viewing bid details, THE System SHALL display RiskAssessment with detailed breakdown
2. FOR each RiskSignal, THE System SHALL display: signal_type, severity, detected_at, contributing_factors (array), evidence_references (document_ids)
3. WHEN an officer clicks on a signal, THE System SHALL show RiskSignalDecomposition with: why this signal was created, what data triggered it, which documents support it, recommendation for action
4. THE System SHALL link each signal to: specific compliance rule, extracted facts, external verification results

### Requirement 6.4: Risk Trending and Historical Comparison

**User Story:** As a procurement analyst, I want to track risk patterns across multiple bids, so that I can detect systemic fraud attempts.

#### Acceptance Criteria

1. THE System SHALL store complete RiskAssessment history; do not update or delete existing assessments
2. WHEN retrieving bid risk profile, THE System SHALL return latest RiskAssessment (most recent assessed_at)
3. WHEN an officer requests historical risk analysis, THE System SHALL retrieve all RiskAssessment records for a bidder organization and display: risk_level trend over time, most common signal types, risk score trajectory
4. THE System SHALL flag if same organization has multiple HIGH risk bids or persistent signal patterns

---

## PHASE 7: OFFICER DECISION SUPPORT

### Requirement 7.1: Bid Evaluation Dashboard

**User Story:** As a government officer, I want to view queued bids with compliance and risk summaries, so that I can prioritize evaluation efforts.

#### Acceptance Criteria

1. WHEN an officer calls GET /api/officer/bids, THE System SHALL return list of submitted bids with:
   - bid_id, bidder_org_name, tender_title, status, current_state
   - compliance_status (PENDING|COMPLIANT|NON_COMPLIANT)
   - risk_level (LOW|MEDIUM|HIGH)
   - decision (PENDING|VERIFIED|NON_COMPLIANT)
   - submitted_at, created_at

2. THE System SHALL sort bids by risk_level descending (HIGH first) to help officer prioritize
3. THE System SHALL support filtering by: status, risk_level, compliance_status
4. THE System SHALL support search by: bidder_org_name, bid_id, tender_title
5. WHEN officer list is generated, THE System SHALL JOIN with Organization, ComplianceResult, RiskAssessment, OfficerDecision tables
6. THE System SHALL handle NULL gracefully: if no RiskAssessment, display risk_level = "UNKNOWN"; if no OfficerDecision, display decision = "PENDING"

### Requirement 7.2: Bid Detail View with Full Context

**User Story:** As a government officer, I want to see comprehensive bid information before making a decision, so that I can make informed choices.

#### Acceptance Criteria

1. WHEN an officer calls GET /api/officer/bids/{bid_id}, THE System SHALL return:
   - Bidder organization: legal_name, gstin, pan, cin, udyam, sector, turnover, address
   - Bid metadata: id, status, current_state, submitted_at, state_history
   - Documents: list with doc_type, file_hash, ocr_status, current_version, uploaded_at
   - Compliance: clause-by-clause results with passed/failed status, failure reason, evidence links
   - Risk assessment: risk_level, overall_risk_score, signal_breakdown, recommendations
   - Verification results: source, verified (T/F), details, confidence
   - Clarifications: pending and past clarification requests/responses
   - Decision: if decided, show final_decision, decided_at, decided_by, reason/override_reason

2. THE System SHALL organize information into tabs/sections for clarity: Overview, Documents, Compliance, Risk, Verification, Clarifications, Decision

### Requirement 7.3: AI Recommendation Generation

**User Story:** As a compliance officer, I want AI-generated recommendation before deciding, so that I can verify my judgment against automated analysis.

#### Acceptance Criteria

1. WHEN compliance and risk evaluation complete, THE System SHALL generate ai_recommendation based on:
   - IF compliance_status = "COMPLIANT" AND risk_level = "LOW": recommendation = "PROCEED_TO_SUBMISSION"
   - IF compliance_status = "COMPLIANT" AND risk_level = "MEDIUM": recommendation = "PROCEED_WITH_CAUTION"
   - IF compliance_status = "COMPLIANT" AND risk_level = "HIGH": recommendation = "MANUAL_REVIEW_REQUIRED"
   - IF compliance_status = "NON_COMPLIANT": recommendation = "DO_NOT_PROCEED"

2. THE System SHALL store ai_recommendation in bid or decision record
3. THE System SHALL display recommendation prominently in officer detail view
4. THE System SHALL NOT force officer to follow recommendation; officer can override
5. WHEN officer decides to override recommendation, THE System SHALL require override_reason (free text) and store in OfficerDecisionOverride record

### Requirement 7.4: Clarification Request Workflow

**User Story:** As a government officer, I want to ask bidders clarifying questions, so that I can resolve ambiguities before final decision.

#### Acceptance Criteria

1. WHEN an officer views a bid and identifies an issue, THE System SHALL allow posting clarification request via POST /api/officer/bids/{bid_id}/clarifications
2. REQUEST body: `{"question_text": "...", "category": "GENERAL|COMPLIANCE|RISK|DOCUMENT"}`
3. WHEN clarification is posted, THE System SHALL create ClarificationRequest with: id (UUID), bid_id (FK), posted_by (officer_id), question_text, category, status = "OPEN", posted_at = current_timestamp
4. THE System SHALL notify bidder (via email and in-app) that a clarification request is pending
5. WHEN bidder responds via POST /api/bidder/bids/{bid_id}/clarifications/{request_id}/respond with `{"response_text": "..."}`, THE System SHALL create ClarificationResponse with: id (UUID), request_id (FK), response_text, responded_by (bidder_id), responded_at = current_timestamp, attachment_ids (optional)
6. WHEN response is posted, THE System SHALL update ClarificationRequest.status = "RESOLVED" and notify officer
7. THE System SHALL allow officer to re-open a clarification if response is unsatisfactory (status = "REOPENED")
8. THE System SHALL prevent bid submission if any clarification status = "OPEN" (bidder must resolve all first)

### Requirement 7.5: Officer Notes and Audit Trail

**User Story:** As a government officer, I want to add internal notes to a bid, so that I can document my reasoning for peer review.

#### Acceptance Criteria

1. WHEN an officer calls POST /api/officer/bids/{bid_id}/notes with `{"note": "...", "category": "GENERAL|COMPLIANCE|RISK|..."}`, THE System SHALL create note record
2. WHEN note is created, THE System SHALL store: note_id (UUID), bid_id (FK), author_id (officer_id), note_text, category, created_at, visible_to (array: [author, senior_officer, none])
3. WHEN visible_to = "author", note is visible only to posting officer (private)
4. WHEN visible_to = "senior_officer", note is visible to officers with senior role
5. WHEN visible_to = "none", note is not visible in frontend but stored for audit
6. WHEN retrieving bid details, THE System SHALL return officer notes with author name (not stored for bidder view)
7. THE System SHALL log OFFICER_NOTE_ADDED audit event

---

## PHASE 8: DECISION MAKING & APPROVAL

### Requirement 8.1: Officer Final Decision

**User Story:** As a government officer, I want to make a final decision on a bid, so that bidders know the outcome of their submission.

#### Acceptance Criteria

1. WHEN an officer calls POST /api/officer/bids/{bid_id}/decision with:
   ```json
   {
     "final_decision": "VERIFIED|NON_COMPLIANT|PENDING",
     "ai_recommendation": "PROCEED|PROCEED_WITH_CAUTION|MANUAL_REVIEW|DO_NOT_PROCEED",
     "override_reason": "string or null"
   }
   ```

2. WHEN final_decision = ai_recommendation, THE System SHALL store OfficerDecision with override_reason = NULL
3. WHEN final_decision != ai_recommendation, THE System SHALL require override_reason (not empty) and store OfficerDecisionOverride record
4. WHEN decision is made, THE System SHALL update Bid.status = "DECIDED" and Bid.current_state = "DECIDED"
5. WHEN decision is made, THE System SHALL set decision_at = current_timestamp and decided_by = officer_id
6. THE System SHALL prevent modifying a decision once made (immutable); officer must create new decision record if needed
7. WHEN decision is made, THE System SHALL log BID_DECIDED audit event with decision code and officer_id

### Requirement 8.2: Decision Audit and Override Tracking

**User Story:** As a procurement director, I want to audit all officer decisions, so that I can identify any patterns of bias or error.

#### Acceptance Criteria

1. WHEN an officer makes a decision, THE System SHALL log complete OfficerDecision record with: bid_id, officer_id, final_decision, ai_recommendation, decided_at
2. WHEN an override occurs (final_decision != ai_recommendation), THE System SHALL create OfficerDecisionOverride record with: decision_id (FK), override_reason, approved_by (if approval required), approved_at
3. WHEN override_reason is stored, THE System SHALL allow querying all decisions where override was made
4. THE System SHALL NOT allow editing override_reason after decision is made
5. THE System SHALL store all audit data for minimum 7 years (retention policy)

### Requirement 8.3: Multi-Level Approval Workflow (Optional)

**User Story:** As a procurement director, I want to approve high-risk decision overrides before they are finalized, so that I can ensure accountability.

#### Acceptance Criteria

1. WHERE risk_level = "HIGH" AND final_decision != ai_recommendation, THE System SHALL require approval from senior officer
2. WHEN such decision is made, THE System SHALL set OfficerDecisionOverride.requires_approval = true and status = "PENDING_APPROVAL"
3. WHEN senior officer approves via POST /api/officer/decisions/{decision_id}/approve, THE System SHALL set status = "APPROVED" and approved_at = current_timestamp
4. WHEN senior officer rejects via POST /api/officer/decisions/{decision_id}/reject with `{"reason": "..."}`, THE System SHALL set status = "REJECTED" and return decision to junior officer for revision
5. THE System SHALL prevent decision from becoming effective until status = "APPROVED"

---

## PHASE 9: BIDDER FEEDBACK & NOTIFICATIONS

### Requirement 9.1: Real-Time Bid Status Updates

**User Story:** As a bidder, I want to see my bid status in real-time, so that I know where my submission is in the evaluation process.

#### Acceptance Criteria

1. WHEN a bidder calls GET /api/bidder/bids/{bid_id}/status, THE System SHALL return:
   ```json
   {
     "status": "DRAFT|SUBMITTED|DECIDED",
     "current_state": "string",
     "decision": {
       "final_decision": "PENDING|VERIFIED|NON_COMPLIANT",
       "decided_at": "ISO8601 or null",
       "decided_by": "string or null",
       "override_reason": "string or null"
     },
     "compliance_status": "PENDING|COMPLIANT|NON_COMPLIANT",
     "risk_level": "LOW|MEDIUM|HIGH|UNKNOWN",
     "officer_notes": ["count only, not content"],
     "document_flags": [{"doc_type": "GST", "flag": "OCR_FAILED"}],
     "tender": {
       "id": "uuid",
       "title": "string",
       "organization": "string",
       "version": "1.0"
     },
     "submitted_at": "ISO8601 or null",
     "current_step": "DRAFT|EVALUATION|DECIDED"
   }
   ```

2. THE System SHALL update status in real-time as bid transitions through states
3. WHEN a new state is entered, THE System SHALL update state_entered_at timestamp
4. THE System SHALL NOT expose officer notes, detailed risk signals, or internal compliance details to bidder (only high-level summary)

### Requirement 9.2: Notification System

**User Story:** As a bidder, I want notifications when my bid status changes, so that I can respond to clarifications promptly.

#### Acceptance Criteria

1. WHEN any of the following events occur, THE System SHALL create Notification record and send to bidder via email:
   - Bid submitted (confirmation)
   - Bid moved to evaluation
   - Clarification request posted (with question snippet)
   - Decision made (VERIFIED or NON_COMPLIANT with brief reason)

2. WHEN Notification is created, THE System SHALL store: id (UUID), user_id (FK to bidder user), notification_type, bid_id (FK), message_template, context_data (JSON), created_at, sent_at = NULL, read_at = NULL
3. WHEN sending email, THE System SHALL use notification_type to select template and populate context_data
4. WHEN email is sent, THE System SHALL set sent_at = current_timestamp
5. WHEN bidder views notification in app (GET /api/bidder/notifications), THE System SHALL set read_at = current_timestamp

### Requirement 9.3: Compliance Readiness Gauge

**User Story:** As a bidder, I want to know how compliant my bid is before submission, so that I can improve it if needed.

#### Acceptance Criteria

1. WHEN a bidder calls GET /api/bidder/bids/{bid_id}/readiness, THE System SHALL return:
   ```json
   {
     "readiness_percent": 67,
     "items": [
       {
         "requirement": "GSTIN validity",
         "status": "SATISFIED|MISSING|WEAK_EVIDENCE|REVIEW",
         "evidence_count": 2
       }
     ],
     "tender": {
       "id": "uuid",
       "title": "string",
       "version": "1.0"
     }
   }
   ```

2. WHEN a compliance rule passes, THE System SHALL mark corresponding requirement as "SATISFIED"
3. WHEN a compliance rule fails, THE System SHALL mark as "MISSING" (if data absent) or "REVIEW" (if data present but issue flagged)
4. THE System SHALL compute readiness_percent = (satisfied_count / total_requirements) * 100
5. THE System SHALL allow bidder to view readiness at any time before submission

### Requirement 9.4: Clarification Response Portal

**User Story:** As a bidder, I want to respond to officer clarifications in the system, so that I don't miss questions and can provide supporting documents.

#### Acceptance Criteria

1. WHEN a clarification request is posted, THE System SHALL create in-app notification for bidder
2. WHEN bidder calls GET /api/bidder/bids/{bid_id}/clarifications, THE System SHALL return list of clarification requests: id, question_text, category, posted_at, status (OPEN|RESOLVED), response (if exists)
3. WHEN bidder responds via POST /api/bidder/bids/{bid_id}/clarifications/{request_id}/respond, THE System SHALL accept response_text and optional attachments (file_ids)
4. WHEN response is created, THE System SHALL update request status = "RESOLVED"
5. THE System SHALL allow bidder to update response until officer has reviewed (no response freezing after bidder posts)

---

## PHASE 10: AUDIT, REPORTING & SYSTEM INTEGRITY

### Requirement 10.1: Complete Audit Trail

**User Story:** As a compliance auditor, I want complete audit trail of all system actions, so that I can investigate any disputes.

#### Acceptance Criteria

1. THE System SHALL log all actions via AuditEvent table with: id (UUID), event_type, actor_id (FK to User), actor_role, entity_type, entity_id, timestamp = current_timestamp, details (JSON), ip_address (if tracked)
2. AUDIT event_types include: TENDER_CREATED, TENDER_PUBLISHED, BID_CREATED, BID_SUBMITTED, COMPLIANCE_EVALUATED, RISK_ASSESSED, DECISION_MADE, OFFICER_DECISION_OVERRIDE, CLARIFICATION_POSTED, CLARIFICATION_RESPONDED, DOCUMENT_UPLOADED, DOCUMENT_VERSION_CREATED, VERIFICATION_EXECUTED, OCR_COMPLETED, OCR_FAILED, STATE_TRANSITIONED
3. WHEN retrieving audit trail via GET /api/bids/{bid_id}/audit, THE System SHALL return chronological list of events with: event_type, actor info, timestamp, details
4. THE System SHALL make audit trail accessible to officers with "auditor" or "senior" role
5. THE System SHALL NOT allow editing or deleting audit records (immutable append-only log)
6. WHEN an event involves sensitive data, THE System SHALL redact PII in audit details (store hashes of PAN, GSTIN for reference only)

### Requirement 10.2: Bid State History and Reconstruction

**User Story:** As a system analyst, I want to reconstruct bid state at any point in time, so that I can debug issues and verify correctness.

#### Acceptance Criteria

1. WHEN a bid transitions between states, THE System SHALL create BidState record with: bid_id (FK), state_exited (previous state), state_entered (new state), exited_at = current_timestamp, entered_at = current_timestamp, metadata (JSON)
2. WHEN retrieving bid state history via GET /api/bids/{bid_id}/state/history, THE System SHALL return chronological list of all state transitions
3. THE System SHALL allow querying: "What was bid X's state at time T?" by finding BidState record where entered_at <= T and (exited_at > T or exited_at IS NULL)
4. WHEN state history is requested, THE System SHALL also include relevant events from AuditEvent table with matching timestamp

### Requirement 10.3: Compliance Rule Audit

**User Story:** As a system auditor, I want to see which rule version was applied to each bid, so that I can understand why an old rule may have produced different result.

#### Acceptance Criteria

1. WHEN a compliance rule is evaluated, THE System SHALL store in ComplianceResult: rule_name, rule_version (e.g., "1.0", "2.1"), evaluated_at, by_system_version (backend version at time of evaluation)
2. WHEN rule logic is changed, THE System SHALL increment rule_version and update evaluation code
3. WHEN querying historical compliance results, THE System SHALL include rule_version so auditor can understand which rule was applied
4. THE System SHALL store all rule versions in database or version control for historical reference
5. WHEN re-evaluating a bid with new rule version, THE System SHALL create new ComplianceResult record (not update existing)

### Requirement 10.4: Data Integrity and Consistency

**User Story:** As a database administrator, I want to ensure data integrity, so that I can trust system outputs.

#### Acceptance Criteria

1. THE System SHALL enforce referential integrity via foreign key constraints
2. WHEN a tender is deleted, THE System SHALL delete dependent TenderVersion records
3. WHEN a bid is deleted, THE System SHALL cascade delete Document, ComplianceResult, RiskAssessment, OfficerDecision records
4. THE System SHALL implement database constraints: User.email UNIQUE, Organization(gstin, pan) UNIQUE
5. WHEN a transaction fails, THE System SHALL roll back all changes (ACID compliance)
6. THE System SHALL log all data modifications (INSERT, UPDATE, DELETE) in AuditEvent for compliance
7. WHEN querying data, THE System SHALL validate referential integrity (e.g., no orphaned Document records)

### Requirement 10.5: System-wide Consistency and Idempotency

**User Story:** As a system architect, I want idempotent operations, so that network retries don't cause duplicate data or state corruption.

#### Acceptance Criteria

1. WHEN an operation is retried (due to network failure), THE System SHALL detect retry and return same result without side effects
2. KEY endpoints must be idempotent: POST /api/officer/tenders/{id}/publish (idempotent: publish already-published tender returns success)
3. WHEN a state transition is retried, THE System SHALL not create duplicate BidState records
4. THE System SHALL use database-level constraints or application-level deduplication (e.g., idempotency keys) to prevent duplicates
5. WHEN audit event is logged, THE System SHALL include idempotency_key (optional) for retry detection

### Requirement 10.6: Export and Reporting

**User Story:** As a procurement officer, I want to export bid data for reporting, so that I can create procurement dashboards and analytics.

#### Acceptance Criteria

1. WHEN an officer calls GET /api/officer/reports/bids-summary, THE System SHALL return aggregated data: total_bids, by_status (count), by_risk_level (count), by_decision (count), by_tender
2. WHEN officer calls GET /api/officer/reports/bids-export?format=csv, THE System SHALL export all bids with columns: bid_id, bidder_org, tender, status, compliance_status, risk_level, decision, submitted_at, decided_at
3. THE System SHALL support export formats: CSV, JSON, PDF (for formal reports)
4. WHEN exporting, THE System SHALL mask/redact sensitive bidder data (PII) unless officer has audit role
5. THE System SHALL allow filtering export by: date range, tender_id, status, risk_level, decision

---

## Integration Points Summary

### Frontend-Backend Integration

| Endpoint | Frontend Component | Data Flow | Auth |
|----------|-------------------|-----------|------|
| POST /api/auth/login | LoginPage.jsx | Credentials → JWT token | Public |
| POST /api/officer/tenders | OfficerDashboard → create | Tender title → Tender record | Officer |
| POST /api/officer/tenders/{id}/publish | OfficerDashboard → publish | tender_id → published status | Officer |
| GET /api/bidder/tenders | BidderTenders.jsx | None → tender list | Bidder |
| POST /api/bidder/tenders/{id}/bids | BidderTenders.jsx | tender_id → bid_id | Bidder |
| POST /api/bidder/bids/{id}/documents | BidderSubmissionFlow.jsx | file + doc_type → document_id | Bidder |
| POST /api/bidder/bids/{id}/verify-stage1 | BidderSubmissionFlow.jsx | bid_id → stage1_results | Bidder |
| POST /api/bidder/bids/{id}/verify-stage2 | BidderSubmissionFlow.jsx | bid_id → compliance_results | Bidder |
| GET /api/bidder/bids/{id}/readiness | BidderSubmissionFlow.jsx | bid_id → readiness_percent | Bidder |
| POST /api/bidder/bids/{id}/submit | BidderSubmissionFlow.jsx | bid_id → submitted status | Bidder |
| GET /api/officer/bids | OfficerDashboard.jsx | None → bid list with risk/compliance | Officer |
| GET /api/officer/bids/{id} | OfficerBidDetail.jsx | bid_id → bid details + context | Officer |
| POST /api/officer/bids/{id}/evaluate | OfficerBidDetail.jsx | bid_id → compliance evaluated | Officer |
| POST /api/officer/bids/{id}/decision | OfficerBidDetail.jsx | decision data → decision_id | Officer |
| GET /api/bids/{id}/audit | BidAuditView.jsx | bid_id → audit events | Officer |

### Backend Service Integration

| Service | Depends On | Provides |
|---------|-----------|----------|
| BidService | Database | Bid CRUD operations |
| ComplianceService | BidService, AdapterOrchestrator | Rule evaluation, compliance results |
| RiskService | ComplianceService | Risk assessment, scoring |
| AdapterOrchestrator | External sources | Verification results |
| OCRService | Document storage | Text extraction, entity facts |
| ClarificationService | BidService | Clarification CRUD, notifications |
| OfficerDecisionService | ComplianceService, RiskService | Decision records, audit logging |
| NotificationService | ClarificationService, OfficerDecisionService | Email/in-app notifications |
| AuditService | All services | Immutable event logging |
| EvidenceTraceability | OCRService, ComplianceService, AdapterOrchestrator | Compliance evidence mapping |

### External System Integration

| Source | Query Type | Data Used For | Verification |
|--------|-----------|--------|--------------|
| GSTIN Registry | GSTIN number, bidder name | Compliance: gstin_valid rule | Tax registration verified |
| PAN Registry | PAN number, bidder name | Compliance: pan_valid rule | Income tax registration verified |
| MCA Portal | CIN, company name | Compliance: cin_valid rule | Company House registration verified |
| NSIC Database | Organization GSTIN/name | Compliance: msme_status rule | MSME classification verified |
| Udyam Registry | Udyam number, org details | Compliance: udyam_valid rule | Udyam registration verified |
| DataGovIn API | All of above | Aggregate queries, batching | Government data hub |

---

## Success Criteria (10 Phases)

### Phase 1: Foundation & Authentication ✅
- [x] User roles (officer/bidder) enforced via RBAC
- [x] JWT authentication working for 3600 seconds
- [x] Organization-user association established
- [x] Core database schema created with foreign keys
- [x] Standard API response formats implemented

### Phase 2: Tender Management & Bid Creation ✅
- [x] Officers can create and publish tenders
- [x] Bidders can discover published tenders
- [x] Bidders can create draft bids for tenders
- [x] Bid status tracking implemented
- [x] State machine initialized (DRAFT state)

### Phase 3: Document Management & Versioning ✅
- [x] Bidders can upload documents
- [x] File hash verification implemented
- [x] Document versioning tracks multiple uploads
- [x] Required document slots validated
- [x] OCR pipeline enqueued (mocked in Phase 3)

### Phase 4: Compliance Rule Engine ⏳
- [ ] 10+ compliance rules implemented and tested
- [ ] Rule evaluation pipeline working end-to-end
- [ ] Compliance results stored with evidence traceability
- [ ] Risk signals generated for failures
- [ ] Rule versions tracked for audit

### Phase 5: External Data Verification ⏳
- [ ] Multi-source verification (GSTIN, PAN, MCA, NSIC, Udyam) integrated
- [ ] Parallel async queries to sources implemented
- [ ] Verification results stored with confidence scores
- [ ] Name matching/entity resolution working
- [ ] Retry logic with exponential backoff tested

### Phase 6: Risk Assessment & Scoring ⏳
- [ ] Risk signals aggregated into risk scores
- [ ] Risk scoring algorithm tuned and calibrated
- [ ] Risk decomposition explanations generated
- [ ] Historical risk trending tracked
- [ ] Risk levels (LOW/MEDIUM/HIGH) correctly assigned

### Phase 7: Officer Decision Support ⏳
- [ ] Officer dashboard displays bids sorted by risk
- [ ] Bid detail view shows compliance + risk context
- [ ] AI recommendation generated and displayed
- [ ] Clarification request workflow implemented
- [ ] Officer notes stored for audit

### Phase 8: Decision Making & Approval ⏳
- [ ] Officers can make final decisions
- [ ] Decision override tracking implemented
- [ ] Multi-level approval for high-risk overrides working
- [ ] Immutable decision records stored
- [ ] Audit trail complete for decisions

### Phase 9: Bidder Feedback & Notifications ⏳
- [ ] Bidders see real-time bid status
- [ ] Email notifications sent for state changes
- [ ] Compliance readiness gauge working
- [ ] Clarification response portal functional
- [ ] No sensitive data leaked to bidder view

### Phase 10: Audit, Reporting & Integrity ⏳
- [ ] Complete audit trail stored immutably
- [ ] Bid state history reconstructible at any point in time
- [ ] Compliance rule versions tracked
- [ ] Data integrity constraints enforced
- [ ] Idempotent operations preventing duplicates
- [ ] Export/reporting functionality working

---

## Database Schema Summary

### Core Tables

```sql
-- Organizations
CREATE TABLE organization (
  id UUID PRIMARY KEY,
  legal_name VARCHAR,
  gstin VARCHAR UNIQUE,
  pan VARCHAR UNIQUE,
  cin VARCHAR UNIQUE,
  udyam_number VARCHAR,
  sector VARCHAR,
  turnover DECIMAL,
  address TEXT,
  created_at TIMESTAMP
);

-- Users
CREATE TABLE user (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE,
  password_hash VARCHAR,
  role VARCHAR (officer|bidder),
  organization_id UUID REFERENCES organization(id),
  created_at TIMESTAMP
);

-- Tenders
CREATE TABLE tender (
  id UUID PRIMARY KEY,
  title VARCHAR,
  status VARCHAR (draft|published|closed),
  created_by UUID REFERENCES user(id),
  organization_id UUID REFERENCES organization(id),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE tender_version (
  id UUID PRIMARY KEY,
  tender_id UUID REFERENCES tender(id),
  version_number VARCHAR,
  source_document_path VARCHAR,
  published_at TIMESTAMP,
  precedence_policy_version VARCHAR,
  created_at TIMESTAMP
);

-- Bids
CREATE TABLE bid (
  id UUID PRIMARY KEY,
  tender_version_id UUID REFERENCES tender_version(id),
  bidder_org_id UUID REFERENCES organization(id),
  status VARCHAR (draft|submitted|decided),
  current_state VARCHAR,
  state_entered_at TIMESTAMP,
  state_metadata JSON,
  submitted_at TIMESTAMP,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Documents
CREATE TABLE document (
  id UUID PRIMARY KEY,
  bid_id UUID REFERENCES bid(id),
  doc_type VARCHAR,
  file_path VARCHAR,
  file_hash VARCHAR,
  ocr_status VARCHAR,
  current_version INT,
  uploaded_at TIMESTAMP
);

CREATE TABLE document_version (
  id UUID PRIMARY KEY,
  document_id UUID REFERENCES document(id),
  version_number INT,
  file_path VARCHAR,
  file_hash VARCHAR,
  ocr_status VARCHAR,
  extracted_text TEXT,
  uploaded_by UUID REFERENCES user(id),
  uploaded_at TIMESTAMP,
  change_reason VARCHAR
);

-- Compliance & Risk
CREATE TABLE compliance_result (
  id UUID PRIMARY KEY,
  bid_id UUID REFERENCES bid(id),
  rule_name VARCHAR,
  rule_version VARCHAR,
  passed BOOLEAN,
  evidence_references JSON,
  explanation TEXT,
  evaluated_at TIMESTAMP
);

CREATE TABLE risk_signal (
  id UUID PRIMARY KEY,
  bid_id UUID REFERENCES bid(id),
  signal_type VARCHAR,
  severity VARCHAR (HIGH|MEDIUM|LOW),
  description TEXT,
  detected_at TIMESTAMP
);

CREATE TABLE risk_assessment (
  id UUID PRIMARY KEY,
  bid_id UUID REFERENCES bid(id),
  overall_risk_score DECIMAL,
  risk_level VARCHAR (LOW|MEDIUM|HIGH),
  assessed_at TIMESTAMP
);

-- Verification
CREATE TABLE verification_result (
  id UUID PRIMARY KEY,
  bid_id UUID REFERENCES bid(id),
  source_name VARCHAR,
  verified BOOLEAN,
  details JSON,
  confidence_score DECIMAL,
  verified_at TIMESTAMP
);

-- Officer Decision
CREATE TABLE officer_decision (
  id UUID PRIMARY KEY,
  bid_id UUID REFERENCES bid(id),
  final_decision VARCHAR,
  ai_recommendation VARCHAR,
  decided_by UUID REFERENCES user(id),
  decided_at TIMESTAMP
);

CREATE TABLE officer_decision_override (
  id UUID PRIMARY KEY,
  decision_id UUID REFERENCES officer_decision(id),
  override_reason TEXT,
  approved_by UUID REFERENCES user(id),
  approved_at TIMESTAMP
);

-- Clarifications
CREATE TABLE clarification_request (
  id UUID PRIMARY KEY,
  bid_id UUID REFERENCES bid(id),
  posted_by UUID REFERENCES user(id),
  question_text TEXT,
  status VARCHAR (OPEN|RESOLVED|REOPENED),
  posted_at TIMESTAMP
);

CREATE TABLE clarification_response (
  id UUID PRIMARY KEY,
  request_id UUID REFERENCES clarification_request(id),
  response_text TEXT,
  responded_by UUID REFERENCES user(id),
  responded_at TIMESTAMP
);

-- Audit
CREATE TABLE audit_event (
  id UUID PRIMARY KEY,
  event_type VARCHAR,
  actor_id UUID REFERENCES user(id),
  actor_role VARCHAR,
  entity_type VARCHAR,
  entity_id VARCHAR,
  timestamp TIMESTAMP,
  details JSON
);

CREATE TABLE bid_state (
  id UUID PRIMARY KEY,
  bid_id UUID REFERENCES bid(id),
  state_exited VARCHAR,
  state_entered VARCHAR,
  exited_at TIMESTAMP,
  entered_at TIMESTAMP,
  metadata JSON
);

-- Notifications
CREATE TABLE notification (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES user(id),
  notification_type VARCHAR,
  bid_id UUID REFERENCES bid(id),
  message_template VARCHAR,
  context_data JSON,
  created_at TIMESTAMP,
  sent_at TIMESTAMP,
  read_at TIMESTAMP
);
```

---

## API Endpoints Summary

### Authentication (Phase 1)
- POST /api/auth/login

### Tender Management (Phase 2)
- POST /api/officer/tenders
- POST /api/officer/tenders/{id}/publish
- GET /api/officer/tenders
- GET /api/tenders (public)
- GET /api/bidder/tenders
- GET /api/bidder/tenders/{id}

### Bid Management (Phase 2-3)
- POST /api/bidder/tenders/{id}/bids
- GET /api/bidder/bids
- GET /api/bidder/bids/{id}
- GET /api/officer/bids
- GET /api/officer/bids/{id}

### Document Management (Phase 3)
- POST /api/bidder/bids/{id}/documents
- GET /api/bidder/bids/{id}/documents
- DELETE /api/bidder/bids/{id}/documents/{doc_id}
- POST /api/bidder/bids/{id}/verify-stage1 (slot validation)

### Compliance & Risk (Phase 4-6)
- POST /api/bidder/bids/{id}/verify-stage2 (compliance evaluation)
- GET /api/bidder/bids/{id}/readiness (compliance gauge)
- POST /api/officer/bids/{id}/evaluate (trigger compliance eval)
- POST /api/officer/bids/{id}/verify-source (trigger verification)

### Decision Making (Phase 7-8)
- POST /api/officer/bids/{id}/clarifications
- POST /api/officer/bids/{id}/notes
- POST /api/officer/bids/{id}/decision
- GET /api/officer/bids/{id}/decision

### Bidder Portal (Phase 9)
- GET /api/bidder/bids/{id}/status
- GET /api/bidder/bids/{id}/readiness
- GET /api/bidder/clarifications
- POST /api/bidder/clarifications/{id}/respond
- GET /api/bidder/notifications

### Audit & Reporting (Phase 10)
- GET /api/bids/{id}/audit
- GET /api/audit (officers only)
- GET /api/officer/reports/bids-summary
- GET /api/officer/reports/bids-export

---

## Dependencies Between Phases

```
Phase 1 (Auth) → Foundation for all phases
  ↓
Phase 2 (Tender & Bid) → Requires Phase 1 auth & roles
  ↓
Phase 3 (Documents) → Requires Phase 2 bid creation
  ↓
Phase 4 (Compliance Rules) → Requires Phase 3 documents & OCR
  ↓
Phase 5 (Verification) → Parallel to Phase 4, feeds into risk
  ↓
Phase 6 (Risk Scoring) → Requires Phase 4 signals + Phase 5 verification
  ↓
Phase 7 (Decision Support) → Requires Phase 6 risk assessment
  ↓
Phase 8 (Decisions) → Requires Phase 7 context
  ↓
Phase 9 (Notifications) → Requires Phase 8 decisions
  ↓
Phase 10 (Audit) → Tracks all prior phases
```

---

## Non-Functional Requirements

### Performance
- WHEN querying /api/officer/bids list, THE System SHALL respond within 2 seconds for 1000+ bids
- WHEN evaluating compliance rules, THE System SHALL complete within 30 seconds
- WHEN querying verification sources, THE System SHALL parallelize and complete within 15 seconds
- WHEN computing risk assessment, THE System SHALL complete within 5 seconds

### Availability
- THE System SHALL maintain 99.5% uptime during business hours
- WHEN database connection fails, THE System SHALL retry with exponential backoff
- WHEN external verification source is down, THE System SHALL continue with partial results

### Security
- ALL passwords SHALL be hashed with Argon2
- ALL API requests except /login SHALL require valid JWT token
- THE System SHALL enforce RBAC: officer endpoints verify role = "officer"
- THE System SHALL implement CSRF protection on state-changing endpoints
- THE System SHALL validate and sanitize all user inputs
- THE System SHALL not log sensitive data (PAN, GSTIN, passwords) in plain text

### Data Integrity
- WHEN a transaction fails, THE System SHALL roll back all changes (ACID)
- THE System SHALL enforce foreign key constraints
- THE System SHALL prevent orphaned records via cascade delete
- THE System SHALL audit all data modifications

### Compliance & Auditability
- THE System SHALL maintain immutable audit trail
- WHEN any bid decision is made, THE System SHALL log event with timestamp, user, reason
- WHEN data is accessed, THE System SHALL log access (for compliance audit)
- THE System SHALL support data retention policies (keep audit logs for 7+ years)
- THE System SHALL support data export for compliance reporting

---

## Document Version

- **Version:** 1.0
- **Date:** 2026-09-12
- **Status:** COMPLETE - ALL 10 PHASES SPECIFIED
- **Phases Covered:** 1-10 (Foundation through Audit)
- **Total Requirements:** 45+ functional requirements across all phases
- **Total API Endpoints:** 30+ endpoints specified
- **Database Tables:** 18+ core tables with relationships specified

