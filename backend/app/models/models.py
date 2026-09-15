import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy import JSON
from sqlalchemy.types import Text
import json
from sqlalchemy.orm import relationship

from app.db.base import Base


def uuid_col():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Organization(Base):
    __tablename__ = "organizations"
    id = uuid_col()
    legal_name = Column(Text, nullable=False)
    cin = Column(Text)
    gstin = Column(Text)
    pan = Column(Text)
    udyam_number = Column(Text)
    nsic_number = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class User(Base):
    __tablename__ = "users"
    id = uuid_col()
    email = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (CheckConstraint("role IN ('bidder','officer','admin')"),)


class Tender(Base):
    __tablename__ = "tenders"
    id = uuid_col()
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False, default="")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(Text, nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    required_documents = Column(JSON, nullable=True)
    deadline = Column(DateTime(timezone=True), nullable=True)

    versions = relationship("TenderVersion", back_populates="tender")

    __table_args__ = (CheckConstraint("status IN ('draft','published','closed')"),)


class TenderVersion(Base):
    __tablename__ = "tender_versions"
    id = uuid_col()
    tender_id = Column(UUID(as_uuid=True), ForeignKey("tenders.id"), nullable=False)
    version_number = Column(Text, nullable=False)
    is_corrigendum = Column(Boolean, default=False)
    supersedes_version_id = Column(UUID(as_uuid=True), ForeignKey("tender_versions.id"))
    source_document_path = Column(Text, nullable=False)
    precedence_policy_version = Column(Text, nullable=False, default="default_v1")
    published_at = Column(DateTime(timezone=True))

    tender = relationship("Tender", back_populates="versions")
    clauses = relationship("Clause", back_populates="tender_version")

    __table_args__ = (UniqueConstraint("tender_id", "version_number"),)


class Clause(Base):
    __tablename__ = "clauses"
    id = uuid_col()
    tender_version_id = Column(
        UUID(as_uuid=True), ForeignKey("tender_versions.id"), nullable=False
    )
    raw_text = Column(Text, nullable=False)
    source_page = Column(Integer)
    source_span = Column(Text)
    category = Column(Text)
    mandatory = Column(Boolean, nullable=False, default=True)
    logic_tree = Column(JSON, nullable=False)
    ambiguity_flag = Column(Boolean, default=False)
    ambiguity_reason = Column(Text)
    extraction_confidence = Column(Numeric(4, 3))
    grounding_verified = Column(Boolean, nullable=False, default=False)
    superseded_by_clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    tender_version = relationship("TenderVersion", back_populates="clauses")

    __table_args__ = (
        CheckConstraint(
            "category IN ('FINANCIAL','STATUTORY','TECHNICAL','EXPERIENCE','OTHER')"
        ),
    )


class ClauseDiff(Base):
    __tablename__ = "clause_diffs"
    id = uuid_col()
    old_clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"))
    new_clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)
    diff_type = Column(Text)
    field_changed = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("diff_type IN ('ADDED','REMOVED','MODIFIED','UNCHANGED')"),
    )


class Bid(Base):
    __tablename__ = "bids"
    id = uuid_col()
    tender_version_id = Column(
        UUID(as_uuid=True), ForeignKey("tender_versions.id"), nullable=False
    )
    bidder_org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    status = Column(Text, nullable=False, default="draft")
    current_state = Column(Text, default="DRAFT")  # Phase 1: State machine
    state_entered_at = Column(DateTime(timezone=True))  # Phase 1
    state_metadata = Column(JSON)  # Phase 1: Transition metadata
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    tender_version = relationship("TenderVersion")
    documents = relationship("Document", back_populates="bid")
    bidder_org = relationship("Organization", foreign_keys=[bidder_org_id])
    
    @property
    def tender(self):
        """Convenience property to access tender through tender_version."""
        if self.tender_version:
            return self.tender_version.tender
        return None

    __table_args__ = (
        CheckConstraint("status IN ('draft','submitted','under_review','decided')"),
        CheckConstraint("current_state IN ('DRAFT','SUBMITTED','VERIFYING','REVIEW','CLARIFICATION','RESUBMITTED','DECIDED')"),
    )


class Document(Base):
    __tablename__ = "documents"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    file_path = Column(Text, nullable=False)
    file_hash = Column(Text, nullable=False)
    doc_type = Column(Text)
    classification_confidence = Column(Numeric(4, 3))
    ocr_status = Column(Text, default="PENDING")
    current_version = Column(Integer, default=1)  # Phase 1: Document versioning
    superseded_by_document_id = Column(UUID(as_uuid=True))  # Phase 1: Version tracking
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    bid = relationship("Bid", back_populates="documents")
    facts = relationship("ExtractedFact", back_populates="document")
    verification_attempts = relationship("VerificationAttempt", back_populates="source_document")

    __table_args__ = (
        CheckConstraint("ocr_status IN ('PENDING','DONE','FAILED','UNSUPPORTED')"),
    )


class ExtractedFact(Base):
    __tablename__ = "extracted_facts"
    id = uuid_col()
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    field_name = Column(Text, nullable=False)
    field_value = Column(Text, nullable=False)
    source_page = Column(Integer)
    evidence_span = Column(Text, nullable=False)
    confidence = Column(Numeric(4, 3), nullable=False)
    meets_threshold = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    document = relationship("Document", back_populates="facts")
    verification_attempts = relationship("VerificationAttempt", back_populates="extracted_fact")


class EntityResolutionResult(Base):
    __tablename__ = "entity_resolution_results"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    claimed_org_name = Column(Text, nullable=False)
    resolved_organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    match_method = Column(Text)
    identifier_conflicts = Column(JSON)
    status = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("match_method IN ('IDENTIFIER_EXACT','NAME_FUZZY','CONFLICT')"),
        CheckConstraint("status IN ('RESOLVED','CONFLICT','UNRESOLVED')"),
    )


class VerificationResult(Base):
    __tablename__ = "verification_results"
    id = uuid_col()
    extracted_fact_id = Column(
        UUID(as_uuid=True), ForeignKey("extracted_facts.id"), nullable=False
    )
    adapter_source = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    checked_at = Column(DateTime(timezone=True), nullable=False)
    freshness_seconds = Column(Integer)
    raw_response = Column(JSON)
    evidence = Column(Text)
    error = Column(Text)

    __table_args__ = (
        CheckConstraint(
            "status IN ('VERIFIED','MISMATCH','UNAVAILABLE','INCONCLUSIVE','PENDING','NOT_REQUIRED')"
        ),
    )


class ComplianceResult(Base):
    __tablename__ = "compliance_results"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"), nullable=False)
    explanation = Column(Text, nullable=False)  # PASS, FAIL, WAIVED, REVIEW, NOT_EVALUATED
    reasoning_chain = Column(JSON, nullable=True)  # Made optional for backward compat
    evidence_refs = Column(JSON, nullable=True)  # Made optional for backward compat
    rule_version = Column(Text, nullable=True)  # Made optional for backward compat
    is_immutable = Column(Boolean, default=True)  # Phase 5: Immutability
    original_status_before_override = Column(Text)  # Phase 8: Override tracking
    evaluated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("explanation IN ('PASS','FAIL','WAIVED','REVIEW','NOT_EVALUATED')"),
    )
    
    @property
    def status(self):
        """Backward compatibility property."""
        return self.explanation


class RiskSignal(Base):
    __tablename__ = "risk_signals"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    signal_type = Column(Text, nullable=False)
    weight = Column(Numeric(5, 3), nullable=False)
    severity = Column(Numeric(5, 3), nullable=False)

    extracted_fact_id = Column(UUID(as_uuid=True), ForeignKey("extracted_facts.id"))
    verification_result_id = Column(UUID(as_uuid=True), ForeignKey("verification_results.id"))
    entity_resolution_result_id = Column(
        UUID(as_uuid=True), ForeignKey("entity_resolution_results.id")
    )
    compliance_result_id = Column(UUID(as_uuid=True), ForeignKey("compliance_results.id"))

    policy_version = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False, unique=True)
    overall_risk_score = Column(Numeric(6, 3), nullable=False)  # 0-100 risk score
    assessed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = ()
    
    @property
    def risk_level(self):
        """Derive risk level from score."""
        if self.overall_risk_score < 30:
            return 'LOW'
        elif self.overall_risk_score < 70:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    @property
    def total_score(self):
        """Backward compatibility."""
        return self.overall_risk_score


class OfficerDecision(Base):
    __tablename__ = "officer_decisions"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decision = Column(Text, nullable=False)  # VERIFIED, NON_COMPLIANT, NEEDS_CLARIFICATION
    reason = Column(Text)  # Decision reasoning
    decided_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "decision IN ('VERIFIED','NON_COMPLIANT','NEEDS_CLARIFICATION')"
        ),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = uuid_col()
    event_type = Column(Text, nullable=False)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    payload = Column(JSON, nullable=False)
    prev_hash = Column(Text)
    event_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ============================================================================
# PHASE 1: STATE MACHINE + DOCUMENT VERSIONING
# ============================================================================

class BidState(Base):
    """Track bid state transitions for state machine."""
    __tablename__ = "bid_states"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    state = Column(Text, nullable=False)
    entered_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    exited_at = Column(DateTime(timezone=True))
    transition_metadata = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("state IN ('DRAFT','SUBMITTED','VERIFYING','REVIEW','CLARIFICATION','RESUBMITTED','DECIDED')"),
    )


class DocumentVersion(Base):
    """Document versioning for Phase 1."""
    __tablename__ = "document_versions"
    id = uuid_col()
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)
    file_path = Column(Text, nullable=False)
    file_hash = Column(Text, nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upload_reason = Column(Text)
    supersedes_version_id = Column(UUID(as_uuid=True), ForeignKey("document_versions.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("document_id", "version_number"),
    )


# ============================================================================
# PHASE 3: OCR PROCESSING
# ============================================================================

class OCRJob(Base):
    """Track OCR processing for Phase 3."""
    __tablename__ = "ocr_jobs"
    id = uuid_col()
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False, default=1)
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(Text, nullable=False, default="PENDING")
    ocr_engine = Column(Text)
    extracted_text = Column(Text)
    extracted_entities = Column(JSON)
    text_content = Column(Text)
    confidence_score = Column(Numeric(4, 3))
    raw_response = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("status IN ('PENDING','PROCESSING','COMPLETED','FAILED')"),
    )


# ============================================================================
# PHASE 6: RISK SIGNAL DECOMPOSITION
# ============================================================================

class RiskSignalDecomposition(Base):
    """Decompose risk signals into components for Phase 6."""
    __tablename__ = "risk_signal_decompositions"
    id = uuid_col()
    risk_signal_id = Column(UUID(as_uuid=True), ForeignKey("risk_signals.id"), nullable=False)
    component_name = Column(Text, nullable=False)
    component_weight = Column(Numeric(5, 3), nullable=False)
    component_evidence = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ============================================================================
# PHASE 7: CLARIFICATION WORKFLOW
# ============================================================================

class ClarificationRequest(Base):
    """Officer requests clarification from bidder for Phase 7."""
    __tablename__ = "clarification_requests"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    question_text = Column(Text, nullable=False)
    related_clause_id = Column(UUID(as_uuid=True), ForeignKey("clauses.id"))
    related_fact_id = Column(UUID(as_uuid=True), ForeignKey("extracted_facts.id"))
    status = Column(Text, nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    resolved_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("status IN ('PENDING','RESOLVED','WITHDRAWN')"),
    )


class ClarificationResponse(Base):
    """Bidder responds to clarification request for Phase 7."""
    __tablename__ = "clarification_responses"
    id = uuid_col()
    clarification_request_id = Column(UUID(as_uuid=True), ForeignKey("clarification_requests.id"), nullable=False)
    bidder_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    response_text = Column(Text, nullable=False)
    supporting_documents = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ============================================================================
# PHASE 8: OFFICER DECISION OVERRIDES
# ============================================================================

class OfficerDecisionOverride(Base):
    """Track officer overrides of compliance results for Phase 8."""
    __tablename__ = "officer_decision_overrides"
    id = uuid_col()
    officer_decision_id = Column(UUID(as_uuid=True), ForeignKey("officer_decisions.id"), nullable=False)
    compliance_result_id = Column(UUID(as_uuid=True), ForeignKey("compliance_results.id"))
    original_compliance_status = Column(Text, nullable=False)
    override_status = Column(Text, nullable=False)
    override_evidence = Column(JSON)
    override_rule_version = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


# ============================================================================
# PHASE 13: NOTIFICATIONS
# ============================================================================

class Notification(Base):
    """User notifications for Phase 13."""
    __tablename__ = "notifications"
    id = uuid_col()
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notification_type = Column(Text, nullable=False)
    subject = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    related_bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"))
    is_read = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("notification_type IN ('STATUS_CHANGE','CLARIFICATION_REQUEST','CLARIFICATION_RESPONSE','DECISION_MADE','VERIFICATION_COMPLETE','RISK_FLAGGED')"),
    )


# ============================================================================
# VERIFICATION TABLES: Real Government Data Verification
# ============================================================================

class VerificationAttempt(Base):
    """Immutable record of each verification attempt against government sources.
    
    One record per attempt. Retries create new records with new verification_attempt_id.
    This implements the audit trail requirement: every verification is traceable.
    """
    __tablename__ = "verification_attempt"
    
    id = uuid_col()
    extracted_fact_id = Column(UUID(as_uuid=True), ForeignKey("extracted_facts.id"), nullable=False)
    source_document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    verification_provider = Column(String(50), nullable=False)  # GSTN, MCA, NSIC, UDYAM, PAN
    extracted_value = Column(Text, nullable=False)  # The actual identifier being verified
    request_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    extracted_fact = relationship("ExtractedFact", back_populates="verification_attempts")
    source_document = relationship("Document", back_populates="verification_attempts")
    verification_result = relationship(
        "VerificationResultNew", 
        back_populates="verification_attempt", 
        uselist=False,
        foreign_keys="VerificationResultNew.verification_attempt_id"
    )
    verification_name_matches = relationship(
        "VerificationNameMatch", 
        back_populates="verification_attempt"
    )


class VerificationResultNew(Base):
    """Result of a single verification attempt.
    
    Immutable: one record per VerificationAttempt.
    Contains HTTP response code, API reference, authority value, and status.
    """
    __tablename__ = "verification_result"
    
    id = uuid_col()
    verification_attempt_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("verification_attempt.id"), 
        nullable=False, 
        unique=True
    )
    api_response_code = Column(Integer)  # 200, 401, 429, 503, etc.
    api_reference_id = Column(String(255))  # Reference from authority for traceability
    authority_value = Column(Text)  # Value/name returned by authority
    authority_normalized_value = Column(Text)  # Normalized authority value
    response_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    verification_status = Column(String(20), nullable=False)  # VERIFIED, MISMATCH, UNAVAILABLE, ERROR, INCONCLUSIVE, PENDING
    fallback_used = Column(Boolean, default=False)  # True if Mock_Adapter used after Real failure
    http_error_message = Column(Text)  # Error message (without credentials)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationship
    verification_attempt = relationship(
        "VerificationAttempt", 
        back_populates="verification_result",
        foreign_keys=[verification_attempt_id],
        overlaps="verification_name_match"
    )
    verification_name_match = relationship(
        "VerificationNameMatch",
        back_populates="verification_result",
        uselist=False,
        primaryjoin="foreign(VerificationNameMatch.verification_attempt_id) == VerificationResultNew.verification_attempt_id",
        overlaps="verification_attempt"
    )
    
    __table_args__ = (
        CheckConstraint(
            "verification_status IN ('VERIFIED', 'MISMATCH', 'UNAVAILABLE', 'ERROR', 'INCONCLUSIVE', 'PENDING')",
            name='check_verification_status_new'
        ),
    )


class VerificationNameMatch(Base):
    """Record of name matching performed during verification.
    
    Stores original and normalized names from document and authority,
    plus match result and score for audit trail.
    """
    __tablename__ = "verification_name_match"
    
    id = uuid_col()
    verification_attempt_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("verification_attempt.id"), 
        nullable=False
    )
    document_name = Column(Text, nullable=False)  # Name from document
    normalized_document_name = Column(Text, nullable=False)  # Normalized document name
    authority_name = Column(Text, nullable=False)  # Name from authority API
    normalized_authority_name = Column(Text, nullable=False)  # Normalized authority name
    match_result = Column(String(20), nullable=False)  # exact_match | fuzzy_match | no_match
    match_score = Column(Numeric(5, 3), nullable=False)  # 0.0 to 1.0
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationship
    verification_attempt = relationship(
        "VerificationAttempt", 
        back_populates="verification_name_matches",
        overlaps="verification_name_match"
    )
    verification_result = relationship(
        "VerificationResultNew",
        back_populates="verification_name_match",
        primaryjoin="foreign(VerificationNameMatch.verification_attempt_id) == VerificationResultNew.verification_attempt_id",
        uselist=False,
        overlaps="verification_attempt,verification_name_matches"
    )
    
    __table_args__ = (
        CheckConstraint(
            "match_result IN ('exact_match', 'fuzzy_match', 'no_match')",
            name='check_match_result'
        ),
        CheckConstraint(
            "match_score BETWEEN 0.0 AND 1.0",
            name='check_match_score'
        ),
    )
