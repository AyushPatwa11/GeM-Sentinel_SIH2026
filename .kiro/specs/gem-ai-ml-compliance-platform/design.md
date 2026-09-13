# Design Document
## GeM AI/ML Based Bidder Compliance Verification Platform

**Feature Name:** gem-ai-ml-compliance-platform  
**Document Type:** Comprehensive Architecture & Design Specification  
**Status:** In Design Phase  
**Last Updated:** 2026-01-15

---

## Executive Summary

This document provides the complete architectural design for the GeM AI/ML Based Bidder Compliance Verification Platform, a 10-phase system that automates procurement compliance verification. The platform spans multiple architectural layers (Presentation, API Gateway, Application, AI/ML, Integration, Data) with integrated services for tender management, bid evaluation, compliance verification, risk assessment, and decision support.

The design emphasizes:
- **Separation of Concerns:** Distinct service layers for compliance, risk, verification, audit
- **Scalability:** Async processing, caching, batch operations for high-volume tenders
- **Auditability:** Immutable event logs, state history tracking, complete evidence traceability
- **Reliability:** Retry logic, fallback strategies, graceful error handling
- **Security:** Role-based access control, JWT authentication, input validation, data encryption

---

## 1. System Architecture

### 1.1 Layered Architecture

The platform is organized into six interconnected layers:

```
┌─────────────────────────────────────────────────┐
│  Presentation Layer (React Frontend)            │
│  - Officer Dashboard, Bidder Portal             │
│  - State management (Zustand/Redux)             │
│  - API client (axios/fetch)                     │
└────────────┬────────────────────────────────────┘
             │ HTTPS/REST
┌────────────▼────────────────────────────────────┐
│  API Gateway Layer (FastAPI)                    │
│  - Request routing, rate limiting               │
│  - JWT validation, CORS handling                │
│  - Request/response transformation              │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│  Application Layer                              │
│  - BidService, TenderService                    │
│  - ClarificationService, NotificationService    │
│  - OfficerDecisionService                       │
│  - Dependency injection, transaction management │
└────────────┬────────────────────────────────────┘
             │
┌────────┬───┴────┬──────────┬───────────┐
│        │        │          │           │
▼        ▼        ▼          ▼           ▼
┌──────┐┌──────┐┌────────┐┌────────┐┌─────────┐
│Risk  ││Audit ││Compliance││Evidence││Verification
│Service││Service││Orchestrator││Traceability││Orchestrator
└──────┘└──────┘└────────┘└────────┘└─────────┘
│  AI/ML Layer                                  │
│  - Risk scoring engine (scikit-learn models)  │
│  - ML model serving, feature extraction       │
│  - Recommendation engine                      │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│  Integration Layer                              │
│  - Adapter Pattern (GSTIN, PAN, MCA, etc.)    │
│  - Async HTTP clients, connection pooling      │
│  - Retry logic, circuit breakers, timeout      │
│  - OCR service client, document processing     │
└────────────┬────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────┐
│  Data Layer                                     │
│  - PostgreSQL (primary), Redis (cache)         │
│  - Connection pools, prepared statements       │
│  - Alembic migrations, schema versioning       │
│  - Audit triggers, immutable event store       │
└─────────────────────────────────────────────────┘
```

**Validates: Requirements 1.3 (database schema foundation), 2.1 (tender management)**

### 1.2 Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend (React)                           │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │Officer Dashboard│  │Bidder Portal │  │Audit Dashboard  │    │
│  └────────────────┘  └──────────────┘  └─────────────────┘    │
└──────────────┬──────────────────────────────────────────────────┘
               │
               ▼ REST API
┌──────────────────────────────────────────────────────────────────┐
│               FastAPI Gateway                                    │
│  - Router: /api/officer/*, /api/bidder/*, /api/admin/*         │
│  - Middleware: Auth, CORS, logging, rate limiting               │
└──────────┬──────────────────────────────────────────────────────┘
           │
    ┌──────┴──────┬────────────┬────────────┬─────────────┐
    │             │            │            │             │
    ▼             ▼            ▼            ▼             ▼
┌────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐  ┌──────────┐
│Tender  │  │Bid       │  │Document│  │Compliance│  │Officer   │
│Service │  │Service   │  │Service │  │Service   │  │Decision  │
│        │  │          │  │        │  │          │  │Service   │
└────────┘  └──────────┘  └────────┘  └──────────┘  └──────────┘
    │           │            │            │             │
    └───────────┴────────────┴────────────┴─────────────┘
                │
        ┌───────┴──────────┐
        │                  │
        ▼                  ▼
    ┌─────────────┐   ┌──────────────┐
    │PostgreSQL   │   │Redis Cache   │
    │(persistent) │   │(session/temp)│
    └─────────────┘   └──────────────┘
        │                  │
        └───────────┬──────┘
                    │
        ┌───────────┴───────────────┐
        │                           │
        ▼                           ▼
    ┌──────────────┐         ┌──────────────┐
    │Audit Log     │         │State History │
    │(immutable)   │         │(versioned)   │
    └──────────────┘         └──────────────┘
                    │
            ┌───────┴───────────┬─────────────┐
            │                   │             │
            ▼                   ▼             ▼
        ┌─────────┐      ┌──────────┐   ┌─────────┐
        │Adapter  │      │Risk      │   │Notification
        │Orch.    │      │Service   │   │Service
        └─────────┘      └──────────┘   └─────────┘
            │
        ┌───┴───┬────────┬────────┬─────────────┐
        │       │        │        │             │
        ▼       ▼        ▼        ▼             ▼
    ┌──────┐┌────┐┌──────┐┌──────┐┌──────────┐
    │GSTIN ││PAN ││MCA   ││NSIC  ││Udyam
    │API   ││API ││Portal││DB    ││Registry
    └──────┘└────┘└──────┘└──────┘└──────────┘
```

**Validates: Requirements 5.1 (multi-source verification), 2.1-2.3 (tender/bid management)**

### 1.3 Request/Response Flow

#### Bid Submission Flow
```
1. Bidder creates bid (POST /api/bidder/tenders/{tender_id}/bids)
   └─→ BidService.create_bid()
       └─→ Database: Insert Bid (status=DRAFT)
       └─→ AuditService.log(BID_CREATED)

2. Bidder uploads documents (POST /api/bidder/bids/{bid_id}/documents)
   └─→ DocumentService.upload()
       ├─→ File storage: Save file to /uploads/...
       ├─→ Document: Calculate SHA256 hash
       ├─→ Database: Insert Document (ocr_status=PENDING)
       └─→ OCRQueue: Enqueue OCRJob

3. Bidder verifies Stage 1 (POST /api/bidder/bids/{bid_id}/verify-stage1)
   └─→ DocumentService.validate_slots()
       ├─→ Query: SELECT COUNT(*) for each required doc_type
       └─→ Response: {passed: bool, slots: [...]}

4. Bidder verifies Stage 2 (POST /api/bidder/bids/{bid_id}/verify-stage2)
   └─→ ComplianceOrchestrator.evaluate()
       ├─→ Parallel: ComplianceService.evaluate_rule() × N
       ├─→ Parallel: AdapterOrchestrator.verify_multi_source()
       ├─→ RiskService.assess_risk()
       └─→ Response: {compliance_status, risk_level, signals: [...]}

5. Bidder submits bid (POST /api/bidder/bids/{bid_id}/submit)
   └─→ BidService.submit()
       ├─→ Database: Update Bid (status=SUBMITTED, submitted_at=now)
       ├─→ AuditService.log(BID_SUBMITTED)
       └─→ NotificationService.notify(bidder, "submitted")
```

**Validates: Requirements 2.3 (bid creation), 3.1-3.3 (document management), 4.2 (compliance evaluation)**

#### Verification Pipeline Flow
```
1. External Data Request (AdapterOrchestrator.verify_multi_source)
   ├─→ GSTIN Adapter (GST Registration Query)
   │   ├─→ Extract GSTIN from bid metadata
   │   ├─→ HTTP GET /api/gstin/{gstin}
   │   └─→ Store VerificationAttempt
   │
   ├─→ PAN Adapter (Income Tax Query)
   │   ├─→ Extract PAN from organization
   │   ├─→ HTTP GET /api/pan/{pan}
   │   └─→ Store VerificationAttempt
   │
   ├─→ MCA Adapter (Company House Query)
   │   ├─→ Extract CIN from organization
   │   ├─→ HTTP GET /api/mca/cin/{cin}
   │   └─→ Store VerificationAttempt
   │
   └─→ Udyam Adapter (MSME Query)
       ├─→ Extract Udyam number
       ├─→ HTTP GET /api/udyam/{udyam}
       └─→ Store VerificationAttempt

2. Name Matching (Entity Resolution)
   ├─→ Extract name variants:
   │   ├─→ Organization.legal_name
   │   ├─→ Extracted OCR name
   │   └─→ Bid state_metadata name
   │
   └─→ Comparison logic:
       ├─→ Exact match? → EntityResolutionResult (confidence=100)
       ├─→ Fuzzy match (Levenshtein) → Score [0-100]
       └─→ If < 95% → RiskSignal (name_mismatch, severity=MEDIUM)

3. Verification Aggregation
   ├─→ Collect all VerificationResult records
   ├─→ Aggregate source_verified counts
   ├─→ Set overall_verification_status:
   │   ├─→ VERIFIED: all critical sources passed
   │   ├─→ PARTIAL: some sources passed
   │   └─→ FAILED: critical sources failed
   └─→ Return summary to ComplianceService
```

**Validates: Requirements 5.1-5.4 (external verification), 5.3 (entity resolution)**

#### Risk Assessment Flow
```
1. Collect Risk Signals
   ├─→ ComplianceResult failures → RiskSignal (rule name, severity)
   ├─→ Verification mismatches → RiskSignal (type, severity)
   ├─→ Document anomalies → RiskSignal (ocr_failed, blacklist_hit)
   └─→ Entity resolution failures → RiskSignal (name_mismatch)

2. Calculate Risk Score
   ├─→ For each RiskSignal:
   │   └─→ score += signal_weight[signal_type] × (count + 1)
   │
   └─→ Cap score at 100 (sum of weights may exceed)

3. Determine Risk Level
   ├─→ IF score >= 70 → HIGH
   ├─→ IF 40 <= score < 70 → MEDIUM
   └─→ IF score < 40 → LOW

4. Generate Recommendation
   ├─→ IF compliance=COMPLIANT + risk=LOW → PROCEED_TO_SUBMISSION
   ├─→ IF compliance=COMPLIANT + risk=MEDIUM → PROCEED_WITH_CAUTION
   ├─→ IF compliance=COMPLIANT + risk=HIGH → MANUAL_REVIEW_REQUIRED
   └─→ IF compliance=NON_COMPLIANT → DO_NOT_PROCEED

5. Store RiskAssessment
   ├─→ Database: Insert RiskAssessment
   ├─→ AuditService.log(RISK_ASSESSED)
   └─→ NotifyOfficer (if risk=HIGH)
```

**Validates: Requirements 6.1-6.3 (risk assessment), 7.3 (AI recommendation)**

#### Officer Decision Flow
```
1. Officer views bid (GET /api/officer/bids/{bid_id})
   └─→ OfficerDecisionService.get_bid_detail()
       ├─→ Query: Bid + TenderVersion + Organization + Compliance + Risk
       ├─→ Query: All ComplianceResult records
       ├─→ Query: All RiskSignal records
       ├─→ Query: All VerificationResult records
       ├─→ Query: All ClarificationRequest records
       └─→ Response: {bidder, documents, compliance, risk, verification, clarifications, ai_recommendation}

2. Officer posts clarification (POST /api/officer/bids/{bid_id}/clarifications)
   └─→ ClarificationService.post_request()
       ├─→ Database: Insert ClarificationRequest (status=OPEN)
       ├─→ AuditService.log(CLARIFICATION_POSTED)
       └─→ NotificationService.notify_bidder(clarification)

3. Bidder responds (POST /api/bidder/bids/{bid_id}/clarifications/{request_id}/respond)
   └─→ ClarificationService.post_response()
       ├─→ Database: Insert ClarificationResponse
       ├─→ Database: Update ClarificationRequest (status=RESOLVED)
       ├─→ AuditService.log(CLARIFICATION_RESPONDED)
       └─→ NotificationService.notify_officer()

4. Officer makes decision (POST /api/officer/bids/{bid_id}/decision)
   └─→ OfficerDecisionService.make_decision()
       ├─→ Validate override_reason if decision != ai_recommendation
       ├─→ Database: Insert OfficerDecision
       ├─→ IF override → Insert OfficerDecisionOverride
       ├─→ IF risk=HIGH + override → Set requires_approval=true
       ├─→ Database: Update Bid (status=DECIDED, current_state=DECIDED)
       ├─→ AuditService.log(BID_DECIDED)
       └─→ NotificationService.notify_bidder(decision)
```

**Validates: Requirements 7.1-7.5 (officer decision), 8.1 (final decision)**

---

## 2. Database Design

### 2.1 Schema Overview

**Core Entity Relationships:**

```
Organization (1) ──── (many) User
           ├──────── (many) Bid (bidder_org_id)
           └──────── (many) Tender (org created_by)

Tender (1) ──────── (many) TenderVersion
       ├──────── (many) Bid (via TenderVersion)
       └──────── (many) Clause (tender requirements)

TenderVersion (1) ──────── (many) Bid

Bid (1) ──────── (many) Document
    ├──────── (many) ComplianceResult
    ├──────── (many) RiskSignal
    ├──────── (many) RiskAssessment
    ├──────── (many) VerificationResult
    ├──────── (many) VerificationAttempt
    ├──────── (many) OfficerDecision
    ├──────── (many) OfficerNote
    ├──────── (many) ClarificationRequest
    ├──────── (many) BidState
    └──────── (many) AuditEvent (entity_id)

Document (1) ──────── (many) DocumentVersion
         └──────── (many) ExtractedFact

ComplianceResult (1) ──────── (many) RiskSignal

OfficerDecision (1) ──────── (1) OfficerDecisionOverride
```

**Validates: Requirement 1.3 (database schema foundation)**

### 2.2 Table Definitions

#### Organizations & Users

```python
# Organization
class Organization(Base):
    __tablename__ = "organization"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    legal_name: str = Column(String(255), nullable=False)
    gstin: str = Column(String(15), unique=True, nullable=True, index=True)
    pan: str = Column(String(10), unique=True, nullable=True, index=True)
    cin: str = Column(String(21), unique=True, nullable=True)
    udyam_number: str = Column(String(12), unique=True, nullable=True)
    sector: str = Column(String(100), nullable=True)
    turnover: Decimal = Column(Numeric(15, 2), nullable=True)
    address: str = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    bids = relationship("Bid", foreign_keys="Bid.bidder_org_id", back_populates="bidder_org")

# User
class User(Base):
    __tablename__ = "user"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    email: str = Column(String(255), unique=True, nullable=False, index=True)
    password_hash: str = Column(String(255), nullable=False)  # Argon2
    role: str = Column(String(20), nullable=False)  # "officer" or "bidder"
    organization_id: UUID = Column(UUID, ForeignKey("organization.id"), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    audit_events = relationship("AuditEvent", foreign_keys="AuditEvent.actor_id")
```

**Validates: Requirements 1.1 (authentication), 1.2 (bidder association)**

#### Tender Management

```python
# Tender
class Tender(Base):
    __tablename__ = "tender"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    title: str = Column(String(500), nullable=False)
    status: str = Column(String(20), default="draft")  # draft|published|closed
    created_by: UUID = Column(UUID, ForeignKey("user.id"), nullable=False)
    organization_id: UUID = Column(UUID, ForeignKey("organization.id"), nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = relationship("TenderVersion", back_populates="tender", cascade="all, delete-orphan")

# TenderVersion
class TenderVersion(Base):
    __tablename__ = "tender_version"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    tender_id: UUID = Column(UUID, ForeignKey("tender.id"), nullable=False)
    version_number: str = Column(String(20), nullable=False)  # "1.0", "2.0"
    source_document_path: str = Column(String(500), nullable=True)
    published_at: datetime = Column(DateTime, nullable=True, index=True)
    precedence_policy_version: str = Column(String(50), nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    tender = relationship("Tender", back_populates="versions")
    bids = relationship("Bid", back_populates="tender_version")
```

**Validates: Requirements 2.1 (tender creation), 2.2 (tender discovery)**

#### Bid Management

```python
# Bid
class Bid(Base):
    __tablename__ = "bid"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    tender_version_id: UUID = Column(UUID, ForeignKey("tender_version.id"), nullable=False)
    bidder_org_id: UUID = Column(UUID, ForeignKey("organization.id"), nullable=False)
    status: str = Column(String(20), default="DRAFT")  # DRAFT|SUBMITTED|DECIDED
    current_state: str = Column(String(50), nullable=False, default="DRAFT")
    state_entered_at: datetime = Column(DateTime, default=datetime.utcnow)
    state_metadata: dict = Column(JSON, default={})
    submitted_at: datetime = Column(DateTime, nullable=True, index=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tender_version = relationship("TenderVersion", back_populates="bids")
    bidder_org = relationship("Organization", foreign_keys=[bidder_org_id])
    documents = relationship("Document", back_populates="bid", cascade="all, delete-orphan")
    compliance_results = relationship("ComplianceResult", back_populates="bid")
    risk_signals = relationship("RiskSignal", back_populates="bid")
    bid_states = relationship("BidState", back_populates="bid")

# BidState (State History)
class BidState(Base):
    __tablename__ = "bid_state"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False)
    state_exited: str = Column(String(50), nullable=True)
    state_entered: str = Column(String(50), nullable=False)
    exited_at: datetime = Column(DateTime, nullable=True)
    entered_at: datetime = Column(DateTime, default=datetime.utcnow)
    metadata: dict = Column(JSON, default={})
    
    # Relationships
    bid = relationship("Bid", back_populates="bid_states")
```

**Validates: Requirements 2.3 (bid creation), 10.2 (state history)**

#### Document Management

```python
# Document
class Document(Base):
    __tablename__ = "document"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False)
    doc_type: str = Column(String(50), nullable=False)  # GST_CERT, PAN, COI, etc.
    file_path: str = Column(String(500), nullable=False)
    file_hash: str = Column(String(64), nullable=False)  # SHA256
    ocr_status: str = Column(String(20), default="PENDING")  # PENDING|COMPLETED|FAILED
    current_version: int = Column(Integer, default=1)
    uploaded_at: datetime = Column(DateTime, default=datetime.utcnow)
    deleted: bool = Column(Boolean, default=False)  # Soft delete
    
    # Relationships
    bid = relationship("Bid", back_populates="documents")
    versions = relationship("DocumentVersion", cascade="all, delete-orphan")

# DocumentVersion
class DocumentVersion(Base):
    __tablename__ = "document_version"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    document_id: UUID = Column(UUID, ForeignKey("document.id"), nullable=False)
    version_number: int = Column(Integer, nullable=False)
    file_path: str = Column(String(500), nullable=False)
    file_hash: str = Column(String(64), nullable=False)
    ocr_status: str = Column(String(20), default="PENDING")
    extracted_text: str = Column(Text, nullable=True)
    uploaded_by: UUID = Column(UUID, ForeignKey("user.id"), nullable=True)
    uploaded_at: datetime = Column(DateTime, default=datetime.utcnow)
    change_reason: str = Column(String(500), nullable=True)
```

**Validates: Requirements 3.1-3.2 (document upload and versioning)**

#### Compliance & Risk

```python
# ComplianceResult
class ComplianceResult(Base):
    __tablename__ = "compliance_result"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False)
    rule_name: str = Column(String(100), nullable=False)
    rule_version: str = Column(String(20), nullable=False)  # e.g., "1.0"
    passed: bool = Column(Boolean, nullable=False)
    evidence_references: dict = Column(JSON, default=[])  # [{doc_id, fact_id}, ...]
    explanation: str = Column(Text, nullable=True)
    evaluated_at: datetime = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bid = relationship("Bid", back_populates="compliance_results")

# RiskSignal
class RiskSignal(Base):
    __tablename__ = "risk_signal"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False)
    signal_type: str = Column(String(100), nullable=False)
    severity: str = Column(String(20), nullable=False)  # HIGH|MEDIUM|LOW
    description: str = Column(Text, nullable=False)
    detected_at: datetime = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bid = relationship("Bid", back_populates="risk_signals")

# RiskAssessment
class RiskAssessment(Base):
    __tablename__ = "risk_assessment"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False, unique=True)
    overall_risk_score: float = Column(Float, nullable=False)  # 0-100
    risk_level: str = Column(String(20), nullable=False)  # LOW|MEDIUM|HIGH
    signal_breakdown: dict = Column(JSON)  # {high_count, medium_count, low_count}
    assessed_at: datetime = Column(DateTime, default=datetime.utcnow)
```

**Validates: Requirements 4.1-4.2 (compliance), 6.1-6.2 (risk assessment)**

#### Verification

```python
# VerificationResult
class VerificationResult(Base):
    __tablename__ = "verification_result"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False)
    source_name: str = Column(String(50), nullable=False)  # GSTIN|PAN|MCA|NSIC|Udyam
    verified: bool = Column(Boolean, nullable=False)
    details: dict = Column(JSON)  # {matched_name, status, matched_details}
    confidence_score: float = Column(Float, nullable=True)  # 0-100
    verified_at: datetime = Column(DateTime, default=datetime.utcnow)

# VerificationAttempt
class VerificationAttempt(Base):
    __tablename__ = "verification_attempt"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False)
    source_name: str = Column(String(50), nullable=False)
    query_data: dict = Column(JSON)
    result: dict = Column(JSON, nullable=True)
    success: bool = Column(Boolean, nullable=False)
    error_message: str = Column(Text, nullable=True)
    verified_at: datetime = Column(DateTime, default=datetime.utcnow)
    retry_count: int = Column(Integer, default=0)

# EntityResolutionResult
class EntityResolutionResult(Base):
    __tablename__ = "entity_resolution_result"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False)
    source1_name: str = Column(String(255), nullable=False)
    source2_name: str = Column(String(255), nullable=False)
    match_type: str = Column(String(20), nullable=False)  # exact|fuzzy
    confidence_score: float = Column(Float, nullable=False)
    resolved_legal_name: str = Column(String(255), nullable=False)
```

**Validates: Requirements 5.1-5.4 (external verification), 5.3 (entity resolution)**

#### Officer Decision

```python
# OfficerDecision
class OfficerDecision(Base):
    __tablename__ = "officer_decision"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False, unique=True)
    final_decision: str = Column(String(50), nullable=False)  # VERIFIED|NON_COMPLIANT|PENDING
    ai_recommendation: str = Column(String(100), nullable=False)
    decided_by: UUID = Column(UUID, ForeignKey("user.id"), nullable=False)
    decided_at: datetime = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    officer = relationship("User")

# OfficerDecisionOverride
class OfficerDecisionOverride(Base):
    __tablename__ = "officer_decision_override"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    decision_id: UUID = Column(UUID, ForeignKey("officer_decision.id"), nullable=False)
    override_reason: str = Column(Text, nullable=False)
    requires_approval: bool = Column(Boolean, default=False)
    status: str = Column(String(50), default="APPROVED")  # PENDING_APPROVAL|APPROVED|REJECTED
    approved_by: UUID = Column(UUID, ForeignKey("user.id"), nullable=True)
    approved_at: datetime = Column(DateTime, nullable=True)
```

**Validates: Requirements 8.1-8.2 (decision making)**

#### Clarifications

```python
# ClarificationRequest
class ClarificationRequest(Base):
    __tablename__ = "clarification_request"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=False)
    posted_by: UUID = Column(UUID, ForeignKey("user.id"), nullable=False)
    question_text: str = Column(Text, nullable=False)
    category: str = Column(String(50), nullable=False)
    status: str = Column(String(20), default="OPEN")  # OPEN|RESOLVED|REOPENED
    posted_at: datetime = Column(DateTime, default=datetime.utcnow)

# ClarificationResponse
class ClarificationResponse(Base):
    __tablename__ = "clarification_response"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    request_id: UUID = Column(UUID, ForeignKey("clarification_request.id"), nullable=False)
    response_text: str = Column(Text, nullable=False)
    responded_by: UUID = Column(UUID, ForeignKey("user.id"), nullable=False)
    responded_at: datetime = Column(DateTime, default=datetime.utcnow)
```

**Validates: Requirements 7.4 (clarification workflow)**

#### Audit & Notifications

```python
# AuditEvent
class AuditEvent(Base):
    __tablename__ = "audit_event"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    event_type: str = Column(String(100), nullable=False, index=True)
    actor_id: UUID = Column(UUID, ForeignKey("user.id"), nullable=True)
    actor_role: str = Column(String(50), nullable=True)
    entity_type: str = Column(String(100), nullable=False)
    entity_id: UUID = Column(UUID, nullable=False)
    details: dict = Column(JSON)
    timestamp: datetime = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address: str = Column(String(50), nullable=True)

# Notification
class Notification(Base):
    __tablename__ = "notification"
    
    id: UUID = Column(UUID, primary_key=True, default=uuid4)
    user_id: UUID = Column(UUID, ForeignKey("user.id"), nullable=False)
    notification_type: str = Column(String(50), nullable=False)
    bid_id: UUID = Column(UUID, ForeignKey("bid.id"), nullable=True)
    message_template: str = Column(String(500), nullable=False)
    context_data: dict = Column(JSON)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    sent_at: datetime = Column(DateTime, nullable=True)
    read_at: datetime = Column(DateTime, nullable=True)
```

**Validates: Requirements 10.1 (audit trail), 9.2 (notifications)**

### 2.3 Indexing Strategy

```sql
-- Performance indexes (HIGH priority)
CREATE INDEX idx_bid_status ON bid(status);
CREATE INDEX idx_bid_current_state ON bid(current_state);
CREATE INDEX idx_bid_submitted_at ON bid(submitted_at);
CREATE INDEX idx_tender_status ON tender(status);
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_organization_gstin ON organization(gstin);
CREATE INDEX idx_organization_pan ON organization(pan);

-- Composite indexes (MEDIUM priority)
CREATE INDEX idx_bid_tender_bidder ON bid(tender_version_id, bidder_org_id);
CREATE INDEX idx_compliance_bid_rule ON compliance_result(bid_id, rule_name);
CREATE INDEX idx_risk_signal_bid_type ON risk_signal(bid_id, signal_type);

-- Audit & History indexes (for queries)
CREATE INDEX idx_audit_event_timestamp ON audit_event(timestamp);
CREATE INDEX idx_audit_event_entity ON audit_event(entity_type, entity_id);
CREATE INDEX idx_bid_state_bid_entered ON bid_state(bid_id, entered_at);
```

**Validates: Requirement 1.3 (indexing strategy)**

### 2.4 Migration Strategy (Alembic)

```python
# alembic/versions/0001_initial_schema.py
def upgrade():
    # Create tables in dependency order
    op.create_table('organization', ...)
    op.create_table('user', ...)
    op.create_table('tender', ...)
    op.create_table('tender_version', ...)
    op.create_table('bid', ...)
    op.create_table('document', ...)
    # ... other tables
    
    # Create indexes
    op.create_index('idx_user_email', 'user', ['email'])
    # ... other indexes
    
    # Create foreign keys
    op.create_foreign_key('fk_bid_tender_version', 'bid', 'tender_version', 
                         ['tender_version_id'], ['id'])
    # ... other FKs

def downgrade():
    # Drop in reverse dependency order
    op.drop_table('audit_event')
    # ... drop other tables
```

Migration commands:
```bash
# Create migration (auto-detect model changes)
alembic revision --autogenerate -m "Add new column to bids"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade ae1027a6acf
```

**Validates: Requirement 1.3 (database schema), 11 (deployment strategy)**

---

## 3. Backend Services Architecture

### 3.1 Service Layer Organization

```
Services/
├── BidService (Bid CRUD, state management)
├── TenderService (Tender CRUD, versioning)
├── DocumentService (Document upload, versioning)
├── ComplianceService (Rule evaluation)
├── RiskService (Risk scoring, aggregation)
├── ClarificationService (Clarification workflow)
├── OfficerDecisionService (Decision making, auditing)
├── AdapterOrchestrator (External data queries)
├── NotificationService (Email/in-app notifications)
├── AuditService (Event logging)
├── EvidenceTraceability (Evidence mapping)
└── OCRService (Document processing)
```

### 3.2 Service Interfaces & Dependencies

#### BidService

```python
class BidService:
    """Bid CRUD and state management."""
    
    def __init__(self, db: Database, audit_service: AuditService):
        self.db = db
        self.audit_service = audit_service
    
    async def create_bid(self, tender_id: UUID, bidder_org_id: UUID) -> Bid:
        """Create a new bid in DRAFT state."""
        tender_version = await self.db.query(TenderVersion)\
            .filter(TenderVersion.tender_id == tender_id)\
            .order_by(TenderVersion.published_at.desc())\
            .first()
        
        bid = Bid(
            tender_version_id=tender_version.id,
            bidder_org_id=bidder_org_id,
            status="DRAFT",
            current_state="DRAFT",
            state_entered_at=datetime.utcnow()
        )
        
        self.db.add(bid)
        await self.db.commit()
        
        # Audit
        await self.audit_service.log(
            event_type="BID_CREATED",
            entity_type="Bid",
            entity_id=bid.id,
            details={"tender_id": tender_id, "bidder_org_id": bidder_org_id}
        )
        
        return bid
    
    async def submit_bid(self, bid_id: UUID) -> Bid:
        """Transition bid from DRAFT to SUBMITTED."""
        bid = await self.db.query(Bid).filter(Bid.id == bid_id).first()
        
        # Validation: All required documents uploaded
        doc_count = await self.db.query(Document)\
            .filter(Document.bid_id == bid_id, Document.deleted == False)\
            .count()
        if doc_count == 0:
            raise ValidationError("No documents uploaded")
        
        # State transition
        bid.status = "SUBMITTED"
        bid.current_state = "SUBMITTED"
        bid.state_entered_at = datetime.utcnow()
        bid.submitted_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Log state transition
        await self._log_state_transition(bid_id, "DRAFT", "SUBMITTED")
        await self.audit_service.log(
            event_type="BID_SUBMITTED",
            entity_type="Bid",
            entity_id=bid_id
        )
        
        return bid
```

**Validates: Requirements 2.3 (bid creation), 10.2 (state history)**

#### ComplianceService

```python
class ComplianceService:
    """Compliance rule evaluation and aggregation."""
    
    def __init__(self, db: Database, adapter_orch: AdapterOrchestrator,
                 evidence_service: EvidenceTraceability, audit_service: AuditService):
        self.db = db
        self.adapter_orch = adapter_orch
        self.evidence_service = evidence_service
        self.audit_service = audit_service
        
        # Load compliance rule definitions
        self.rules = self._load_rules()
    
    async def evaluate_all_rules(self, bid_id: UUID) -> ComplianceEvaluation:
        """Evaluate all compliance rules for a bid."""
        bid = await self.db.query(Bid).filter(Bid.id == bid_id).first()
        organization = await self.db.query(Organization)\
            .filter(Organization.id == bid.bidder_org_id).first()
        
        results = []
        risk_signals = []
        
        # Execute rules in parallel
        tasks = [
            self.evaluate_rule(bid_id, rule_name, rule_def)
            for rule_name, rule_def in self.rules.items()
        ]
        
        compliance_results = await asyncio.gather(*tasks)
        
        for result in compliance_results:
            await self.db.add(result)
            results.append(result)
            
            # Generate risk signal if failed
            if not result.passed:
                signal = RiskSignal(
                    bid_id=bid_id,
                    signal_type=result.rule_name,
                    severity=self._get_severity(result.rule_name),
                    description=result.explanation,
                    detected_at=datetime.utcnow()
                )
                await self.db.add(signal)
                risk_signals.append(signal)
        
        await self.db.commit()
        
        # Aggregate compliance status
        all_passed = all(r.passed for r in results)
        compliance_status = "COMPLIANT" if all_passed else "NON_COMPLIANT"
        
        # Audit
        await self.audit_service.log(
            event_type="COMPLIANCE_EVALUATED",
            entity_type="Bid",
            entity_id=bid_id,
            details={"compliance_status": compliance_status, "rules_evaluated": len(results)}
        )
        
        return ComplianceEvaluation(
            bid_id=bid_id,
            results=results,
            compliance_status=compliance_status,
            risk_signals=risk_signals
        )
    
    async def evaluate_rule(self, bid_id: UUID, rule_name: str, rule_def: dict) -> ComplianceResult:
        """Evaluate a single compliance rule."""
        if rule_name == "gstin_valid":
            return await self._evaluate_gstin_valid(bid_id, rule_def)
        elif rule_name == "name_consistency":
            return await self._evaluate_name_consistency(bid_id, rule_def)
        # ... other rules
```

**Validates: Requirements 4.1-4.3 (compliance engine)**

#### RiskService

```python
class RiskService:
    """Risk assessment and scoring."""
    
    # Risk weights for each signal type
    SIGNAL_WEIGHTS = {
        "gstin_invalid": 25,
        "pan_invalid": 20,
        "name_mismatch": 15,
        "duplicate_bidder": 40,
        "blacklisted": 50,
        "unverified_source": 10,
        "financial_threshold_miss": 20,
    }
    
    def __init__(self, db: Database, audit_service: AuditService):
        self.db = db
        self.audit_service = audit_service
    
    async def assess_risk(self, bid_id: UUID) -> RiskAssessment:
        """Calculate risk score and level for a bid."""
        
        # Collect all risk signals for the bid
        signals = await self.db.query(RiskSignal)\
            .filter(RiskSignal.bid_id == bid_id)\
            .all()
        
        # Count signals by severity
        signal_breakdown = {
            "high_count": len([s for s in signals if s.severity == "HIGH"]),
            "medium_count": len([s for s in signals if s.severity == "MEDIUM"]),
            "low_count": len([s for s in signals if s.severity == "LOW"]),
        }
        
        # Calculate overall score
        overall_risk_score = self._calculate_risk_score(signals)
        
        # Determine risk level
        risk_level = self._determine_risk_level(overall_risk_score, signal_breakdown)
        
        # Create assessment
        assessment = RiskAssessment(
            bid_id=bid_id,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            signal_breakdown=signal_breakdown,
            assessed_at=datetime.utcnow()
        )
        
        self.db.add(assessment)
        await self.db.commit()
        
        await self.audit_service.log(
            event_type="RISK_ASSESSED",
            entity_type="Bid",
            entity_id=bid_id,
            details={"risk_level": risk_level, "score": overall_risk_score}
        )
        
        return assessment
    
    def _calculate_risk_score(self, signals: List[RiskSignal]) -> float:
        """Calculate overall risk score from signals."""
        score = 0.0
        signal_counts = {}
        
        for signal in signals:
            signal_counts[signal.signal_type] = signal_counts.get(signal.signal_type, 0) + 1
        
        for signal_type, count in signal_counts.items():
            weight = self.SIGNAL_WEIGHTS.get(signal_type, 5)
            score += weight * (count + 1)  # Weight increases with multiple signals
        
        return min(score, 100)  # Cap at 100
    
    def _determine_risk_level(self, score: float, breakdown: dict) -> str:
        """Determine risk level from score and breakdown."""
        if breakdown["high_count"] >= 1:
            return "HIGH"
        elif breakdown["medium_count"] >= 2 and breakdown["high_count"] == 0:
            return "MEDIUM"
        elif breakdown["low_count"] >= 3 and breakdown["medium_count"] <= 1:
            return "MEDIUM"
        else:
            return "LOW"
```

**Validates: Requirements 6.1-6.2 (risk assessment)**

#### AdapterOrchestrator

```python
class AdapterOrchestrator:
    """Coordinate external data source queries in parallel."""
    
    def __init__(self, adapters: Dict[str, Adapter], db: Database,
                 audit_service: AuditService, config: Config):
        self.adapters = adapters  # {source_name: adapter_instance}
        self.db = db
        self.audit_service = audit_service
        self.config = config
        self.max_retries = 3
        self.retry_delays = [1, 2, 4]  # Exponential backoff in seconds
    
    async def verify_multi_source(self, bid_id: UUID, sources: List[str]) -> VerificationSummary:
        """Query multiple sources in parallel."""
        
        bid = await self.db.query(Bid).filter(Bid.id == bid_id).first()
        organization = bid.bidder_org  # Lazy-loaded via relationship
        
        # Prepare query tasks for each source
        tasks = [
            self._verify_source_with_retry(bid_id, source, organization)
            for source in sources
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        verification_results = []
        failed_sources = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_sources.append(sources[i])
            else:
                verification_results.append(result)
        
        # Aggregate summary
        summary = VerificationSummary(
            bid_id=bid_id,
            total_sources_queried=len(sources),
            sources_verified=len(verification_results),
            sources_failed=len(failed_sources),
            overall_verification_status=self._determine_status(
                verification_results, failed_sources, sources
            ),
            results=verification_results
        )
        
        await self.audit_service.log(
            event_type="VERIFICATION_EXECUTED",
            entity_type="Bid",
            entity_id=bid_id,
            details={
                "sources": sources,
                "verified": len(verification_results),
                "failed": len(failed_sources)
            }
        )
        
        return summary
    
    async def _verify_source_with_retry(self, bid_id: UUID, source_name: str,
                                       organization: Organization) -> VerificationResult:
        """Query a source with retry logic and exponential backoff."""
        
        for attempt in range(self.max_retries):
            try:
                adapter = self.adapters.get(source_name)
                if not adapter:
                    raise ValueError(f"No adapter for source {source_name}")
                
                # Execute query
                result = await adapter.query(organization)
                
                # Store successful attempt
                attempt_record = VerificationAttempt(
                    bid_id=bid_id,
                    source_name=source_name,
                    query_data={
                        "gstin": organization.gstin,
                        "pan": organization.pan,
                        "cin": organization.cin,
                    },
                    result=result.to_dict(),
                    success=True,
                    retry_count=attempt
                )
                self.db.add(attempt_record)
                await self.db.commit()
                
                return VerificationResult(
                    bid_id=bid_id,
                    source_name=source_name,
                    verified=result.verified,
                    details=result.details,
                    confidence_score=result.confidence
                )
                
            except Exception as e:
                if attempt < self.max_retries - 1:
                    # Retry with exponential backoff
                    await asyncio.sleep(self.retry_delays[attempt])
                else:
                    # Final attempt failed, store failure record
                    attempt_record = VerificationAttempt(
                        bid_id=bid_id,
                        source_name=source_name,
                        query_data={...},
                        result=None,
                        success=False,
                        error_message=str(e),
                        retry_count=attempt
                    )
                    self.db.add(attempt_record)
                    await self.db.commit()
                    
                    raise  # Re-raise to gather() to handle in calling function
```

**Validates: Requirements 5.1-5.2 (external verification), 7 (scalability)**

### 3.3 Dependency Injection & Service Factory

```python
# services/service_factory.py
class ServiceFactory:
    """Factory for creating service instances with dependencies."""
    
    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self._services = {}
    
    def get_audit_service(self) -> AuditService:
        if "audit_service" not in self._services:
            self._services["audit_service"] = AuditService(self.db)
        return self._services["audit_service"]
    
    def get_bid_service(self) -> BidService:
        if "bid_service" not in self._services:
            self._services["bid_service"] = BidService(
                self.db,
                audit_service=self.get_audit_service()
            )
        return self._services["bid_service"]
    
    def get_compliance_service(self) -> ComplianceService:
        if "compliance_service" not in self._services:
            self._services["compliance_service"] = ComplianceService(
                self.db,
                adapter_orch=self.get_adapter_orchestrator(),
                evidence_service=self.get_evidence_service(),
                audit_service=self.get_audit_service()
            )
        return self._services["compliance_service"]
    
    def get_risk_service(self) -> RiskService:
        if "risk_service" not in self._services:
            self._services["risk_service"] = RiskService(
                self.db,
                audit_service=self.get_audit_service()
            )
        return self._services["risk_service"]
    
    def get_adapter_orchestrator(self) -> AdapterOrchestrator:
        if "adapter_orch" not in self._services:
            adapters = {
                "GSTIN": GSTINAdapter(self.config),
                "PAN": PANAdapter(self.config),
                "MCA": MCAAdapter(self.config),
                "NSIC": NSICAdapter(self.config),
                "Udyam": UdyamAdapter(self.config),
            }
            self._services["adapter_orch"] = AdapterOrchestrator(
                adapters=adapters,
                db=self.db,
                audit_service=self.get_audit_service(),
                config=self.config
            )
        return self._services["adapter_orch"]
    
    def get_notification_service(self) -> NotificationService:
        if "notification_service" not in self._services:
            self._services["notification_service"] = NotificationService(
                db=self.db,
                email_client=EmailClient(self.config),
                audit_service=self.get_audit_service()
            )
        return self._services["notification_service"]
```

### 3.4 Async Patterns & Event Handling

```python
# Async request handling
class BidController:
    def __init__(self, service_factory: ServiceFactory):
        self.factory = service_factory
    
    @app.post("/api/bidder/bids/{bid_id}/verify-stage2")
    async def verify_stage2(self, bid_id: UUID, current_user: User = Depends(get_current_user)):
        """Verify compliance for a bid (async)."""
        
        # Dispatch to background task queue
        task_id = await queue.enqueue(
            task_name="compliance.evaluate_all_rules",
            bid_id=bid_id,
            user_id=current_user.id
        )
        
        # Return immediately with task status
        return {
            "status": "IN_PROGRESS",
            "task_id": task_id,
            "message": "Compliance evaluation started"
        }
    
    @app.get("/api/bidder/bids/{bid_id}/verify-stage2/status/{task_id}")
    async def check_verification_status(self, bid_id: UUID, task_id: str):
        """Poll for verification status."""
        
        task_status = await queue.get_status(task_id)
        
        if task_status.status == "COMPLETED":
            # Fetch results from database
            compliance = await self.factory.get_compliance_service()\
                .get_evaluation_results(bid_id)
            return {
                "status": "COMPLETED",
                "compliance_status": compliance.compliance_status,
                "results": compliance.results
            }
        elif task_status.status == "FAILED":
            return {
                "status": "FAILED",
                "error": task_status.error_message
            }
        else:
            return {
                "status": "IN_PROGRESS",
                "progress": f"Evaluating rule {task_status.current_step}/{task_status.total_steps}"
            }

# Background task worker
async def evaluate_compliance_task(bid_id: UUID, user_id: UUID):
    """Long-running compliance evaluation (runs in worker process)."""
    
    try:
        service_factory = ServiceFactory(db, config)
        compliance_service = service_factory.get_compliance_service()
        risk_service = service_factory.get_risk_service()
        
        # Evaluate compliance
        evaluation = await compliance_service.evaluate_all_rules(bid_id)
        
        # Assess risk
        risk_assessment = await risk_service.assess_risk(bid_id)
        
        # Generate AI recommendation
        recommendation = generate_recommendation(
            evaluation.compliance_status,
            risk_assessment.risk_level
        )
        
        # Persist recommendation
        await db.query(Bid)\
            .filter(Bid.id == bid_id)\
            .update({"ai_recommendation": recommendation})
        await db.commit()
        
    except Exception as e:
        logger.error(f"Compliance evaluation failed for bid {bid_id}: {e}")
        raise
```

**Validates: Requirements 4.2 (compliance evaluation), 7 (scalability with async)**

---

## 4. Frontend Architecture

### 4.1 Component Hierarchy

```
App.tsx (Root)
├── Routes
│   ├── /login → LoginPage
│   ├── /officer/* (Protected by OfficerGuard)
│   │   ├── /dashboard → OfficerDashboard
│   │   │   ├── BidsList (with sorting/filtering)
│   │   │   ├── RiskSummary
│   │   │   └── TenderMetrics
│   │   │
│   │   ├── /tenders → OfficerTenderManagement
│   │   │   ├── TenderCreateForm
│   │   │   ├── TenderList
│   │   │   └── TenderVersionHistor


---

## 4. Frontend Architecture (Continued)

### 4.1 Component Hierarchy (Continued)

```
App.tsx (Root)
├── Routes
│   ├── /login → LoginPage
│   │   ├── EmailInput
│   │   └── PasswordInput
│   │
│   ├── /officer/* (Protected by OfficerGuard)
│   │   ├── /dashboard → OfficerDashboard
│   │   │   ├── BidsList (sortable, filterable)
│   │   │   │   ├── BidCard (risk badge, compliance status)
│   │   │   │   └── RiskFilter
│   │   │   └── MetricsSummary
│   │   │
│   │   ├── /bids/{bid_id} → BidDetailView
│   │   │   ├── BidderInfo (org details, documents)
│   │   │   ├── ComplianceTab (results, evidence)
│   │   │   ├── RiskTab (signals, breakdown)
│   │   │   ├── VerificationTab (sources, results)
│   │   │   ├── ClarificationTab (requests, responses)
│   │   │   └── DecisionPanel (recommendation, decision form)
│   │   │
│   │   ├── /bids/{bid_id}/audit → BidAuditTrail
│   │   │   └── EventTimeline
│   │   │
│   │   └── /tenders → OfficerTenderManagement
│   │       ├── TenderCreateForm
│   │       ├── TenderList
│   │       └── TenderPublishDialog
│   │
│   └── /bidder/* (Protected by BidderGuard)
│       ├── /tenders → BidderTendersDiscovery
│       │   ├── TenderSearchBar
│       │   ├── TenderFilters
│       │   └── TenderCards (browse public list)
│       │
│       ├── /bids → BidderBidsManagement
│       │   └── BidStatusCard[] (with readiness %)
│       │
│       ├── /bids/{bid_id}/submit → BidSubmissionFlow
│       │   ├── Stage1_DocumentCheck
│       │   │   └── DocumentUploadZone[] (by type)
│       │   ├── Stage2_Verification
│       │   │   └── VerificationProgressBar
│       │   ├── Stage3_ComplianceReview
│       │   │   └── ReadinessGauge
│       │   └── Stage4_Submit (confirm button)
│       │
│       ├── /bids/{bid_id}/status → BidStatusMonitor
│       │   ├── StateIndicator (current state)
│       │   ├── ClarificationPending[] (if any)
│       │   └── DecisionDisplay (if decided)
│       │
│       └── /clarifications → ClarificationResponder
│           └── ClarificationRequestCard[] (Q&A)
```

**Validates: Requirements 2.2 (tender discovery), 7.1-7.2 (officer dashboard)**

### 4.2 State Management (Zustand Store)

```typescript
// stores/authStore.ts
import { create } from 'zustand';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  isAuthenticated: !!localStorage.getItem('token'),
  
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    const { access_token, user } = response.data;
    
    localStorage.setItem('token', access_token);
    set({ user, token: access_token, isAuthenticated: true });
  },
  
  logout: () => {
    localStorage.removeItem('token');
    set({ user: null, token: null, isAuthenticated: false });
  },
  
  setUser: (user: User) => set({ user }),
}));

// stores/bidStore.ts
interface BidState {
  currentBid: Bid | null;
  bids: Bid[];
  complianceResults: ComplianceResult[];
  riskAssessment: RiskAssessment | null;
  verificationResults: VerificationResult[];
  
  fetchBid: (bid_id: UUID) => Promise<void>;
  evaluateCompliance: (bid_id: UUID) => Promise<void>;
  submitBid: (bid_id: UUID) => Promise<void>;
}

export const useBidStore = create<BidState>((set, get) => ({
  currentBid: null,
  bids: [],
  complianceResults: [],
  riskAssessment: null,
  verificationResults: [],
  
  fetchBid: async (bid_id: UUID) => {
    const response = await api.get(`/officer/bids/${bid_id}`);
    const bid = response.data;
    set({
      currentBid: bid,
      complianceResults: bid.compliance_results || [],
      riskAssessment: bid.risk_assessment || null,
      verificationResults: bid.verification_results || [],
    });
  },
  
  evaluateCompliance: async (bid_id: UUID) => {
    // Enqueue task and poll for status
    const taskId = (await api.post(`/bidder/bids/${bid_id}/verify-stage2`)).data.task_id;
    
    // Poll until complete
    while (true) {
      const status = await api.get(`/bidder/bids/${bid_id}/verify-stage2/status/${taskId}`);
      if (status.data.status === 'COMPLETED') {
        set({
          complianceResults: status.data.results,
          riskAssessment: status.data.risk_assessment,
        });
        break;
      } else if (status.data.status === 'FAILED') {
        throw new Error(status.data.error);
      }
      await new Promise(resolve => setTimeout(resolve, 2000));  // Poll every 2 seconds
    }
  },
  
  submitBid: async (bid_id: UUID) => {
    const response = await api.post(`/bidder/bids/${bid_id}/submit`);
    set({ currentBid: response.data });
  },
}));
```

**Validates: Requirements 7.1 (bid dashboard), 9.1 (bid status updates)**

### 4.3 API Client & Interceptors

```typescript
// api/client.ts
import axios, { AxiosInstance } from 'axios';
import { useAuthStore } from '../stores/authStore';

const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL,
  timeout: 30000,
});

// Request interceptor: Add JWT token
apiClient.interceptors.request.use((config) => {
  const { token } = useAuthStore.getState();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

**Validates: Requirements 1.1 (JWT authentication)**

### 4.4 Key Components

#### OfficerDashboard

```typescript
// pages/OfficerDashboard.tsx
const OfficerDashboard: React.FC = () => {
  const [bids, setBids] = useState<Bid[]>([]);
  const [filter, setFilter] = useState({ risk_level: null, status: null });
  const [sortBy, setSortBy] = useState('risk_level_desc');

  useEffect(() => {
    fetchBids();
  }, [filter, sortBy]);

  const fetchBids = async () => {
    try {
      const response = await apiClient.get('/officer/bids', {
        params: {
          risk_level: filter.risk_level,
          status: filter.status,
          sort_by: sortBy,
        },
      });
      setBids(response.data.bids);
    } catch (error) {
      toast.error('Failed to fetch bids');
    }
  };

  return (
    <div className="dashboard">
      <h1>Officer Dashboard</h1>
      
      {/* Filters */}
      <div className="filters">
        <RiskLevelFilter value={filter.risk_level} onChange={(val) => setFilter({...filter, risk_level: val})} />
        <StatusFilter value={filter.status} onChange={(val) => setFilter({...filter, status: val})} />
        <SortDropdown value={sortBy} onChange={setSortBy} />
      </div>
      
      {/* Bid Cards */}
      <div className="bids-list">
        {bids.map(bid => (
          <BidCard
            key={bid.id}
            bid={bid}
            onClick={() => navigate(`/officer/bids/${bid.id}`)}
          />
        ))}
      </div>
    </div>
  );
};

interface BidCardProps {
  bid: Bid;
  onClick: () => void;
}

const BidCard: React.FC<BidCardProps> = ({ bid, onClick }) => {
  const riskColor = {
    HIGH: '#d32f2f',
    MEDIUM: '#f57c00',
    LOW: '#388e3c',
  };

  return (
    <Card onClick={onClick} className="bid-card">
      <div className="bid-header">
        <h3>{bid.bidder_org_name}</h3>
        <Badge color={riskColor[bid.risk_level]}>
          Risk: {bid.risk_level}
        </Badge>
      </div>
      <p>Tender: {bid.tender_title}</p>
      <div className="bid-meta">
        <span>Status: {bid.status}</span>
        <span>Compliance: {bid.compliance_status}</span>
        <span>Submitted: {new Date(bid.submitted_at).toLocaleDateString()}</span>
      </div>
    </Card>
  );
};
```

**Validates: Requirements 7.1 (bid evaluation dashboard)**

#### BidSubmissionFlow

```typescript
// pages/BidSubmissionFlow.tsx
const BidSubmissionFlow: React.FC<{ bidId: UUID }> = ({ bidId }) => {
  const [stage, setStage] = useState(1);  // 1-4
  const [documents, setDocuments] = useState<Document[]>([]);
  const [compliance, setCompliance] = useState<ComplianceEvaluation | null>(null);
  const [readiness, setReadiness] = useState(0);
  const bidStore = useBidStore();

  const handleDocumentUpload = async (file: File, docType: string) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('doc_type', docType);

    try {
      const response = await apiClient.post(`/bidder/bids/${bidId}/documents`, formData);
      setDocuments([...documents, response.data]);
      toast.success('Document uploaded');
    } catch (error) {
      toast.error('Document upload failed');
    }
  };

  const handleStage1Verify = async () => {
    try {
      const response = await apiClient.post(`/bidder/bids/${bidId}/verify-stage1`);
      if (response.data.passed) {
        setStage(2);
      } else {
        toast.error('Not all required documents uploaded');
      }
    } catch (error) {
      toast.error('Verification failed');
    }
  };

  const handleStage2Verify = async () => {
    try {
      await bidStore.evaluateCompliance(bidId);
      setCompliance(bidStore.complianceResults);
      
      // Fetch readiness
      const readinessResp = await apiClient.get(`/bidder/bids/${bidId}/readiness`);
      setReadiness(readinessResp.data.readiness_percent);
      
      setStage(3);
    } catch (error) {
      toast.error('Compliance evaluation failed');
    }
  };

  const handleSubmit = async () => {
    try {
      await apiClient.post(`/bidder/bids/${bidId}/submit`);
      toast.success('Bid submitted successfully');
      setStage(4);
    } catch (error) {
      toast.error('Bid submission failed');
    }
  };

  return (
    <div className="submission-flow">
      {stage === 1 && (
        <Stage1DocumentCheck
          onDocumentUpload={handleDocumentUpload}
          onComplete={handleStage1Verify}
        />
      )}
      
      {stage === 2 && (
        <Stage2Verification
          bidId={bidId}
          onComplete={handleStage2Verify}
        />
      )}
      
      {stage === 3 && (
        <Stage3ComplianceReview
          readiness={readiness}
          compliance={compliance}
          onSubmit={handleSubmit}
        />
      )}
      
      {stage === 4 && (
        <Stage4Confirmation />
      )}
    </div>
  );
};
```

**Validates: Requirements 3.1-3.3 (document management), 9.3 (readiness gauge)**

---

## 5. Integration Design: Adapter Pattern

### 5.1 Base Adapter Interface

```python
# adapters/base.py
from abc import ABC, abstractmethod

class Adapter(ABC):
    """Base adapter for external data sources."""
    
    @abstractmethod
    async def query(self, organization: Organization) -> AdapterResponse:
        """Query external source and return results."""
        pass
    
    @abstractmethod
    async def verify_format(self, data: dict) -> bool:
        """Verify response format is valid."""
        pass

# adapters/adapter_response.py
class AdapterResponse:
    """Standardized response from adapters."""
    
    def __init__(self, verified: bool, details: dict, confidence: float = None):
        self.verified = verified
        self.details = details  # Source-specific details
        self.confidence = confidence or (100.0 if verified else 0.0)
    
    def to_dict(self):
        return {
            "verified": self.verified,
            "details": self.details,
            "confidence": self.confidence,
        }
```

### 5.2 Concrete Adapters

```python
# adapters/real_adapters/gstin_adapter.py
class GSTINAdapter(Adapter):
    """Query GSTIN Registry via DataGovIn API."""
    
    def __init__(self, config: Config):
        self.base_url = "https://api.datagov.in/resource/ckan/gstin"
        self.api_key = config.datagov_api_key
        self.timeout = 5
    
    async def query(self, organization: Organization) -> AdapterResponse:
        """Query GSTIN registry."""
        
        if not organization.gstin:
            return AdapterResponse(
                verified=False,
                details={"error": "No GSTIN provided"},
                confidence=0
            )
        
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "gstin": organization.gstin,
                    "api_key": self.api_key,
                }
                
                async with session.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_response(organization, data)
                    else:
                        return AdapterResponse(
                            verified=False,
                            details={"error": f"HTTP {response.status}"},
                            confidence=0
                        )
        
        except asyncio.TimeoutError:
            return AdapterResponse(
                verified=False,
                details={"error": "API timeout"},
                confidence=0
            )
        except Exception as e:
            logger.error(f"GSTIN query failed: {e}")
            return AdapterResponse(
                verified=False,
                details={"error": str(e)},
                confidence=0
            )
    
    def _parse_response(self, organization: Organization, data: dict) -> AdapterResponse:
        """Parse GSTIN API response."""
        
        if data.get("count", 0) == 0:
            return AdapterResponse(
                verified=False,
                details={"error": "GSTIN not found"},
                confidence=0
            )
        
        record = data["records"][0]
        matched_name = record.get("legal_name", "")
        status = record.get("status", "").lower()
        
        # Check if status is active
        if status not in ["active", "regular"]:
            return AdapterResponse(
                verified=False,
                details={
                    "matched_name": matched_name,
                    "status": status,
                    "reason": f"GSTIN is {status}"
                },
                confidence=100
            )
        
        # Verify name match
        name_match_score = fuzzy_match(organization.legal_name, matched_name)
        
        return AdapterResponse(
            verified=True,
            details={
                "matched_name": matched_name,
                "status": status,
                "registration_date": record.get("registration_date"),
                "name_match_confidence": name_match_score,
            },
            confidence=name_match_score
        )

# adapters/real_adapters/pan_adapter.py
class PANAdapter(Adapter):
    """Query PAN Registry."""
    # Similar structure to GSTINAdapter

# adapters/real_adapters/mca_adapter.py
class MCAAdapter(Adapter):
    """Query MCA Portal for CIN verification."""
    # Similar structure to GSTINAdapter

# adapters/mock_adapters.py (for development/testing)
class MockGSTINAdapter(Adapter):
    """Mock GSTIN adapter for testing."""
    
    async def query(self, organization: Organization) -> AdapterResponse:
        """Return mock response based on GSTIN pattern."""
        
        if organization.gstin == "00INVALID00000V":
            return AdapterResponse(
                verified=False,
                details={"error": "GSTIN not found"},
                confidence=0
            )
        elif organization.gstin == "18AABCT1234A1Z5":
            return AdapterResponse(
                verified=True,
                details={
                    "matched_name": organization.legal_name,
                    "status": "active"
                },
                confidence=100
            )
        else:
            return AdapterResponse(
                verified=True,
                details={"matched_name": organization.legal_name},
                confidence=95
            )
```

**Validates: Requirements 5.1-5.2 (external verification adapters)**

### 5.3 Retry Logic & Circuit Breaker

```python
# adapters/retry_handler.py
import asyncio
from datetime import datetime, timedelta

class RetryHandler:
    """Handle retries with exponential backoff and circuit breaker."""
    
    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.failures = {}  # {endpoint: [(timestamp, error), ...]}
        self.circuit_breaker = {}  # {endpoint: {state, opened_at}}
    
    async def execute_with_retry(self, adapter: Adapter, organization: Organization,
                                endpoint: str) -> AdapterResponse:
        """Execute adapter query with retry logic."""
        
        # Check circuit breaker
        if self._is_circuit_open(endpoint):
            logger.warning(f"Circuit breaker open for {endpoint}")
            return AdapterResponse(
                verified=False,
                details={"error": "Service temporarily unavailable"},
                confidence=0
            )
        
        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = await adapter.query(organization)
                
                # Reset failure count on success
                if endpoint in self.failures:
                    del self.failures[endpoint]
                
                return result
            
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Adapter query failed (attempt {attempt + 1}/{self.max_retries}): {e}"
                )
                
                # Record failure for circuit breaker
                if endpoint not in self.failures:
                    self.failures[endpoint] = []
                self.failures[endpoint].append((datetime.utcnow(), e))
                
                # Exponential backoff
                if attempt < self.max_retries - 1:
                    delay = self.backoff_factor ** attempt
                    await asyncio.sleep(delay)
        
        # All retries failed, open circuit breaker if threshold reached
        if len(self.failures.get(endpoint, [])) >= self.max_retries * 2:
            self.circuit_breaker[endpoint] = {
                "state": "open",
                "opened_at": datetime.utcnow()
            }
        
        raise last_error
    
    def _is_circuit_open(self, endpoint: str) -> bool:
        """Check if circuit breaker is open."""
        
        if endpoint not in self.circuit_breaker:
            return False
        
        cb = self.circuit_breaker[endpoint]
        if cb["state"] != "open":
            return False
        
        # Auto-reset after 60 seconds
        if datetime.utcnow() - cb["opened_at"] > timedelta(seconds=60):
            cb["state"] = "half-open"
            return False
        
        return True
```

**Validates: Requirement 5.1 (retry logic)**

---

## 6. Security Design

### 6.1 Authentication & JWT

```python
# security/auth.py
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class AuthService:
    """Authentication and JWT management."""
    
    def __init__(self, config: Config):
        self.secret_key = config.jwt_secret_key
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60  # 3600 seconds
    
    def hash_password(self, password: str) -> str:
        """Hash password using Argon2."""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, user_id: UUID, role: str) -> str:
        """Create JWT access token."""
        
        payload = {
            "sub": str(user_id),
            "role": role,
            "exp": datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes),
            "iat": datetime.utcnow(),
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode JWT token."""
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            role = payload.get("role")
            
            if not user_id or not role:
                raise JWTError("Invalid token payload")
            
            return {"user_id": UUID(user_id), "role": role}
        
        except JWTError as e:
            logger.warning(f"Token verification failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid token")
```

**Validates: Requirement 1.1 (JWT authentication)**

### 6.2 RBAC Enforcement

```python
# security/rbac.py
from enum import Enum
from fastapi import HTTPException, Depends

class Role(str, Enum):
    OFFICER = "officer"
    BIDDER = "bidder"
    ADMIN = "admin"

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Extract user from JWT token."""
    
    auth_service = AuthService(config)
    payload = auth_service.verify_token(token)
    
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

def require_role(*allowed_roles: Role):
    """Decorator to enforce role-based access control."""
    
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required roles: {allowed_roles}"
            )
        return current_user
    
    return role_checker

# Usage in routes
@app.post("/api/officer/tenders")
async def create_tender(
    tender_data: TenderCreateRequest,
    current_user: User = Depends(require_role(Role.OFFICER))
):
    """Create tender - only officers allowed."""
    # Implementation
    pass

@app.get("/api/bidder/tenders")
async def list_tenders(
    current_user: User = Depends(require_role(Role.BIDDER))
):
    """List tenders - only bidders allowed."""
    # Implementation
    pass
```

**Validates: Requirements 1.1 (role management), 1.6-1.7 (RBAC enforcement)**

### 6.3 Input Validation & Sanitization

```python
# schemas/validators.py
from pydantic import BaseModel, validator, EmailStr

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def password_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        return v

class TenderCreateRequest(BaseModel):
    title: str
    organization_id: UUID
    
    @validator('title')
    def title_length(cls, v):
        if not (10 <= len(v) <= 500):
            raise ValueError('Title must be 10-500 characters')
        return v

class DocumentUploadRequest(BaseModel):
    doc_type: str
    
    @validator('doc_type')
    def valid_doc_type(cls, v):
        allowed_types = ["GST_CERT", "PAN", "COI", "UDYAM", "BANK_STATEMENT", "ITR", "CAPACITY_CERT"]
        if v not in allowed_types:
            raise ValueError(f"Invalid doc_type. Allowed: {allowed_types}")
        return v

# File upload validation
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_file_upload(file: UploadFile):
    """Validate uploaded file."""
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {ALLOWED_EXTENSIONS}")
    
    # Check file magic bytes (prevent spoofing)
    file_type = magic.from_buffer(contents, mime=True)
    if not file_type.startswith(("application/pdf", "image/jpeg", "image/png")):
        raise HTTPException(status_code=400, detail="Invalid file content")
    
    return contents
```

**Validates: Requirements 1.4 (error handling), 3.1 (file validation)**

### 6.4 Data Encryption

```python
# security/encryption.py
from cryptography.fernet import Fernet

class DataEncryption:
    """Encrypt sensitive data at rest."""
    
    def __init__(self, config: Config):
        self.cipher = Fernet(config.encryption_key.encode())
    
    def encrypt_pii(self, data: str) -> str:
        """Encrypt PII before storing."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_pii(self, encrypted_data: str) -> str:
        """Decrypt PII for display."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

# Usage in audit logging
async def log_audit_event(event_type: str, details: dict):
    """Log audit event with PII encryption."""
    
    encryption = DataEncryption(config)
    
    # Encrypt sensitive fields
    if "pan" in details:
        details["pan"] = encryption.encrypt_pii(details["pan"])
    if "gstin" in details:
        details["gstin"] = encryption.encrypt_pii(details["gstin"])
    
    audit_event = AuditEvent(
        event_type=event_type,
        details=details,
        timestamp=datetime.utcnow()
    )
    db.add(audit_event)
    await db.commit()
```

**Validates: Requirement 10.1 (audit trail with PII redaction)**

---

## 7. Scalability Design

### 7.1 Caching Strategy (Redis)

```python
# cache/redis_client.py
import redis
import json
from datetime import timedelta

class CacheService:
    """Redis caching for performance optimization."""
    
    def __init__(self, config: Config):
        self.redis = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=0,
            decode_responses=True
        )
    
    async def get_cached_bid(self, bid_id: UUID) -> Bid | None:
        """Get bid from cache."""
        
        key = f"bid:{bid_id}"
        cached = self.redis.get(key)
        
        if cached:
            return Bid(**json.loads(cached))
        return None
    
    async def cache_bid(self, bid: Bid, ttl_minutes: int = 5):
        """Cache bid for quick retrieval."""
        
        key = f"bid:{bid.id}"
        self.redis.setex(
            key,
            timedelta(minutes=ttl_minutes),
            json.dumps(bid.to_dict())
        )
    
    async def invalidate_bid_cache(self, bid_id: UUID):
        """Invalidate bid cache on updates."""
        
        key = f"bid:{bid_id}"
        self.redis.delete(key)
    
    async def get_cached_tender(self, tender_id: UUID) -> Tender | None:
        """Get published tender from cache."""
        
        key = f"tender:published:{tender_id}"
        cached = self.redis.get(key)
        
        if cached:
            return Tender(**json.loads(cached))
        return None
    
    async def cache_tender_list(self, tenders: List[Tender]):
        """Cache published tender list."""
        
        key = "tenders:published:all"
        self.redis.setex(
            key,
            timedelta(hours=1),
            json.dumps([t.to_dict() for t in tenders])
        )

# Cache invalidation on writes
@app.post("/api/officer/tenders/{tender_id}/publish")
async def publish_tender(tender_id: UUID, cache: CacheService = Depends()):
    # ... publish logic
    await cache.invalidate_bid_cache(tender_id)  # Invalidate related bids
```

**Validates: Requirement 7 (scalability with caching)**

### 7.2 Batch Processing & Task Queues

```python
# queue/task_queue.py
from celery import Celery
from kombu import Exchange, Queue

# Initialize Celery with Redis broker
celery_app = Celery(
    'gem_sentinel',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Define queues
celery_app.conf.task_queues = (
    Queue('compliance', Exchange('compliance'), routing_key='compliance.#'),
    Queue('ocr', Exchange('ocr'), routing_key='ocr.#'),
    Queue('notification', Exchange('notification'), routing_key='notification.#'),
)

# Task definitions
@celery_app.task(queue='compliance')
def evaluate_compliance_batch(bid_ids: List[UUID]):
    """Batch evaluate compliance for multiple bids."""
    
    service_factory = ServiceFactory(db, config)
    compliance_service = service_factory.get_compliance_service()
    
    for bid_id in bid_ids:
        try:
            evaluation = compliance_service.evaluate_all_rules(bid_id)
            logger.info(f"Batch compliance evaluation completed for bid {bid_id}")
        except Exception as e:
            logger.error(f"Batch compliance evaluation failed for bid {bid_id}: {e}")

@celery_app.task(queue='ocr')
def process_ocr_batch(document_ids: List[UUID]):
    """Batch process OCR for multiple documents."""
    
    ocr_service = OCRService(config)
    
    for doc_id in document_ids:
        try:
            ocr_result = ocr_service.extract_text(doc_id)
            logger.info(f"OCR completed for document {doc_id}")
        except Exception as e:
            logger.error(f"OCR failed for document {doc_id}: {e}")

@celery_app.task(queue='notification')
def send_notification_batch(notification_ids: List[UUID]):
    """Batch send notifications."""
    
    service_factory = ServiceFactory(db, config)
    notification_service = service_factory.get_notification_service()
    
    for notif_id in notification_ids:
        try:
            notification_service.send_notification(notif_id)
        except Exception as e:
            logger.error(f"Notification send failed for {notif_id}: {e}")

# Enqueue tasks
async def trigger_batch_compliance_evaluation():
    """Batch evaluate compliance for submitted bids."""
    
    # Find all submitted bids not yet evaluated
    pending_bids = db.query(Bid)\
        .filter(Bid.status == "SUBMITTED")\
        .filter(~Bid.compliance_results.any())\
        .limit(100)\
        .all()
    
    if pending_bids:
        bid_ids = [b.id for b in pending_bids]
        evaluate_compliance_batch.delay(bid_ids)
```

**Validates: Requirement 7 (batch processing for scalability)**

### 7.3 Connection Pooling

```python
# database/connection.py
from sqlalchemy.pool import QueuePool

DATABASE_URL = "postgresql://user:password@localhost:5432/gem_sentinel"

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Number of connections to maintain
    max_overflow=40,  # Allow up to 40 additional connections
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Test connection before using
    echo=False,
    connect_args={"timeout": 10}
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

async def get_db():
    """Database dependency for routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

**Validates: Requirement 7 (connection pooling)**

---

## 8. Data Flow Diagrams

### 8.1 Complete Bid Submission Pipeline

```
Bidder Creates Bid
    │
    ▼
POST /api/bidder/tenders/{tender_id}/bids
    │
    ├─→ BidService.create_bid()
    │   ├─→ Find latest TenderVersion
    │   ├─→ Create Bid (status=DRAFT)
    │   └─→ Log: BID_CREATED
    │
    ▼
Bid in DRAFT State
    │ (Bidder uploads documents)
    │
    ├─→ POST /api/bidder/bids/{bid_id}/documents
    │   ├─→ DocumentService.upload()
    │   │   ├─→ Validate file (size, type, content)
    │   │   ├─→ Calculate SHA256 hash
    │   │   ├─→ Store file to /uploads/...
    │   │   ├─→ Create Document (ocr_status=PENDING)
    │   │   └─→ Enqueue: OCR job
    │   │
    │   └─→ Background: OCRService processes
    │       ├─→ Extract text from PDF/image
    │       ├─→ Create ExtractedFact records
    │       ├─→ Update DocumentVersion.ocr_status=COMPLETED
    │       └─→ Log: OCR_COMPLETED
    │
    ├─→ POST /api/bidder/bids/{bid_id}/verify-stage1
    │   ├─→ DocumentService.validate_slots()
    │   │   └─→ Check: All required doc_types uploaded?
    │   └─→ Response: {passed: bool, slots: [...]}
    │
    ├─→ (If stage1 passed, proceed)
    │
    ├─→ POST /api/bidder/bids/{bid_id}/verify-stage2
    │   ├─→ Enqueue: ComplianceEvaluationTask
    │   └─→ Return: {task_id, status: IN_PROGRESS}
    │
    │   Background Worker (Compliance Evaluation):
    │   ├─→ ComplianceService.evaluate_all_rules()
    │   │   ├─→ For each compliance rule (GSTIN, PAN, name, etc.):
    │   │   │   ├─→ Extract required data (OCR facts + org metadata)
    │   │   │   ├─→ Apply rule logic
    │   │   │   ├─→ Store ComplianceResult (passed | failed)
    │   │   │   └─→ IF failed: Create RiskSignal
    │   │   │
    │   │   └─→ AdapterOrchestrator.verify_multi_source()
    │   │       ├─→ Parallel: Query GSTIN registry
    │   │       ├─→ Parallel: Query PAN registry
    │   │       ├─→ Parallel: Query MCA portal
    │   │       ├─→ Parallel: Query NSIC database
    │   │       ├─→ Parallel: Query Udyam registry
    │   │       └─→ Each with retry logic (3 attempts, exponential backoff)
    │   │           └─→ Store VerificationResult + VerificationAttempt
    │   │
    │   ├─→ RiskService.assess_risk()
    │   │   ├─→ Aggregate all RiskSignals
    │   │   ├─→ Calculate risk_score
    │   │   └─→ Determine risk_level (HIGH|MEDIUM|LOW)
    │   │
    │   └─→ Generate AI Recommendation based on compliance + risk
    │
    ├─→ Bidder polls: GET /api/bidder/bids/{bid_id}/verify-stage2/status/{task_id}
    │   └─→ When status=COMPLETED, fetch results
    │
    ├─→ Bidder reviews compliance readiness
    │   └─→ GET /api/bidder/bids/{bid_id}/readiness
    │       └─→ Return: {readiness_percent, items: [...]}
    │
    ▼
Bidder Submits Bid
    │
    ├─→ POST /api/bidder/bids/{bid_id}/submit
    │   ├─→ BidService.submit_bid()
    │   │   ├─→ Validate all required documents present
    │   │   ├─→ Set status=SUBMITTED, submitted_at=now
    │   │   ├─→ Update state: DRAFT → SUBMITTED
    │   │   ├─→ Log: BID_SUBMITTED + state transition
    │   │   └─→ Cache invalidation
    │   │
    │   └─→ NotificationService.notify()
    │       └─→ Send: Bidder confirmation email
    │
    ▼
Bid Queued for Officer Review
    │ (Officer reviews bid)
    │
    ├─→ GET /api/officer/bids
    │   └─→ Return: All submitted bids, sorted by risk (HIGH first)
    │
    ├─→ GET /api/officer/bids/{bid_id}
    │   ├─→ Fetch: Bid + TenderVersion + Organization
    │   ├─→ Fetch: All ComplianceResult records
    │   ├─→ Fetch: All RiskSignal + RiskAssessment
    │   ├─→ Fetch: All VerificationResult records
    │   ├─→ Fetch: All ClarificationRequest records
    │   └─→ Return: Comprehensive bid detail with AI recommendation
    │
    ├─→ (Officer may post clarification if needed)
    │   │
    │   ├─→ POST /api/officer/bids/{bid_id}/clarifications
    │   │   ├─→ ClarificationService.post_request()
    │   │   ├─→ Log: CLARIFICATION_POSTED
    │   │   └─→ NotificationService.notify(bidder)
    │   │
    │   └─→ GET /api/bidder/bids/{bid_id}/clarifications
    │       └─→ Bidder responds:
    │           ├─→ POST /api/bidder/bids/{bid_id}/clarifications/{request_id}/respond
    │           ├─→ ClarificationService.post_response()
    │           ├─→ Log: CLARIFICATION_RESPONDED
    │           └─→ NotificationService.notify(officer)
    │
    ▼
Officer Makes Final Decision
    │
    └─→ POST /api/officer/bids/{bid_id}/decision
        ├─→ OfficerDecisionService.make_decision()
        │   ├─→ Validate override_reason if decision != ai_recommendation
        │   ├─→ Create OfficerDecision record
        │   ├─→ IF override: Create OfficerDecisionOverride
        │   ├─→ IF risk=HIGH + override: Set requires_approval=true
        │   ├─→ Update Bid (status=DECIDED, current_state=DECIDED)
        │   ├─→ Log: BID_DECIDED + state transition
        │   └─→ Cache invalidation
        │
        └─→ NotificationService.notify(bidder)
            └─→ Send: Decision email (VERIFIED | NON_COMPLIANT)

Timeline:
Step 1: Bidder creates bid (DRAFT)
Step 2: Bidder uploads documents + OCR processes
Step 3: Bidder verifies stage 1 (document slots)
Step 4: Bidder triggers stage 2 (compliance + risk evaluation) - async task
Step 5: Bidder polls for completion, reviews readiness
Step 6: Bidder submits bid (SUBMITTED)
Step 7: Officer reviews bid dashboard (sorted by risk)
Step 8: Officer may request clarification, bidder responds
Step 9: Officer makes final decision (DECIDED)
```

**Validates: Requirements 2.3 (bid creation), 3.1-3.3 (document flow), 4.2 (compliance), 7.1 (officer dashboard), 8.1 (decision)**

---

## 9. Error Handling & Recovery

### 9.1 Exception Hierarchy

```python
# exceptions/errors.py

class GemSentinelException(Exception):
    """Base exception for all system errors."""
    
    def __init__(self, message: str, code: str = None, details: dict = None):
        self.message = message
        self.code = code or "INTERNAL_ERROR"
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(GemSentinelException):
    """Invalid input or state."""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", details)

class NotFoundError(GemSentinelException):
    """Resource not found."""
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            f"{resource_type} not found",
            "NOT_FOUND",
            {"resource_type": resource_type, "resource_id": resource_id}
        )

class AuthenticationError(GemSentinelException):
    """Authentication failed."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTHENTICATION_ERROR")

class AuthorizationError(GemSentinelException):
    """Insufficient permissions."""
    def __init__(self, required_role: str):
        super().__init__(
            f"Insufficient permissions",
            "AUTHORIZATION_ERROR",
            {"required_role": required_role}
        )

class ExternalServiceError(GemSentinelException):
    """External API/service error."""
    def __init__(self, service_name: str, error: str, retry_count: int = 0):
        super().__init__(
            f"{service_name} error: {error}",
            "EXTERNAL_SERVICE_ERROR",
            {"service": service_name, "retry_count": retry_count}
        )

class DocumentProcessingError(GemSentinelException):
    """Document upload/OCR error."""
    def __init__(self, doc_id: str, error: str):
        super().__init__(
            f"Document processing failed: {error}",
            "DOCUMENT_ERROR",
            {"document_id": doc_id}
        )

class StateTransitionError(GemSentinelException):
    """Invalid state transition."""
    def __init__(self, current_state: str, requested_state: str):
        super().__init__(
            f"Cannot transition from {current_state} to {requested_state}",
            "STATE_TRANSITION_ERROR",
            {"current_state": current_state, "requested_state": requested_state}
        )
```

**Validates: Requirement 1.4 (error handling)**

### 9.2 Global Exception Handler

```python
# middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse

@app.exception_handler(GemSentinelException)
async def gem_exception_handler(request: Request, exc: GemSentinelException):
    """Handle application exceptions."""
    
    # Log error with context
    logger.error(
        f"Application error: {exc.code}",
        extra={
            "endpoint": request.url.path,
            "user_id": getattr(request.state, "user_id", None),
            "timestamp": datetime.utcnow(),
            "error_details": exc.details,
        }
    )
    
    # Map error codes to HTTP status
    status_map = {
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "AUTHENTICATION_ERROR": status.HTTP_401_UNAUTHORIZED,
        "AUTHORIZATION_ERROR": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
        "DOCUMENT_ERROR": status.HTTP_400_BAD_REQUEST,
        "STATE_TRANSITION_ERROR": status.HTTP_409_CONFLICT,
    }
    
    http_status = status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return JSONResponse(
        status_code=http_status,
        content={
            "detail": exc.message,
            "error_code": exc.code,
            "details": exc.details,
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    
    # Log full stack trace
    logger.exception(
        f"Unexpected error: {exc}",
        extra={
            "endpoint": request.url.path,
            "user_id": getattr(request.state, "user_id", None),
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )
```

**Validates: Requirements 1.4 (API error handling)**

### 9.3 Fallback Strategies

```python
# services/fallback_strategy.py

class VerificationFallback:
    """Fallback strategies for external verification failures."""
    
    @staticmethod
    async def handle_gstin_failure(organization: Organization) -> VerificationResult:
        """Fallback when GSTIN verification fails."""
        
        # Strategy 1: Check if GSTIN format is valid
        if not is_valid_gstin_format(organization.gstin):
            return VerificationResult(
                verified=False,
                details={"reason": "Invalid GSTIN format"},
                confidence=0
            )
        
        # Strategy 2: Check against cached/historical data
        cached_gstin = await cache.get(f"gstin:{organization.gstin}")
        if cached_gstin:
            return VerificationResult(
                verified=cached_gstin["verified"],
                details=cached_gstin["details"],
                confidence=50  # Lower confidence due to staleness
            )
        
        # Strategy 3: Default to UNKNOWN status
        return VerificationResult(
            verified=None,  # Unknown
            details={"reason": "Verification source temporarily unavailable"},
            confidence=0
        )
    
    @staticmethod
    async def handle_ocr_failure(document: Document) -> ExtractedFact:
        """Fallback when OCR processing fails."""
        
        # Strategy 1: Try alternate OCR provider (if available)
        try:
            alt_result = await alternate_ocr_provider.extract_text(document.file_path)
            return alt_result
        except:
            pass
        
        # Strategy 2: Manual review queue
        await queue.enqueue(
            "manual_document_review",
            document_id=document.id,
            reason="OCR failed"
        )
        
        # Strategy 3: Mark document as requiring human review
        return ExtractedFact(
            document_id=document.id,
            fact_type="REQUIRES_REVIEW",
            value="Document requires manual OCR",
            confidence=0
        )
    
    @staticmethod
    async def handle_email_failure(notification: Notification) -> bool:
        """Fallback when email sending fails."""
        
        # Strategy 1: Retry with exponential backoff (already implemented)
        # Strategy 2: Store in queue for later delivery
        await notification_queue.enqueue(notification)
        
        # Strategy 3: In-app notification as fallback
        notification.in_app_only = True
        await db.commit()
        
        # Strategy 4: Alert admin if critical notification fails
        if notification.notification_type in ["DECISION", "URGENT"]:
            await send_admin_alert(
                f"Critical notification failed: {notification.id}",
                severity="HIGH"
            )
        
        return False
```

**Validates: Requirement 5.1 (retry/fallback logic)**

---

## 10. Testing Strategy

### 10.1 Unit Test Coverage

```python
# tests/test_compliance_service.py
import pytest
from unittest.mock import Mock, AsyncMock, patch

class TestComplianceService:
    """Unit tests for ComplianceService."""
    
    @pytest.fixture
    def setup(self):
        self.db = Mock()
        self.adapter_orch = AsyncMock()
        self.evidence_service = AsyncMock()
        self.audit_service = AsyncMock()
        
        self.service = ComplianceService(
            db=self.db,
            adapter_orch=self.adapter_orch,
            evidence_service=self.evidence_service,
            audit_service=self.audit_service
        )
    
    @pytest.mark.asyncio
    async def test_evaluate_gstin_valid(self, setup):
        """Test GSTIN validation rule."""
        
        # Arrange
        bid_id = UUID("12345678-1234-5678-1234-567812345678")
        organization = Mock(legal_name="Test Corp", gstin="18AABCT1234A1Z5")
        
        # Mock verification result
        self.adapter_orch.verify_multi_source.return_value = Mock(
            overall_verification_status="VERIFIED",
            results=[Mock(source_name="GSTIN", verified=True)]
        )
        
        # Act
        result = await self.service.evaluate_rule(bid_id, "gstin_valid", {})
        
        # Assert
        assert result.passed is True
        assert result.rule_name == "gstin_valid"
        self.audit_service.log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_evaluate_gstin_invalid(self, setup):
        """Test GSTIN validation with invalid GSTIN."""
        
        # Arrange
        bid_id = UUID("12345678-1234-5678-1234-567812345678")
        organization = Mock(legal_name="Test Corp", gstin="00INVALID00000V")
        
        self.adapter_orch.verify_multi_source.return_value = Mock(
            overall_verification_status="FAILED",
            results=[]
        )
        
        # Act
        result = await self.service.evaluate_rule(bid_id, "gstin_valid", {})
        
        # Assert
        assert result.passed is False
        assert result.explanation is not None

# tests/test_bid_service.py
class TestBidService:
    """Unit tests for BidService."""
    
    @pytest.mark.asyncio
    async def test_create_bid(self):
        """Test bid creation."""
        
        # Arrange
        service = BidService(db=Mock(), audit_service=AsyncMock())
        tender_id = UUID("...") 
        bidder_org_id = UUID("...")
        
        # Act
        bid = await service.create_bid(tender_id, bidder_org_id)
        
        # Assert
        assert bid.status == "DRAFT"
        assert bid.current_state == "DRAFT"
        assert bid.state_entered_at is not None
    
    @pytest.mark.asyncio
    async def test_submit_bid_validates_documents(self):
        """Test bid submission requires documents."""
        
        # Arrange
        db = Mock()
        db.query(Document).filter(...).count.return_value = 0
        
        service = BidService(db=db, audit_service=AsyncMock())
        bid_id = UUID("...")
        
        # Act & Assert
        with pytest.raises(ValidationError):
            await service.submit_bid(bid_id)
```

**Validates: Requirement 12 (testing strategy)**

### 10.2 Integration Test Coverage

```python
# tests/integration/test_compliance_pipeline.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

class TestCompliancePipeline:
    """Integration tests for complete compliance pipeline."""
    
    def test_bid_submission_to_decision(self, client, test_database):
        """Test complete flow from submission to decision."""
        
        # 1. Create tender
        tender_response = client.post(
            "/api/officer/tenders",
            json={"title": "Test Tender"},
            headers={"Authorization": f"Bearer {officer_token}"}
        )
        tender_id = tender_response.json()["id"]
        
        # 2. Publish tender
        client.post(
            f"/api/officer/tenders/{tender_id}/publish",
            headers={"Authorization": f"Bearer {officer_token}"}
        )
        
        # 3. Create bid
        bid_response = client.post(
            f"/api/bidder/tenders/{tender_id}/bids",
            headers={"Authorization": f"Bearer {bidder_token}"}
        )
        bid_id = bid_response.json()["id"]
        
        # 4. Upload document
        with open("test_data/sample_gst.pdf", "rb") as f:
            doc_response = client.post(
                f"/api/bidder/bids/{bid_id}/documents",
                files={"file": f},
                data={"doc_type": "GST_CERT"},
                headers={"Authorization": f"Bearer {bidder_token}"}
            )
        assert doc_response.status_code == 200
        
        # 5. Verify stage 1
        stage1_response = client.post(
            f"/api/bidder/bids/{bid_id}/verify-stage1",
            headers={"Authorization": f"Bearer {bidder_token}"}
        )
        assert stage1_response.json()["passed"] is True
        
        # 6. Verify stage 2 (async)
        stage2_response = client.post(
            f"/api/bidder/bids/{bid_id}/verify-stage2",
            headers={"Authorization": f"Bearer {bidder_token}"}
        )
        task_id = stage2_response.json()["task_id"]
        
        # Poll for completion
        import time
        max_polls = 30
        for _ in range(max_polls):
            status_response = client.get(
                f"/api/bidder/bids/{bid_id}/verify-stage2/status/{task_id}",
                headers={"Authorization": f"Bearer {bidder_token}"}
            )
            if status_response.json()["status"] == "COMPLETED":
                break
            time.sleep(1)
        
        # 7. Submit bid
        submit_response = client.post(
            f"/api/bidder/bids/{bid_id}/submit",
            headers={"Authorization": f"Bearer {bidder_token}"}
        )
        assert submit_response.json()["status"] == "SUBMITTED"
        
        # 8. Officer reviews and decides
        detail_response = client.get(
            f"/api/officer/bids/{bid_id}",
            headers={"Authorization": f"Bearer {officer_token}"}
        )
        bid_detail = detail_response.json()
        
        decision_response = client.post(
            f"/api/officer/bids/{bid_id}/decision",
            json={
                "final_decision": "VERIFIED",
                "ai_recommendation": bid_detail["ai_recommendation"]
            },
            headers={"Authorization": f"Bearer {officer_token}"}
        )
        assert decision_response.status_code == 200
        assert decision_response.json()["status"] == "DECIDED"
```

**Validates: Requirements 4.2, 7.1, 8.1 (end-to-end testing)**

### 10.3 End-to-End Test Scenarios

```python
# tests/e2e/test_scenarios.py

class TestE2EScenarios:
    """End-to-end test scenarios."""
    
    def test_high_risk_bid_requires_override(self, client):
        """Scenario: High-risk bid requires officer override."""
        
        # Setup: Create bid with multiple risk factors
        # - GSTIN name mismatch
        # - PAN verification failed
        # - Duplicate bidder detected
        
        # Expected outcome:
        # - risk_level = "HIGH"
        # - ai_recommendation = "MANUAL_REVIEW_REQUIRED"
        # - officer must provide override_reason to approve
        
        pass
    
    def test_clarification_workflow(self, client):
        """Scenario: Officer posts clarification, bidder responds."""
        
        # Setup: Submitted bid with unclear compliance
        # Officer posts: "Please clarify GSTIN mismatch"
        # Bidder responds: "GSTIN was recently updated, here's new certificate"
        
        # Expected outcome:
        # - ClarificationRequest status = "RESOLVED"
        # - Compliance can be re-evaluated with new documents
        
        pass
    
    def test_concurrent_bid_submissions(self, client):
        """Scenario: Multiple bidders submit for same tender."""
        
        # Setup: 5 bidders submit simultaneously
        # Each uploads documents, triggers compliance evaluation
        
        # Expected outcome:
        # - All bids queued without interference
        # - Each evaluation independent and complete
        # - Risk scores calculated accurately
        
        pass
```

**Validates: Requirement 10 (comprehensive testing)**

---

## 11. Deployment Strategy

### 11.1 Database Migration & Initialization

```bash
# Step 1: Apply migrations
alembic upgrade head

# Step 2: Seed initial data (if needed)
python scripts/seed_database.py

# Step 3: Verify schema
python -m scripts.verify_schema

# Step 4: Create indexes
alembic upgrade head --sql > migrations/indexes.sql
```

### 11.2 Service Deployment Order

```
1. Database migrations (PostgreSQL)
2. Cache setup (Redis)
3. Backend services (FastAPI + Uvicorn)
4. Message queue (Celery workers)
5. Frontend (React)
6. Monitoring/Logging (ELK stack optional)

Deployment sequence:
├─ Phase 1: Infrastructure
│  ├─ PostgreSQL + migrations
│  ├─ Redis cache
│  └─ Message broker (RabbitMQ/Redis)
│
├─ Phase 2: Backend
│  ├─ Uvicorn server (multiple instances)
│  ├─ Celery workers
│  └─ Health check verification
│
├─ Phase 3: Frontend
│  ├─ React build
│  └─ Static file serving (nginx)
│
└─ Phase 4: Verification
   ├─ API health checks
   ├─ Database connectivity tests
   └─ End-to-end smoke tests
```

**Validates: Requirement 11 (deployment strategy)**

### 11.3 Rollback Procedures

```bash
# Database rollback
alembic downgrade -1  # Rollback one migration
alembic downgrade ae1027a6acf  # Rollback to specific revision

# Service rollback
docker pull gem-sentinel:previous-version
docker-compose down
docker-compose up -d  # With previous version in docker-compose.yml

# Cache cleanup (if needed)
redis-cli FLUSHALL  # Clear all cache on rollback
```

---

## 12. Monitoring & Observability

### 12.1 Metrics

```python
# monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Request metrics
request_count = Counter('requests_total', 'Total requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('request_duration_seconds', 'Request latency', ['endpoint'])

# Business metrics
bids_submitted = Counter('bids_submitted_total', 'Total bids submitted')
bids_verified = Counter('bids_verified_total', 'Bids verified')
bids_noncompliant = Counter('bids_noncompliant_total', 'Non-compliant bids')

# Risk assessment metrics
high_risk_bids = Gauge('high_risk_bids_current', 'Current high-risk bids')
average_risk_score = Gauge('average_risk_score', 'Average bid risk score')

# External service metrics
external_api_errors = Counter('external_api_errors_total', 'External API errors', ['service'])
verification_latency = Histogram('verification_latency_seconds', 'Verification latency', ['source'])

# Usage
@app.post("/api/bidder/bids/{bid_id}/submit")
async def submit_bid(bid_id: UUID):
    start = time.time()
    try:
        # Business logic
        bids_submitted.inc()
        request_count.labels(method='POST', endpoint='/submit', status='200').inc()
        return response
    finally:
        duration = time.time() - start
        request_duration.labels(endpoint='/submit').observe(duration)
```

### 12.2 Logging Strategy

```python
# logging/logger.py
import logging
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Usage in code
logger.info(
    "Bid evaluated",
    extra={
        "bid_id": str(bid_id),
        "compliance_status": "COMPLIANT",
        "risk_level": "MEDIUM",
        "duration_ms": 1234,
        "user_id": str(user_id),
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

### 12.3 Alerting

```python
# monitoring/alerts.py

class AlertManager:
    """Send alerts for critical events."""
    
    async def alert_high_risk_detected(self, bid_id: UUID, risk_score: float):
        """Alert when high-risk bid detected."""
        
        message = f"High-risk bid {bid_id}: score={risk_score}"
        await self.send_to_slack(message, severity="WARNING")
    
    async def alert_external_service_failure(self, service_name: str, error: str):
        """Alert when external service fails."""
        
        message = f"External service {service_name} failed: {error}"
        await self.send_to_slack(message, severity="CRITICAL")
    
    async def alert_database_connection_lost(self):
        """Alert on database connectivity loss."""
        
        message = "Database connection lost"
        await self.send_to_slack(message, severity="CRITICAL")
```

**Validates: Requirement 12 (monitoring & observability)**

---

## 13. Performance Optimization

### 13.1 Query Optimization

```sql
-- Instead of N+1 queries
-- Bad: Query bid, then loop through to fetch compliance results
SELECT * FROM bid WHERE id = ?;
SELECT * FROM compliance_result WHERE bid_id = ?;  -- Repeated in loop

-- Good: Join at database level
SELECT b.*, cr.* 
FROM bid b
LEFT JOIN compliance_result cr ON b.id = cr.bid_id
WHERE b.id = ?;

-- With indexes
CREATE INDEX idx_compliance_bid_id ON compliance_result(bid_id);
CREATE INDEX idx_risk_signal_bid_id ON risk_signal(bid_id);
```

### 13.2 Caching Strategy

```python
# Bidder bid list - cache 5 minutes
@app.get("/api/bidder/bids")
@cache(expire=300)
async def list_bidder_bids(current_user: User = Depends(get_current_user)):
    return db.query(Bid).filter(Bid.bidder_org_id == current_user.organization_id).all()

# Officer dashboard - cache 1 minute (more frequent changes)
@app.get("/api/officer/bids")
@cache(expire=60)
async def list_officer_bids():
    return db.query(Bid).filter(Bid.status == "SUBMITTED").order_by(Bid.risk_level.desc()).all()

# Published tenders - cache 1 hour (rarely change)
@app.get("/api/bidder/tenders")
@cache(expire=3600)
async def list_published_tenders():
    return db.query(Tender).filter(Tender.status == "published").all()
```

### 13.3 Async Processing

```python
# Long-running operations enqueued to background workers
@app.post("/api/bidder/bids/{bid_id}/verify-stage2")
async def verify_stage2(bid_id: UUID):
    # Enqueue to Celery instead of blocking
    task = evaluate_compliance_batch.delay([bid_id])
    return {"task_id": task.id, "status": "IN_PROGRESS"}

# Return immediately to user, let worker process
```

**Validates: Requirement 13 (performance optimization)**

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Bid State Transitions Are Valid

For any bid, state transitions must follow the defined state machine: DRAFT → SUBMITTED → DECIDED. No direct transitions to non-adjacent states are allowed.

**Validates: Requirements 2.3 (bid creation), 10.2 (state history)**

### Property 2: Compliance Evaluation is Deterministic

For any bid and snapshot of external verification data, compliance evaluation produces the same result (same compliance_status, same compliance_results). Re-evaluating the same bid with the same data yields identical outcomes.

**Validates: Requirements 4.2 (compliance evaluation), 10.3 (audit)**

### Property 3: Risk Score Calculation is Monotonic

For any bid, if a new risk signal is detected, the overall_risk_score increases or stays the same. Risk score never decreases when additional signals are added.

**Validates: Requirement 6.2 (risk scoring)**

### Property 4: Verification Results are Persisted Immutably

For any bid verification attempt, all VerificationAttempt and VerificationResult records created are immutable. Once created, they cannot be modified or deleted; only new records can be added.

**Validates: Requirements 5.1 (verification), 10.1 (audit trail)**

### Property 5: Officer Decision Override Requires Reason

For any officer decision where final_decision ≠ ai_recommendation, an OfficerDecisionOverride record must exist with a non-empty override_reason. Decisions that override recommendations must be auditable.

**Validates: Requirements 8.1 (decision), 8.2 (audit), 7.3 (recommendation)**

### Property 6: Document Hash Provides Integrity

For any uploaded document, the stored file_hash (SHA256) remains unchanged throughout the document's lifetime. File content and hash are immutably paired; if file is modified, hash must change.

**Validates: Requirement 3.1 (document integrity)**

### Property 7: All Compliance Results Reference Evidence

For any ComplianceResult with passed=false, evidence_references array must contain at least one reference (document_id or fact_id). Failed compliance rules always have supporting evidence stored.

**Validates: Requirements 4.3 (evidence traceability), 4.4 (risk signals)**

### Property 8: Audit Trail is Complete and Chronological

For any bid lifecycle, the audit trail (AuditEvent records) contains all state-changing operations in chronological order by timestamp. No operations are missing; no timestamps are out of order.

**Validates: Requirement 10.1 (audit trail)**

### Property 9: Verification Sources Query in Parallel

For any compliance evaluation requesting multi-source verification, all configured sources (GSTIN, PAN, MCA, NSIC, Udyam) are queried concurrently. Query latency = max(individual source latencies), not sum.

**Validates: Requirement 5.1 (parallel verification)**

### Property 10: Required Documents Cannot Be Missing Before Submission

For any bid with status=SUBMITTED, all documents specified in tender.required_documents must exist (Document records with deleted=false). Bids cannot be submitted if required documents are missing.

**Validates: Requirements 2.4 (document requirements), 3.3 (slot validation)**

### Property 11: Clarification Workflow is Bidirectional

For any ClarificationRequest, if status=OPEN, a corresponding ClarificationResponse must not exist. If status=RESOLVED, a ClarificationResponse must exist. Status transitions are one-way: OPEN → RESOLVED (optionally → REOPENED).

**Validates: Requirement 7.4 (clarification workflow)**

### Property 12: JWTokens Expire After Exactly 3600 Seconds

For any JWT access token, the exp claim minus iat claim equals 3600 seconds. Tokens issued now will be rejected after 3600 seconds. Early rejection is not allowed; late acceptance is not allowed.

**Validates: Requirement 1.3 (JWT validation)**

---

## Summary

This comprehensive design document covers all 10 phases of the GeM AI/ML Based Bidder Compliance Verification Platform with:

- **Layered Architecture:** Clear separation between Presentation, API, Application, AI/ML, Integration, and Data layers
- **Database Schema:** Complete relational design with indexes, migrations, and audit trails
- **Backend Services:** Modular, dependency-injected services with async patterns and error handling
- **Frontend Components:** React architecture with state management and API integration
- **Integration Patterns:** Adapter pattern for external sources with retry logic and circuit breakers
- **Security:** JWT authentication, RBAC, input validation, and PII encryption
- **Scalability:** Redis caching, task queues, connection pooling, and batch processing
- **Testing:** Unit, integration, and end-to-end test strategies
- **Deployment:** Migration strategy, service deployment order, and rollback procedures
- **Observability:** Metrics, logging, and alerting for production support
- **Performance:** Query optimization, caching, and async processing

Each design decision maps back to specific requirements, enabling traceability and compliance verification.

