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
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(Text, nullable=False, default="draft")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

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
    logic_tree = Column(JSONB, nullable=False)
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
    submitted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    documents = relationship("Document", back_populates="bid")

    __table_args__ = (
        CheckConstraint("status IN ('draft','submitted','under_review','decided')"),
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
    uploaded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    bid = relationship("Bid", back_populates="documents")
    facts = relationship("ExtractedFact", back_populates="document")

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


class EntityResolutionResult(Base):
    __tablename__ = "entity_resolution_results"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    claimed_org_name = Column(Text, nullable=False)
    resolved_organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    match_method = Column(Text)
    identifier_conflicts = Column(JSONB)
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
    raw_response = Column(JSONB)
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
    status = Column(Text, nullable=False)
    reasoning_chain = Column(JSONB, nullable=False)
    evidence_refs = Column(JSONB, nullable=False)
    rule_version = Column(Text, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint("status IN ('PASS','FAIL','WAIVED','REVIEW','NOT_EVALUATED')"),
    )


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
    total_score = Column(Numeric(6, 3), nullable=False)
    risk_level = Column(Text)
    policy_version = Column(Text, nullable=False)
    computed_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (CheckConstraint("risk_level IN ('LOW','MEDIUM','HIGH')"),)


class OfficerDecision(Base):
    __tablename__ = "officer_decisions"
    id = uuid_col()
    bid_id = Column(UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    ai_recommendation = Column(Text, nullable=False)
    final_decision = Column(Text, nullable=False)
    override_reason = Column(Text)
    decided_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "final_decision IN ('VERIFIED','NON_COMPLIANT','NEEDS_CLARIFICATION')"
        ),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = uuid_col()
    event_type = Column(Text, nullable=False)
    entity_type = Column(Text, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    actor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    payload = Column(JSONB, nullable=False)
    prev_hash = Column(Text)
    event_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
