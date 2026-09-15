# Requirements Document: Real Government Data Verification

## Introduction

This feature extends the GeM-Sentinel system to perform real-time verification of extracted government identifiers (GSTIN, CIN, NSIC, UDYAM, PAN) against authoritative government sources. The implementation maintains backward compatibility with mock adapters for testing and graceful fallback when live services are unavailable. Verification results inform compliance rules and provide audit trails for officer decision-making, enabling accurate identity and organization validation during the tender evaluation process.

---

## Glossary

- **Verification_Status**: One of six discrete states (VERIFIED, MISMATCH, UNAVAILABLE, ERROR, INCONCLUSIVE, PENDING) representing the outcome of an authoritative data check
- **Adapter**: A component that interfaces with a specific government data source (GSTIN, MCA/CIN, NSIC, UDYAM, or PAN)
- **Real_Adapter**: An adapter that makes live API calls to authoritative government sources
- **Mock_Adapter**: An adapter that returns deterministic hardcoded responses for testing and fallback
- **Registry**: The central component responsible for instantiating and selecting which adapter implementation to use
- **Authoritative_Source**: A government-operated system of record (GST portal, MCA, NSIC, UDYAM portal, PAN system)
- **Extracted_Value**: A government identifier (e.g., GSTIN, CIN) extracted from a tender document via OCR or manual input
- **Claim**: A statement that an extracted value matches the expected identifier for an entity
- **Verification_Request**: The process of querying an authoritative source to validate a claim
- **API_Response**: The structured data returned by an authoritative source after a verification request
- **Name_Normalization**: The deterministic process of transforming names to a canonical form (trim, lowercase, punctuation collapse)
- **Fuzzy_Match**: A probabilistic string comparison that assigns a similarity score between 0 and 1
- **Audit_Trail**: The immutable record of all verification requests, responses, and decisions stored in the database
- **Reference_ID**: A unique identifier provided by the authoritative source to trace a verification request for later inquiry
- **Credential**: Authentication material (API key, username, password) required to access an authoritative source
- **Graceful_Degradation**: The system's ability to continue functioning with reduced capability (mock fallback) when real services are unavailable
- **Environment_Variable**: A configuration parameter injected at deployment time, not hardcoded in the application

---

## Requirements

### Requirement 1: Real Adapter Implementation

**User Story:** As a compliance officer, I want real government data to be verified so that I can trust that extracted identifiers are authentic and match the records maintained by authorities.

#### Acceptance Criteria

1. THE Real_Adapter_Layer SHALL implement live verification for GSTIN via the GSTN API with the production endpoint
2. THE Real_Adapter_Layer SHALL implement live verification for CIN via the MCA portal with the production endpoint
3. THE Real_Adapter_Layer SHALL implement live verification for NSIC via the NSIC verification service with the production endpoint
4. THE Real_Adapter_Layer SHALL implement live verification for UDYAM via the UDYAM registration portal with the production endpoint
5. THE Real_Adapter_Layer SHALL implement live verification for PAN via the PAN verification service with the production endpoint
6. WHEN a Real_Adapter is instantiated, THE Adapter SHALL accept configuration via environment variables (PAN_API_KEY, GSTIN_API_KEY, NSIC_API_KEY, UDYAM_API_KEY, MCA_API_KEY)
7. WHEN a Real_Adapter is instantiated and the corresponding environment variable is not set, THE Adapter SHALL set its internal enabled flag to false and not attempt API calls
8. THE Real_Adapter_Layer SHALL inherit from a Base_Adapter abstract class defining verify() and status_map() methods
9. EACH Real_Adapter SHALL return a structured response object containing: extracted_value, authority_name, authority_value, match_result, match_score, reference_id, response_timestamp, http_status_code

---

### Requirement 2: Mock Adapter Preservation and Fallback

**User Story:** As a developer and tester, I want mock adapters to remain functional for testing and as a fallback so that the system gracefully degrades when live services are unavailable.

#### Acceptance Criteria

1. THE existing GSTNMockAdapter, MCAMockAdapter, NSICMockAdapter, UDYAMMockAdapter, and PANMockAdapter SHALL be retained without modification
2. THE Mock_Adapter implementations SHALL return deterministic responses matching their original behavior (e.g., valid GSTIN returns VERIFIED, invalid format returns MISMATCH)
3. WHEN a Real_Adapter is disabled (environment variable not set), THE Registry SHALL return the corresponding Mock_Adapter for that service
4. WHEN a Real_Adapter fails with a connection error, THE system SHALL log the error and fall back to the Mock_Adapter for that request
5. WHEN using a Mock_Adapter after real adapter failure, THE Verification_Status response SHALL include a flag indicating the result is from fallback
6. THE Mock_Adapter test fixtures SHALL cover valid identifiers, invalid format, timeout simulation, and auth failure scenarios
7. THE Registry SHALL be the only location where Adapter implementations are swapped

---

### Requirement 3: Verification Status State Machine

**User Story:** As a compliance rule evaluator, I want clear, discrete verification states so that I can apply consistent rules regardless of whether verification succeeded, failed, or could not be attempted.

#### Acceptance Criteria

1. THE Verification_Status field SHALL accept exactly six values: VERIFIED, MISMATCH, UNAVAILABLE, ERROR, INCONCLUSIVE, PENDING
2. WHEN an authoritative source confirms the extracted identifier matches its records, THE Verification_Status SHALL be set to VERIFIED
3. WHEN an authoritative source confirms the extracted identifier exists but the name does not match after normalization, THE Verification_Status SHALL be set to MISMATCH
4. WHEN an authoritative source is unreachable or credentials are not configured, THE Verification_Status SHALL be set to UNAVAILABLE
5. WHEN a verification request results in a technical failure (malformed response, timeout after retries, auth failure), THE Verification_Status SHALL be set to ERROR
6. WHEN an authoritative source confirms no record exists for the extracted identifier, THE Verification_Status SHALL be set to INCONCLUSIVE
7. WHEN a verification has not yet been performed for an extracted value, THE Verification_Status SHALL be set to PENDING
8. THE Verification_Status field SHALL not be a boolean; systems SHALL not conflate ERROR with FAIL or UNAVAILABLE with PASS
9. WHILE a Verification_Status is PENDING, THE system SHALL not apply compliance rules that depend on verification results

---

### Requirement 4: Audit Trail and Persistence

**User Story:** As an auditor, I want a complete record of every verification attempt so that I can trace how extracted values were validated and investigate discrepancies.

#### Acceptance Criteria

1. WHEN a verification request is initiated, THE system SHALL create an audit record in the VerificationAudit table containing: extracted_value, source_document_id, verification_provider, verification_request_timestamp
2. WHEN an authoritative source responds, THE system SHALL append to the audit record: api_response_code, api_reference_id, authority_extracted_value, authority_normalized_value, response_timestamp, verification_status
3. WHEN name matching occurs, THE system SHALL record in the audit trail: original_name, normalized_name, authority_name, normalized_authority_name, match_result, match_score
4. THE audit record SHALL include the http_status_code returned by the authoritative source (e.g., 200, 401, 429, 503)
5. THE audit trail SHALL be immutable; records SHALL not be updated or deleted after creation
6. THE audit record SHALL include a unique verification_attempt_id that can be referenced in compliance reports
7. WHEN a verification request is retried, THE system SHALL create a new audit record with a new verification_attempt_id
8. THE audit trail SHALL NOT store raw API credentials, raw request/response bodies, or sensitive authentication tokens
9. WHEN an officer views a verification result, THE UI SHALL display the verification_attempt_id enabling the officer to cross-reference logs

---

### Requirement 5: Credential Management

**User Story:** As a DevOps engineer, I want credentials to be injected at deployment time so that the application can be deployed securely without embedding secrets in the codebase.

#### Acceptance Criteria

1. THE system SHALL accept credentials via environment variables only: PAN_API_KEY, GSTIN_API_KEY, NSIC_API_KEY, UDYAM_API_KEY, MCA_API_KEY
2. WHEN an environment variable is not set, THE corresponding Real_Adapter SHALL not be enabled
3. IF a Real_Adapter receives a verification request but its credential is not set, THEN THE system SHALL log a warning and return UNAVAILABLE status
4. THE system SHALL NOT hardcode any API keys, usernames, passwords, or authentication tokens in source files
5. WHEN logging verification requests or responses, THE system SHALL never include the raw credential values
6. WHEN writing to the audit trail, THE system SHALL NOT include credential values; only reference_ids and status codes SHALL be persisted
7. WHEN a Real_Adapter reads credentials from environment variables, THE Adapter SHALL cache them in memory at startup, not re-read them per request
8. IF credential caching fails at startup, THEN THE system SHALL disable the Real_Adapter and log an error without failing the application startup

---

### Requirement 6: Timeout and Retry Logic

**User Story:** As a system operator, I want automatic retry and timeout handling so that transient network issues do not cause verification failures.

#### Acceptance Criteria

1. WHEN a verification request exceeds 5 seconds of elapsed time, THE system SHALL cancel the request and return UNAVAILABLE status
2. WHEN a verification request results in a network timeout or connection refused error, THE system SHALL retry up to 2 times with exponential backoff (base 1 second, max 8 seconds)
3. WHEN a verification request results in an HTTP 5xx response, THE system SHALL retry up to 2 times with exponential backoff
4. WHEN a verification request results in an HTTP 401 (unauthorized) response, THE system SHALL not retry and return ERROR status
5. WHEN a verification request results in an HTTP 429 (rate limit) response, THE system SHALL parse the Retry-After header if present and honor it, or wait 60 seconds before the next attempt
6. WHEN a rate limit response includes a Retry-After header, THE audit record SHALL include the retry-after value
7. WHEN all retry attempts are exhausted for a network error, THE system SHALL return UNAVAILABLE status
8. WHEN all retry attempts are exhausted for a 5xx error, THE system SHALL return UNAVAILABLE status
9. WHEN a timeout occurs during a verification attempt, THE system SHALL NOT convert the timeout to a MISMATCH status; UNAVAILABLE SHALL be used

---

### Requirement 7: Name Matching Logic

**User Story:** As a compliance officer, I want names to be matched deterministically so that minor formatting differences do not cause false mismatches.

#### Acceptance Criteria

1. WHEN comparing names from the extracted document and the authoritative source, THE system SHALL apply deterministic normalization: trim whitespace, lowercase all characters, and remove or collapse punctuation
2. THE normalization algorithm SHALL be specified in a standalone function that is pure and testable
3. WHEN normalized names are identical after normalization, THE match_result SHALL be set to "exact_match" and match_score SHALL be set to 1.0
4. WHEN normalized names differ, THE system SHALL optionally apply fuzzy matching (Jaro-Winkler or Levenshtein with threshold >= 0.85) to compute a match_score
5. IF fuzzy matching is enabled and the match_score is >= 0.85, THEN the match_result SHALL be set to "fuzzy_match"
6. IF fuzzy matching is enabled and the match_score is < 0.85, THEN the match_result SHALL be set to "no_match"
7. THE audit trail SHALL record: original_name (from document), normalized_name, authority_name (from API), normalized_authority_name, match_result, and match_score for every name comparison
8. WHEN Verification_Status is VERIFIED, the underlying name match_result SHALL be exact_match or fuzzy_match (depending on configuration)
9. WHEN Verification_Status is MISMATCH, the underlying name match_result SHALL be no_match or the authoritative source returned a mismatch flag

---

### Requirement 8: Error Handling and Status Mapping

**User Story:** As a system maintainer, I want errors to be handled consistently so that different failure modes are never conflated.

#### Acceptance Criteria

1. WHEN an API returns a 4xx response (other than 401 and 429), THE system SHALL map it to ERROR status
2. WHEN an API returns a 5xx response after all retries are exhausted, THE system SHALL map it to UNAVAILABLE status
3. WHEN an API returns a malformed or unparseable JSON response, THE system SHALL map it to ERROR status
4. WHEN network connectivity fails after all retries, THE system SHALL map it to UNAVAILABLE status
5. WHEN an API returns authentication failure (401), THE system SHALL map it to ERROR status and not retry
6. WHEN an authoritative source is rate-limited (429), THE system SHALL map it to ERROR status and not mark it as UNAVAILABLE
7. WHEN a timeout occurs during verification, THE system SHALL map it to UNAVAILABLE status, not ERROR
8. THE system SHALL NEVER automatically convert an API error response to a VERIFIED status
9. THE system SHALL NEVER automatically convert an API error response to a MISMATCH status; only explicit authority responses SHALL produce MISMATCH

---

### Requirement 9: UI Presentation of Verification Status

**User Story:** As a tender evaluation officer, I want clear visual indicators of verification status so that I can quickly assess the reliability of extracted identifiers.

#### Acceptance Criteria

1. WHEN an officer views a bid document in the UI, THE system SHALL display a verification badge next to each extracted identifier
2. WHEN Verification_Status is VERIFIED, THE badge SHALL display "✓ VERIFIED" with green background
3. WHEN Verification_Status is MISMATCH, THE badge SHALL display "✕ MISMATCH" with red background
4. WHEN Verification_Status is UNAVAILABLE, THE badge SHALL display "⚠ UNAVAILABLE" with gray background
5. WHEN Verification_Status is ERROR, THE badge SHALL display "✕ ERROR" with red background
6. WHEN Verification_Status is INCONCLUSIVE, THE badge SHALL display "◌ INCONCLUSIVE" with orange background
7. WHEN Verification_Status is PENDING, THE badge SHALL display "◷ PENDING" with blue background
8. WHEN an officer hovers over a verification badge, THE UI SHALL display: verification provider name, verification timestamp, and reference_id (if available)
9. THE UI SHALL visually distinguish LIVE verification (from Real_Adapter) from MOCK verification (from Mock_Adapter fallback)
10. WHEN an officer clicks on a verification badge, THE UI SHALL open a detailed view showing: original_extracted_value, normalized_value, authority_returned_value, normalized_authority_value, match_result, match_score, and verification_attempt_id

---

### Requirement 10: Integration with Compliance Rules

**User Story:** As a compliance rule author, I want verification status to be available as a discrete field so that I can write rules that depend on verification outcomes.

#### Acceptance Criteria

1. THE Compliance_Rule_Engine SHALL consume verification_status as a field in the evidence context, not as a boolean flag
2. WHEN a compliance rule references verification_status, THE rule SHALL be able to check for specific states (e.g., "WHEN verification_status == VERIFIED")
3. WHEN a compliance rule depends on verification but the Verification_Status is PENDING, THE system SHALL not evaluate the rule and defer the evaluation
4. WHEN a compliance rule depends on verification and Verification_Status is UNAVAILABLE, THE system SHALL apply the project's policy for handling unavailable services (pass, fail, or defer)
5. WHEN a compliance rule depends on verification and Verification_Status is INCONCLUSIVE, THE system SHALL apply the project's policy (pass, fail, or defer)
6. THE Evidence_Traceability system SHALL include verification_status in the evidence chain: document → extracted_fact → verification_result → compliance_rule_evaluation
7. WHEN an officer generates a compliance report, THE report SHALL indicate which facts were verified, which were not verified, and which are unavailable
8. WHEN a compliance rule fails because of an UNAVAILABLE verification status, THE system SHALL NOT record the rule failure without explicitly noting the verification unavailability

---

### Requirement 11: Testing and Fixtures

**User Story:** As a test engineer, I want comprehensive test fixtures so that I can verify adapter behavior without calling live APIs.

#### Acceptance Criteria

1. THE test suite SHALL include Mock_Adapter fixtures for: valid identifier (returns VERIFIED), invalid identifier (returns INCONCLUSIVE), format mismatch (returns MISMATCH), timeout scenario (simulates 6-second delay, returns UNAVAILABLE), and auth failure (simulates 401, returns ERROR)
2. THE Real_Adapter test suite SHALL NOT make live API calls; instead, SHALL mock the underlying HTTP client
3. THE Real_Adapter test suite SHALL verify that request payloads are correctly formed (required fields, correct format, valid headers)
4. THE Real_Adapter test suite SHALL verify that response parsing correctly handles the documented API response format
5. WHEN running the full test suite, NO environment variables for real credentials SHALL be set, ensuring only Mock_Adapters are used
6. THE test fixtures SHALL cover the state machine transitions: PENDING → VERIFIED, PENDING → MISMATCH, PENDING → UNAVAILABLE, PENDING → ERROR, PENDING → INCONCLUSIVE
7. THE test fixtures SHALL cover retry logic: network timeout → retry → retry → UNAVAILABLE
8. THE test fixtures SHALL cover rate limit handling: 429 response with Retry-After header → ERROR with retry-after recorded
9. THE test fixtures SHALL cover name matching: exact match, fuzzy match (if enabled), and no match scenarios
10. THE test suite SHALL verify that audit trail records are persisted correctly for each scenario

---

### Requirement 12: Deployment and Credential Injection

**User Story:** As a DevOps engineer, I want to deploy code with mock adapters first, then switch to real adapters by injecting credentials later without code changes.

#### Acceptance Criteria

1. WHEN the application is deployed without environment variables for real credentials, THE system SHALL use Mock_Adapters exclusively
2. WHEN the application is deployed with real credential environment variables set, THE system SHALL use Real_Adapters for those services
3. WHEN a Real_Adapter is enabled but no verified API endpoint is available, THE system SHALL disable the adapter and fall back to Mock_Adapter, logging a warning
4. THE Registry.py file SHALL be the only location where adapter implementations are selected; no other files SHALL directly instantiate adapters
5. WHEN switching from Mock to Real adapters (or vice versa) by changing environment variables, THE system SHALL NOT require code recompilation or restart (if possible in the deployment model)
6. THE application startup logs SHALL clearly indicate which adapters are enabled and which are using mocks
7. WHEN a Real_Adapter is disabled due to missing credentials, THE startup log SHALL note this with a clear message for the operator
8. THE system SHALL support a configuration file or environment variable to control which adapters are enabled at runtime

---

### Requirement 13: Logger and Observability

**User Story:** As a system operator, I want detailed logs and observability into verification processes so that I can debug integration issues and monitor adapter health.

#### Acceptance Criteria

1. WHEN a verification request is initiated, THE system SHALL log at INFO level: verification_provider, extracted_value, verification_attempt_id
2. WHEN a Real_Adapter is disabled (credential not set), THE system SHALL log at INFO level at startup
3. WHEN a Real_Adapter request fails, THE system SHALL log at WARN level: verification_provider, error_type, retry_count, elapsed_time
4. WHEN an API returns an error response, THE system SHALL log at WARN level: http_status_code, error_message (without credential values)
5. WHEN all retries are exhausted, THE system SHALL log at ERROR level: verification_provider, final_error, total_elapsed_time
6. WHEN a verification succeeds, THE system SHALL log at DEBUG level: verification_provider, verification_status, match_result, elapsed_time
7. THE system SHALL NOT log raw credentials, raw request bodies, or raw response bodies; only structural information and error messages SHALL be logged
8. WHEN metrics are collected, THE system SHALL track: verification_attempt_count (by provider), verification_success_rate (by provider), verification_latency_p50_p95_p99, retry_count_distribution

---

### Requirement 14: Non-Functional Requirements

**User Story:** As a system architect, I want performance, reliability, and maintainability so that the verification system scales and remains operational.

#### Acceptance Criteria

1. THE maximum latency for a single verification request (including retries) SHALL be 15 seconds (5s timeout + 2 retries with backoff)
2. WHEN conducting batch verification of multiple identifiers, THE system SHALL process them sequentially or with bounded parallelism (max 3 concurrent requests) to avoid overwhelming upstream APIs
3. THE Adapter interface SHALL be extensible to support adding new government data sources without modifying existing adapters
4. THE Real_Adapter implementations SHALL follow a consistent pattern for request building, response parsing, and error handling
5. THE code SHALL have unit test coverage >= 80% for adapter logic and compliance rule integration
6. THE system SHALL gracefully handle adapter initialization failures without crashing the application startup

---

## Constraints

- **Credential Availability**: Real credentials will be provided after development is complete; code must support running with mocks in the interim
- **Government API Stability**: Some government APIs may have varying uptime; the system must not fail catastrophically when upstream services are unavailable
- **Backward Compatibility**: Existing mock adapters must remain functional and unmodified; verification status changes must not break existing compliance rules
- **Authentication Mechanisms**: Each government service may have different authentication schemes (API key, OAuth, certificate-based); the system must abstract these details
- **Rate Limiting**: Government APIs may enforce rate limits; the system must respect Retry-After headers and implement exponential backoff
- **Name Formats**: Different government systems store names in different formats; deterministic normalization must be carefully designed to avoid false mismatches

---

## Assumptions

- Government APIs will return structured JSON or XML responses with documented formats
- API endpoints and authentication requirements are stable or provided by the government agencies
- The project will provide credentials via environment variables at deployment time
- The audit database has sufficient storage and query performance for the verification trail
- The compliance rule engine can consume discrete status values (not boolean flags)

