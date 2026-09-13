# Implementation Plan: Real Government Data Verification

## Overview

This implementation plan translates 14 requirements and 15 correctness properties into an incremental, dependency-ordered task sequence. The design uses a pluggable adapter pattern with a registry as the single swap point, enabling seamless switching between real and mock adapters. Tasks build from foundational abstractions (base adapter, name matching) through adapter implementations, database schema, compliance integration, and finally UI and deployment integration.

---

## Tasks

- [ ] 1. Foundation: Base Adapter Interface and Verification Classes
  - [ ] 1.1 Create PortalAdapter abstract base class with verify() and status_map() methods
    - Implement timeout + retry logic with exponential backoff (1s, 2s)
    - Implement error-to-status mapping (401 → ERROR, 429 → ERROR, 5xx → UNAVAILABLE, timeout → UNAVAILABLE)
    - Define VerificationStatus enum (VERIFIED, MISMATCH, UNAVAILABLE, ERROR, INCONCLUSIVE, PENDING)
    - Define VerificationClaim and VerificationResult dataclasses
    - _Requirements: 1.8, 3.1, 3.2-3.7, 6.1-6.9, 8.1-8.9_

  - [ ]* 1.2 Write property tests for PortalAdapter base class
    - **Property 4: Verification Status Not Boolean** — Verify status is never boolean or null
    - **Property 5: HTTP Status to VerificationStatus Mapping** — Test mapping function for all status codes
    - **Property 6: Retry Logic Exponential Backoff** — Verify 1s then 2s backoff sequence
    - **Property 7: No Retry on Auth Failure** — Verify 401 and 429 don't retry
    - **Property 8: Timeout Handling Maps to UNAVAILABLE** — Verify timeouts return UNAVAILABLE, not ERROR or MISMATCH
    - _Requirements: 3.8, 6.2-6.9, 8.1-8.7_

- [ ] 2. Name Matching Service
  - [ ] 2.1 Implement normalize_name() pure function with deterministic normalization
    - Trim whitespace, lowercase, remove punctuation, collapse spaces
    - _Requirements: 7.1, 7.2_

  - [ ] 2.2 Implement match_names() function with exact and fuzzy (Jaro-Winkler) matching
    - Return (match_result, match_score) tuple
    - Support configurable fuzzy_threshold (default 0.85)
    - _Requirements: 7.3-7.9_

  - [ ]* 2.3 Write property tests for name matching
    - **Property 1: Name Normalization Determinism** — Applying normalize twice yields same result
    - **Property 2: Exact Name Match Detection** — Identical normalized names yield exact_match with score 1.0
    - **Property 3: Fuzzy Match Threshold Behavior** — Score >= 0.85 → fuzzy_match, < 0.85 → no_match
    - _Requirements: 7.1-7.6, 7.9_

- [ ] 3. Database Schema and Models
  - [ ] 3.1 Create migration 0006_add_verification_tables with three new tables
    - VerificationAttempt: id, extracted_fact_id, source_document_id, verification_provider, extracted_value, request_timestamp
    - VerificationResult: id, verification_attempt_id, api_response_code, api_reference_id, authority_value, authority_normalized_value, response_timestamp, verification_status, fallback_used, http_error_message
    - VerificationNameMatch: id, verification_attempt_id, document_name, normalized_document_name, authority_name, normalized_authority_name, match_result, match_score
    - _Requirements: 4.1-4.7, 4.9_

  - [ ] 3.2 Add SQLAlchemy ORM models (VerificationAttempt, VerificationResult, VerificationNameMatch)
    - Define relationships with ExtractedFact and Document
    - Add CHECK constraints for enum values and ranges
    - Add database indexes for query performance
    - _Requirements: 4.1-4.7, 4.9_

  - [ ] 3.3 Update ExtractedFact and Document models with backward relationships
    - _Requirements: 4.1_

- [ ] 4. Mock Adapters Preservation and Registry
  - [ ] 4.1 Verify existing mock adapters remain unmodified (GSTNMockAdapter, MCAMockAdapter, NSICMockAdapter, UDYAMMockAdapter, PANMockAdapter)
    - Confirm mock behavior: valid → VERIFIED, invalid format → MISMATCH, not found → INCONCLUSIVE, timeout → UNAVAILABLE, auth fail → ERROR
    - _Requirements: 2.1, 2.2, 2.6_

  - [ ] 4.2 Create RegistryManager singleton class in registry.py
    - Load environment variables (GSTIN_API_KEY, MCA_API_KEY, NSIC_API_KEY, UDYAM_API_KEY, PAN_API_KEY) at startup
    - Select adapters: Real if creds present, Mock if not
    - Maintain ADAPTER_REGISTRY dict as single swap point
    - Implement get_adapter(source_name) and get_adapter_for_field(field_name)
    - Log adapter status at startup (which are enabled, which are mock)
    - _Requirements: 2.3, 2.7, 5.1-5.2, 12.4, 13.2_

  - [ ]* 4.3 Write property test for credential injection
    - **Property 10: Credential Injection Disables Missing Adapters** — When env var missing, adapter.enabled=False and verify() returns UNAVAILABLE without API calls
    - _Requirements: 1.6, 1.7, 5.1-5.3_

  - [ ]* 4.4 Write property test for fallback behavior
    - **Property 11: Fallback to Mock on Real Adapter Failure** — On AdapterError, fallback to Mock with fallback_used=True
    - _Requirements: 2.4, 2.5_

- [ ] 5. Real Adapter Implementations (GSTIN, MCA, PAN, NSIC, UDYAM)
  - [ ] 5.1 Implement GSTINAdapter (Real) with GSTN API integration
    - Accept GSTIN_API_KEY from environment
    - Validate GSTIN format (15 chars, alphanumeric)
    - Call https://api.gst.gov.in/gst/returns/{gstin} with Bearer token
    - Parse response: status, name, state, business_type
    - Map status "active" + exact/fuzzy name match → VERIFIED; status "active" + name mismatch → MISMATCH; status != "active" → INCONCLUSIVE
    - Handle 404 → INCONCLUSIVE, 401 → AdapterError, 429 → AdapterError, 5xx → AdapterError
    - _Requirements: 1.1, 1.6, 1.9, 5.1_

  - [ ] 5.2 Implement MCAAdapter (Real) with MCA portal integration
    - Accept MCA_API_KEY from environment
    - Validate CIN format (21 chars, alphanumeric)
    - Call https://api.data.gov.in/resource/companies-house-data with query params
    - Parse response: CIN, Company_Name, Status, ROC, Date_of_Incorporation
    - Map status "Active" + name match → VERIFIED; status "Active" + name mismatch → MISMATCH; status != "Active" → INCONCLUSIVE
    - Handle errors (404, 401, 429, 5xx) as above
    - _Requirements: 1.2, 1.6, 1.9, 5.1_

  - [ ] 5.3 Implement PANAdapter (Real) with Income Tax PAN verification
    - Accept PAN_API_KEY from environment
    - Validate PAN format (10 chars, alphanumeric)
    - Call https://incometaxindiaefiling.gov.in/e-filing/services/pan-verification (POST with pan, name, api_key)
    - Parse response: status, pan, name, entity_type
    - Map status "valid" + name match → VERIFIED; status "valid" + name mismatch → MISMATCH; status != "valid" → INCONCLUSIVE
    - Handle errors (404, 401, 429, 5xx) as above
    - _Requirements: 1.5, 1.6, 1.9, 5.1_

  - [ ] 5.4 Implement NSICAdapter (Real) with NSIC verification service
    - Accept NSIC_API_KEY from environment
    - Validate NSIC number format
    - Call NSIC verification API endpoint
    - Parse response and map statuses
    - _Requirements: 1.3, 1.6, 1.9, 5.1_

  - [ ] 5.5 Implement UDYAMAdapter (Real) with UDYAM registration portal
    - Accept UDYAM_API_KEY from environment
    - Validate UDYAM number format
    - Call UDYAM verification API endpoint
    - Parse response and map statuses
    - _Requirements: 1.4, 1.6, 1.9, 5.1_

  - [ ]* 5.6 Write integration tests for all Real Adapters (mocked HTTP)
    - Test valid identifier → VERIFIED
    - Test identifier not found → INCONCLUSIVE
    - Test invalid format → MISMATCH (or INCONCLUSIVE depending on API)
    - Test auth failure (401) → ERROR
    - Test rate limit (429) → ERROR
    - Test timeout scenario → UNAVAILABLE
    - Test name matching (exact, fuzzy, no match)
    - Test audit trail persistence for each adapter
    - _Requirements: 11.2-11.10_

  - [ ] 5.7 Checkpoint - Verify all adapter tests pass
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 6. Verification Service and Audit Trail Persistence
  - [ ] 6.1 Create VerificationService with verify_extracted_fact(extracted_fact_id) method
    - Query ExtractedFact to construct VerificationClaim
    - Call registry.get_adapter_for_field() to get appropriate adapter
    - Call adapter.verify() to perform verification
    - Create VerificationAttempt record (PENDING status at start)
    - Create VerificationResult record with returned status, http_code, api_reference_id, authority_value
    - Create VerificationNameMatch record if name matching performed
    - Return VerificationResult
    - _Requirements: 4.1-4.7, 4.9, 5.6_

  - [ ] 6.2 Implement Audit Trail Persistence (immutable append-only)
    - Ensure VerificationAttempt and VerificationResult records cannot be updated/deleted (application-level checks)
    - Every retry creates a new VerificationAttempt record with new verification_attempt_id
    - Store verification_attempt_id, extracted_value, source_document_id, request_timestamp, api_response_code, api_reference_id, authority_value, response_timestamp, verification_status
    - Do NOT store raw credentials, raw API request/response bodies, or authentication tokens
    - _Requirements: 4.1-4.9, 13.2_

  - [ ]* 6.3 Write property tests for audit trail
    - **Property 9: Audit Trail Immutability** — Records cannot be updated/deleted; each retry creates new record
    - **Property 14: Extracted Value Persistence in Audit Trail** — extracted_value field contains exact identifier sent to adapter; authority_value contains exact return from authority
    - **Property 15: Credential Values Never Logged or Persisted** — No raw API keys, passwords, or tokens in audit trail or logs
    - _Requirements: 4.5-4.9, 5.4-5.6_

- [ ] 7. Compliance Rule Integration
  - [ ] 7.1 Update Compliance_Rule_Engine to consume verification_status as discrete field (not boolean)
    - Modify rule evaluation to check for specific status values: VERIFIED, MISMATCH, UNAVAILABLE, ERROR, INCONCLUSIVE, PENDING
    - Implement rule deferral when status is PENDING
    - Implement policy handling for UNAVAILABLE and INCONCLUSIVE (pass, fail, or defer per configuration)
    - _Requirements: 10.1-10.3, 10.5_

  - [ ] 7.2 Update Evidence_Traceability system to include verification_status in evidence chain
    - Chain: document → extracted_fact → verification_result → compliance_rule_evaluation
    - Include verification_attempt_id in evidence chain for traceability
    - _Requirements: 10.6-10.8_

  - [ ]* 7.3 Write property test for compliance rule integration
    - **Property 12: Compliance Rule Defers on PENDING Status** — When verification_status is PENDING, rule evaluation returns NOT_EVALUATED
    - **Property 13: Error Status Never Implies Compliance Pass** — ERROR or UNAVAILABLE status never automatically PASSes compliance rule
    - _Requirements: 3.9, 10.3-10.4_

- [ ] 8. Checkpoint - Verify core verification logic
  - [ ] 8.1 Checkpoint - Run all verification and audit trail tests
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. UI Integration: Verification Status Display
  - [ ] 9.1 Create UI component: VerificationBadge
    - Accept verification_status as prop
    - Render appropriate badge with icon and color: VERIFIED (✓, green), MISMATCH (✕, red), UNAVAILABLE (⚠, gray), ERROR (✕, red), INCONCLUSIVE (◌, orange), PENDING (◷, blue)
    - Display verification provider name, timestamp, and reference_id on hover
    - Distinguish LIVE (Real_Adapter) from MOCK (Mock_Adapter fallback) with visual indicator
    - _Requirements: 9.1-9.9_

  - [ ] 9.2 Create UI component: VerificationDetailView
    - Triggered on click of VerificationBadge
    - Display: original_extracted_value, normalized_value, authority_returned_value, normalized_authority_value, match_result, match_score, verification_attempt_id
    - _Requirements: 9.10_

  - [ ] 9.3 Integrate VerificationBadge and VerificationDetailView into BidDocument view
    - Display badge next to each extracted identifier (GSTIN, CIN, PAN, NSIC, UDYAM)
    - Allow officer to click for details
    - _Requirements: 9.1_

  - [ ]* 9.4 Write unit tests for UI components
    - Test badge rendering for each status
    - Test hover tooltip display
    - Test detail view modal opening/closing
    - _Requirements: 9.1-9.10_

- [ ] 10. Observability and Logging
  - [ ] 10.1 Add structured logging throughout verification pipeline
    - INFO: Verification initiation (provider, extracted_value, verification_attempt_id)
    - INFO: Real_Adapter disabled (startup message)
    - WARN: Real_Adapter request failure (error_type, retry_count, elapsed_time)
    - WARN: API error response (http_status_code, error_message without credentials)
    - ERROR: All retries exhausted (final_error, total_elapsed_time)
    - DEBUG: Verification success (provider, status, match_result, elapsed_time)
    - Never log raw credentials, request bodies, or response bodies
    - _Requirements: 13.1-13.7_

  - [ ] 10.2 Add metrics collection
    - Track: verification_attempt_count (by provider), verification_success_rate (by provider), latency (p50, p95, p99), retry_count_distribution
    - _Requirements: 13.8_

- [ ] 11. Deployment Configuration
  - [ ] 11.1 Update application startup to log adapter registry status
    - List all adapters with enabled/disabled status
    - For disabled adapters, explain why (credential not set)
    - _Requirements: 12.1-12.3, 12.6-12.7_

  - [ ] 11.2 Document environment variable configuration
    - Create deployment guide showing: PAN_API_KEY, GSTIN_API_KEY, NSIC_API_KEY, UDYAM_API_KEY, MCA_API_KEY
    - Document fallback behavior when variables not set
    - _Requirements: 1.6, 5.1-5.8, 12.1-12.3, 12.5, 12.8_

  - [ ] 11.3 Support gradual adapter activation (mock-first deployment)
    - Deploy without environment variables → all Mock_Adapters used
    - Inject credentials later via environment variables → Real_Adapters activated
    - No code recompilation needed
    - _Requirements: 12.1-12.3, 12.5_

- [ ] 12. Compliance Rule Tests
  - [ ] 12.1 Write comprehensive compliance rule tests
    - Test rule evaluation with VERIFIED status → rule may pass/fail based on logic
    - Test rule evaluation with MISMATCH status → rule typically fails
    - Test rule evaluation with UNAVAILABLE status → rule defers/applies policy
    - Test rule evaluation with INCONCLUSIVE status → rule defers/applies policy
    - Test rule evaluation with PENDING status → rule defers immediately
    - Test rule evaluation with ERROR status → rule defers/applies policy (never auto-passes)
    - _Requirements: 10.1-10.8_

- [ ] 13. Checkpoint - Ensure all tests pass
  - [ ] 13.1 Final checkpoint - Run full test suite
    - Ensure all tests pass, ask the user if questions arise.

- [ ] 14. Integration Testing with Real API Mocks
  - [ ] 14.1 Create comprehensive mock fixtures for end-to-end testing
    - Mock all five government API responses (GSTN, MCA, NSIC, UDYAM, PAN)
    - Test complete verification flow: extract → claim → adapter → audit trail → rule evaluation
    - Test fallback scenarios: Real_Adapter timeout → Mock_Adapter activation
    - Test state machine transitions (PENDING → all six states)
    - _Requirements: 11.1-11.10_

  - [ ]* 14.2 Write property-based tests for complete verification workflow
    - Generate random identifiers, entity names, and adapter responses
    - Verify properties hold across all combinations
    - _Requirements: 11.2-11.10_

- [ ] 15. Final Integration and Deployment Readiness
  - [ ] 15.1 Verify system operates correctly with Mock_Adapters (development mode)
    - Deploy without real credentials
    - Confirm all mock fixtures return expected responses
    - Confirm audit trail records as expected
    - _Requirements: 2.1-2.7, 12.1_

  - [ ] 15.2 Create deployment checklist for credential injection
    - Ensure environment variables are set correctly in deployment environment
    - Verify Real_Adapters enabled in logs
    - Test end-to-end verification flow with real credentials (if available)
    - _Requirements: 12.1-12.8_

  - [ ] 15.3 Performance validation
    - Verify single verification request completes within 15 seconds (5s timeout + 2 retries with backoff)
    - Verify batch verification processes sequentially or with max 3 concurrent requests
    - _Requirements: 14.1, 14.2_

- [ ] 16. Final Checkpoint - All Requirements Covered
  - [ ] 16.1 Final checkpoint - Verify all 14 requirements covered
    - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP delivery. Test-related sub-tasks are marked optional; all core implementation tasks must be completed.
- Each task references specific requirements for traceability. All 14 requirements covered across implementation tasks.
- The Registry (task 4.2) is the single swap point where adapters are selected; no other file directly instantiates adapters.
- Mock Adapters remain unmodified and functional throughout; Real_Adapters are added alongside them.
- All 15 correctness properties are validated through property-based tests (marked as sub-tasks with `*`).
- Checkpoints (tasks 8.1, 13.1, 16.1) verify incremental progress before moving forward.

---

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1.1", "2.1", "3.1"]
    },
    {
      "id": 1,
      "tasks": ["1.2", "2.2", "2.3", "3.2", "3.3", "4.1"]
    },
    {
      "id": 2,
      "tasks": ["4.2", "4.3", "4.4", "5.1", "5.2", "5.3", "5.4", "5.5"]
    },
    {
      "id": 3,
      "tasks": ["5.6", "6.1", "6.2"]
    },
    {
      "id": 4,
      "tasks": ["6.3", "7.1", "7.2", "9.1"]
    },
    {
      "id": 5,
      "tasks": ["7.3", "9.2", "9.3", "10.1", "10.2"]
    },
    {
      "id": 6,
      "tasks": ["9.4", "11.1", "11.2", "11.3", "12.1"]
    },
    {
      "id": 7,
      "tasks": ["14.1", "14.2", "15.1", "15.2", "15.3"]
    }
  ]
}
```

---

## Execution Strategy

### Wave 0 (Foundation)
- Create base adapter class, name matching service, and database migration
- These are pure abstractions with no dependencies on external systems

### Wave 1 (Validation)
- Write property tests for base classes to ensure correctness properties hold
- Update database models with ORM definitions
- Preserve mock adapters

### Wave 2 (Adapter Registry)
- Create registry singleton that swaps between Real and Mock based on environment variables
- Implement all five Real_Adapter classes (GSTIN, MCA, PAN, NSIC, UDYAM)
- Each Real_Adapter is independent and can be tested in isolation

### Wave 3 (Verification Service)
- Build verification service layer that orchestrates adapter selection and audit trail persistence
- All adapter implementations complete before this

### Wave 4 (Audit & Compliance)
- Integrate with compliance rule engine to consume verification_status
- Update evidence traceability system
- Both depend on verification service being complete

### Wave 5 (UI & Observability)
- Create UI components for displaying verification status
- Add structured logging and metrics
- These depend on verification service being complete

### Wave 6 (Integration & Testing)
- Write comprehensive integration tests
- Deploy in mock-first mode for validation
- Prepare for credential injection

### Wave 7 (Final Validation)
- End-to-end testing with mock fixtures
- Performance validation
- Deployment readiness checklist
