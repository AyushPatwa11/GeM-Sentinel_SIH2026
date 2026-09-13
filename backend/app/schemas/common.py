"""Common request/response schemas for Phase 2+."""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


# ============================================================================
# TENDER SCHEMAS (Phase 2)
# ============================================================================

class TenderCreateRequest(BaseModel):
    """Create tender request."""
    title: str
    description: Optional[str] = ""
    deadline: datetime
    version_number: Optional[str] = "1.0"
    required_documents: Optional[List[str]] = []
    source_document_path: Optional[str] = None


class TenderResponse(BaseModel):
    """Tender response with details."""
    id: str
    title: str
    status: str
    created_by: str
    organization_id: str
    version_number: str
    published_at: Optional[str] = None
    created_at: str
    required_documents: List[str] = []
    clause_count: int = 0
    
    class Config:
        from_attributes = True


class TenderPublishRequest(BaseModel):
    """Publish tender request."""
    pass  # Endpoint path determines action


# ============================================================================
# BID SCHEMAS (Phase 2-3)
# ============================================================================

class BidCreateRequest(BaseModel):
    """Create bid request."""
    pass  # Endpoint path determines action


class BidResponse(BaseModel):
    """Bid response with details."""
    id: str
    tender_id: str
    tender_version_id: str
    bidder_org_id: str
    status: str
    current_state: str
    submitted_at: Optional[str] = None
    created_at: str
    
    class Config:
        from_attributes = True


class BidStatusResponse(BaseModel):
    """Bid status for bidder viewing."""
    status: str
    current_state: str
    decision: Optional[str] = None
    compliance_status: Optional[str] = None
    risk_level: Optional[str] = None
    submitted_at: Optional[str] = None
    current_step: str


# ============================================================================
# DOCUMENT SCHEMAS (Phase 3)
# ============================================================================

class DocumentResponse(BaseModel):
    """Document response."""
    id: str
    bid_id: str
    doc_type: str
    file_hash: str
    ocr_status: str
    current_version: int
    uploaded_at: str
    
    class Config:
        from_attributes = True


class DocumentVersionResponse(BaseModel):
    """Document version response."""
    version_number: int
    file_hash: str
    uploaded_at: str
    uploaded_by: Optional[str] = None
    change_reason: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Document upload response."""
    document_id: str
    version_number: int
    file_hash: str
    ocr_job_id: str
    message: str


class OCRStatusResponse(BaseModel):
    """OCR job status response."""
    job_id: str
    status: str  # PENDING, PROCESSING, COMPLETED, FAILED
    version_number: int
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    extracted_text: Optional[str] = None
    entities: Optional[dict] = None


class OCREntityResponse(BaseModel):
    """Extracted entity from OCR."""
    entity_type: str
    values: List[str]


# ============================================================================
# EXTERNAL VERIFICATION SCHEMAS (Phase 5)
# ============================================================================

class VerificationClaimRequest(BaseModel):
    """Verification claim request."""
    fact_type: str  # GSTIN, PAN, COMPANY_NAME, etc.
    extracted_value: str
    entity_name: Optional[str] = None


class VerificationResultResponse(BaseModel):
    """Single verification result."""
    fact_type: str
    extracted_value: str
    verification_status: str  # VERIFIED, MISMATCH, INCONCLUSIVE, UNAVAILABLE, ERROR
    api_response_code: Optional[int] = None
    authority_value: Optional[str] = None
    match_result: Optional[str] = None  # exact_match, fuzzy_match, no_match
    match_score: Optional[float] = None
    verified_at: Optional[str] = None


class BidVerificationResponse(BaseModel):
    """Comprehensive bid verification results."""
    bid_id: str
    overall_status: str  # ALL_VERIFIED, PARTIAL_FAILURE
    total_facts: int
    verified_count: int
    mismatch_count: int
    unavailable_count: int
    inconclusive_count: int
    error_count: int
    verification_results: List[dict]


class NameMatchResultResponse(BaseModel):
    """Name matching result."""
    document_name: str
    authority_name: str
    match_result: str  # exact_match, fuzzy_match, no_match
    match_score: float
    """Compliance rule details."""
    id: str
    name: str
    description: str
    rule_type: str
    severity: str
    version: str
    applicable_contexts: List[str]


class BidComplianceEvaluationResponse(BaseModel):
    """Comprehensive bid compliance evaluation."""
    overall_status: str  # COMPLIANT, NON_COMPLIANT, REQUIRES_REVIEW
    passed_count: int
    failed_count: int
    total_rules: int
    risk_signals_triggered: int
    rule_results: List[dict]


class EvidenceChainResponse(BaseModel):
    """Evidence chain for compliance decision."""
    compliance_result_id: str
    chain_hash: str
    evidence_count: int
    created_at: str


class RiskSignalResponse(BaseModel):
    """Risk signal details."""
    signal_id: str
    bid_id: str
    signal_type: str
    weight: float
    severity: float
    created_at: Optional[str] = None
    """Stage 1 verification response (document slots)."""
    passed: bool
    slots: List[dict]  # [{type, uploaded}]
    uploaded_mandatory: int
    total_mandatory: int


class Stage2VerificationResponse(BaseModel):
    """Stage 2 verification response (compliance)."""
    compliance_status: str  # COMPLIANT, NON_COMPLIANT
    rule_results: List[dict]  # [{rule, passed, explanation}]


# ============================================================================
# RISK SCHEMAS (Phase 6)
# ============================================================================

class RiskAssessmentResponse(BaseModel):
    """Risk assessment response."""
    overall_risk_score: float
    risk_level: str  # LOW, MEDIUM, HIGH
    signal_breakdown: dict  # {high_count, medium_count, low_count}
    assessed_at: str


class RiskScoringResultResponse(BaseModel):
    """Comprehensive risk scoring result."""
    total_score: float
    risk_level: str
    signal_count: int
    signals_by_type: dict
    signal_breakdown: dict
    risk_factors: List[dict]
    mitigating_factors: List[dict]


class RiskDecompositionResponse(BaseModel):
    """Risk score decomposition by source."""
    total_contribution: float
    sources: List[dict]


class RiskRecommendationResponse(BaseModel):
    """Recommended action based on risk."""
    priority: str
    action: str
    reason: str
    details: str

# ============================================================================
# DECISION SCHEMAS (Phase 8)
# ============================================================================

class MakeDecisionRequest(BaseModel):
    """Officer decision request."""
    final_decision: str  # VERIFIED, NON_COMPLIANT
    override_reason: Optional[str] = None


class DecisionResponse(BaseModel):
    """Officer decision response."""
    decision_id: str
    final_decision: str
    decided_at: str
    decided_by: str
    override_status: Optional[str] = None
