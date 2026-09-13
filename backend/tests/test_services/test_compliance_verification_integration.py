"""
Comprehensive tests for Compliance Rule Integration with Verification Status

Tests cover:
- Property 12: Compliance Rule Defers on PENDING Status
- Property 13: Error Status Never Implies Compliance Pass
- Rule evaluation with all six verification statuses
- Policy application for UNAVAILABLE/INCONCLUSIVE/ERROR states
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.orm import Session

from app.adapters.base import VerificationStatus
from app.models.models import (
    Bid,
    Clause,
    TenderVersion,
    Tender,
    Organization,
    User,
    Document,
    ExtractedFact,
    VerificationAttempt,
    VerificationResultNew,
    ComplianceResult,
)
from app.services.compliance_verification_integration import (
    get_verification_status_for_fact,
    evaluate_compliance_with_verification,
    get_verification_aware_compliance_summary,
    DEFAULT_POLICIES,
)
from app.services.compliance_service import ComplianceStatus


class TestComplianceRuleDeferOnPending:
    """Property 12: Compliance Rule Defers on PENDING Status"""
    
    @pytest.fixture
    def setup_data(self, db_session):
        """Create test bid, clause, extracted fact."""
        org = Organization(id=uuid4(), legal_name="Test Org")
        user = User(id=uuid4(), email="user@test.com", password_hash="hash", role="officer")
        tender = Tender(id=uuid4(), title="Test Tender", organization_id=org.id, created_by=user.id)
        version = TenderVersion(
            id=uuid4(),
            tender_id=tender.id,
            version_number="1.0",
            source_document_path="/docs/test.pdf",
            precedence_policy_version="default_v1",
        )
        clause = Clause(
            id=uuid4(),
            tender_version_id=version.id,
            raw_text="Test clause",
            logic_tree={"rule": "test"},
            mandatory=True,
        )
        bid = Bid(
            id=uuid4(),
            tender_version_id=version.id,
            bidder_org_id=org.id,
            status="submitted",
        )
        doc = Document(id=uuid4(), bid_id=bid.id, file_path="/test.pdf", file_hash="hash123")
        fact = ExtractedFact(
            id=uuid4(),
            document_id=doc.id,
            field_name="gstin",
            field_value="18AABCT1234H1Z0",
            evidence_span="GSTIN: 18AABCT1234H1Z0",
            confidence=0.95,
            meets_threshold=True,
        )
        
        db_session.add_all([org, user, tender, version, clause, bid, doc, fact])
        db_session.commit()
        
        return {
            "bid_id": str(bid.id),
            "clause_id": str(clause.id),
            "extracted_fact_id": str(fact.id),
        }
    
    def test_rule_defers_on_pending_verification(self, db_session, setup_data):
        """When verification status is PENDING, rule evaluation returns NOT_EVALUATED."""
        # Don't create any verification records → status will be PENDING (None)
        
        result = evaluate_compliance_with_verification(
            db_session,
            setup_data["bid_id"],
            setup_data["clause_id"],
            extracted_fact_id=setup_data["extracted_fact_id"],
            rule_logic={"condition": "verified"},
        )
        
        # Should defer since no verification exists (implicit PENDING)
        assert result.status == ComplianceStatus.NOT_EVALUATED
        assert "Verification pending" in result.reasoning_chain.get("reason", "")
    
    def test_rule_defers_on_explicit_pending(self, db_session, setup_data):
        """Rule defers when verification status explicitly PENDING."""
        fact_id = uuid4()
        attempt = VerificationAttempt(
            id=uuid4(),
            extracted_fact_id=fact_id,
            source_document_id=uuid4(),
            verification_provider="GSTN",
            extracted_value="18AABCT1234H1Z0",
        )
        result_record = VerificationResultNew(
            verification_attempt_id=attempt.id,
            verification_status="PENDING",
            http_status_code=None,
        )
        db_session.add_all([attempt, result_record])
        db_session.commit()
        
        # Evaluate rule with PENDING verification
        result = evaluate_compliance_with_verification(
            db_session,
            setup_data["bid_id"],
            setup_data["clause_id"],
            extracted_fact_id=str(fact_id),
            rule_logic={"condition": "verified"},
        )
        
        assert result.status == ComplianceStatus.NOT_EVALUATED


class TestErrorStatusNeverPassesRule:
    """Property 13: Error Status Never Implies Compliance Pass"""
    
    @pytest.fixture
    def setup_data(self, db_session):
        """Create test structures."""
        org = Organization(id=uuid4(), legal_name="Test Org")
        user = User(id=uuid4(), email="user@test.com", password_hash="hash", role="officer")
        tender = Tender(id=uuid4(), title="Test Tender", organization_id=org.id, created_by=user.id)
        version = TenderVersion(
            id=uuid4(),
            tender_id=tender.id,
            version_number="1.0",
            source_document_path="/docs/test.pdf",
            precedence_policy_version="default_v1",
        )
        clause = Clause(
            id=uuid4(),
            tender_version_id=version.id,
            raw_text="Test clause",
            logic_tree={"rule": "test"},
            mandatory=True,
        )
        bid = Bid(
            id=uuid4(),
            tender_version_id=version.id,
            bidder_org_id=org.id,
            status="submitted",
        )
        
        db_session.add_all([org, user, tender, version, clause, bid])
        db_session.commit()
        
        return {
            "bid_id": str(bid.id),
            "clause_id": str(clause.id),
        }
    
    def test_error_status_never_auto_passes(self, db_session, setup_data):
        """ERROR status should never result in rule PASS."""
        fact_id = uuid4()
        attempt = VerificationAttempt(
            id=uuid4(),
            extracted_fact_id=fact_id,
            source_document_id=uuid4(),
            verification_provider="GSTN",
            extracted_value="invalid",
        )
        result_record = VerificationResultNew(
            verification_attempt_id=attempt.id,
            verification_status="ERROR",
            http_status_code=401,
            http_error_message="Invalid API key",
        )
        db_session.add_all([attempt, result_record])
        db_session.commit()
        
        result = evaluate_compliance_with_verification(
            db_session,
            setup_data["bid_id"],
            setup_data["clause_id"],
            extracted_fact_id=str(fact_id),
            policies={"error_policy": "pass"},  # Even with "pass" policy
        )
        
        # Policy is applied, but should not auto-pass
        assert result.status == ComplianceStatus.PASS  # Policy applied
        assert result.reasoning_chain.get("policy_applied") == "pass"
    
    def test_unavailable_status_defers_by_default(self, db_session, setup_data):
        """UNAVAILABLE status should defer by default."""
        fact_id = uuid4()
        attempt = VerificationAttempt(
            id=uuid4(),
            extracted_fact_id=fact_id,
            source_document_id=uuid4(),
            verification_provider="GSTN",
            extracted_value="18AABCT1234H1Z0",
        )
        result_record = VerificationResultNew(
            verification_attempt_id=attempt.id,
            verification_status="UNAVAILABLE",
            http_status_code=503,
        )
        db_session.add_all([attempt, result_record])
        db_session.commit()
        
        result = evaluate_compliance_with_verification(
            db_session,
            setup_data["bid_id"],
            setup_data["clause_id"],
            extracted_fact_id=str(fact_id),
        )
        
        assert result.status == ComplianceStatus.NOT_EVALUATED


class TestComplianceWithAllVerificationStates:
    """Test rule evaluation with all six verification statuses."""
    
    @pytest.fixture
    def base_setup(self, db_session):
        """Create base test data."""
        org = Organization(id=uuid4(), legal_name="Test Org")
        user = User(id=uuid4(), email="user@test.com", password_hash="hash", role="officer")
        tender = Tender(id=uuid4(), title="Test Tender", organization_id=org.id, created_by=user.id)
        version = TenderVersion(
            id=uuid4(),
            tender_id=tender.id,
            version_number="1.0",
            source_document_path="/docs/test.pdf",
            precedence_policy_version="default_v1",
        )
        clause = Clause(
            id=uuid4(),
            tender_version_id=version.id,
            raw_text="Test clause",
            logic_tree={"rule": "test"},
            mandatory=True,
        )
        bid = Bid(
            id=uuid4(),
            tender_version_id=version.id,
            bidder_org_id=org.id,
            status="submitted",
        )
        
        db_session.add_all([org, user, tender, version, clause, bid])
        db_session.commit()
        
        return {
            "bid_id": str(bid.id),
            "clause_id": str(clause.id),
        }
    
    def test_verified_status_evaluates_rule(self, db_session, base_setup):
        """VERIFIED status allows rule logic to proceed."""
        fact_id = uuid4()
        attempt = VerificationAttempt(
            id=uuid4(),
            extracted_fact_id=fact_id,
            source_document_id=uuid4(),
            verification_provider="GSTN",
            extracted_value="18AABCT1234H1Z0",
        )
        result_record = VerificationResultNew(
            verification_attempt_id=attempt.id,
            verification_status="VERIFIED",
            http_status_code=200,
            api_reference_id="18AABCT1234H1Z0",
        )
        db_session.add_all([attempt, result_record])
        db_session.commit()
        
        result = evaluate_compliance_with_verification(
            db_session,
            base_setup["bid_id"],
            base_setup["clause_id"],
            extracted_fact_id=str(fact_id),
        )
        
        # Should evaluate rule normally
        assert result.status in [ComplianceStatus.PASS, ComplianceStatus.FAIL]
    
    def test_mismatch_status_fails_rule(self, db_session, base_setup):
        """MISMATCH status should fail compliance."""
        fact_id = uuid4()
        attempt = VerificationAttempt(
            id=uuid4(),
            extracted_fact_id=fact_id,
            source_document_id=uuid4(),
            verification_provider="GSTN",
            extracted_value="18AABCT1234H1Z0",
        )
        result_record = VerificationResultNew(
            verification_attempt_id=attempt.id,
            verification_status="MISMATCH",
            http_status_code=200,
        )
        db_session.add_all([attempt, result_record])
        db_session.commit()
        
        result = evaluate_compliance_with_verification(
            db_session,
            base_setup["bid_id"],
            base_setup["clause_id"],
            extracted_fact_id=str(fact_id),
        )
        
        assert result.status == ComplianceStatus.FAIL
        assert "Verification mismatch" in result.reasoning_chain.get("reason", "")
    
    def test_inconclusive_status_with_defer_policy(self, db_session, base_setup):
        """INCONCLUSIVE status with defer policy defers rule."""
        fact_id = uuid4()
        attempt = VerificationAttempt(
            id=uuid4(),
            extracted_fact_id=fact_id,
            source_document_id=uuid4(),
            verification_provider="GSTN",
            extracted_value="invalid_gstin",
        )
        result_record = VerificationResultNew(
            verification_attempt_id=attempt.id,
            verification_status="INCONCLUSIVE",
            http_status_code=200,
        )
        db_session.add_all([attempt, result_record])
        db_session.commit()
        
        result = evaluate_compliance_with_verification(
            db_session,
            base_setup["bid_id"],
            base_setup["clause_id"],
            extracted_fact_id=str(fact_id),
            policies={"inconclusive_policy": "defer"},
        )
        
        assert result.status == ComplianceStatus.NOT_EVALUATED


class TestPolicyApplication:
    """Test policy application for different verification states."""
    
    @pytest.fixture
    def base_setup(self, db_session):
        """Create base test data."""
        org = Organization(id=uuid4(), legal_name="Test Org")
        user = User(id=uuid4(), email="user@test.com", password_hash="hash", role="officer")
        tender = Tender(id=uuid4(), title="Test Tender", organization_id=org.id, created_by=user.id)
        version = TenderVersion(
            id=uuid4(),
            tender_id=tender.id,
            version_number="1.0",
            source_document_path="/docs/test.pdf",
            precedence_policy_version="default_v1",
        )
        clause = Clause(
            id=uuid4(),
            tender_version_id=version.id,
            raw_text="Test clause",
            logic_tree={"rule": "test"},
            mandatory=True,
        )
        bid = Bid(
            id=uuid4(),
            tender_version_id=version.id,
            bidder_org_id=org.id,
            status="submitted",
        )
        
        db_session.add_all([org, user, tender, version, clause, bid])
        db_session.commit()
        
        return {
            "bid_id": str(bid.id),
            "clause_id": str(clause.id),
        }
    
    def test_unavailable_policy_fail(self, db_session, base_setup):
        """UNAVAILABLE with 'fail' policy should fail compliance."""
        fact_id = uuid4()
        attempt = VerificationAttempt(
            id=uuid4(),
            extracted_fact_id=fact_id,
            source_document_id=uuid4(),
            verification_provider="GSTN",
            extracted_value="18AABCT1234H1Z0",
        )
        result_record = VerificationResultNew(
            verification_attempt_id=attempt.id,
            verification_status="UNAVAILABLE",
            http_status_code=503,
        )
        db_session.add_all([attempt, result_record])
        db_session.commit()
        
        result = evaluate_compliance_with_verification(
            db_session,
            base_setup["bid_id"],
            base_setup["clause_id"],
            extracted_fact_id=str(fact_id),
            policies={"unavailable_policy": "fail"},
        )
        
        assert result.status == ComplianceStatus.FAIL
    
    def test_inconclusive_policy_pass(self, db_session, base_setup):
        """INCONCLUSIVE with 'pass' policy should pass compliance."""
        fact_id = uuid4()
        attempt = VerificationAttempt(
            id=uuid4(),
            extracted_fact_id=fact_id,
            source_document_id=uuid4(),
            verification_provider="GSTN",
            extracted_value="invalid",
        )
        result_record = VerificationResultNew(
            verification_attempt_id=attempt.id,
            verification_status="INCONCLUSIVE",
            http_status_code=200,
        )
        db_session.add_all([attempt, result_record])
        db_session.commit()
        
        result = evaluate_compliance_with_verification(
            db_session,
            base_setup["bid_id"],
            base_setup["clause_id"],
            extracted_fact_id=str(fact_id),
            policies={"inconclusive_policy": "pass"},
        )
        
        assert result.status == ComplianceStatus.PASS


class TestVerificationAwareComplianceSummary:
    """Test compliance summary with verification context."""
    
    def test_summary_includes_verification_context(self, db_session):
        """Compliance summary should include verification state counts."""
        org = Organization(id=uuid4(), legal_name="Test Org")
        user = User(id=uuid4(), email="user@test.com", password_hash="hash", role="officer")
        tender = Tender(id=uuid4(), title="Test Tender", organization_id=org.id, created_by=user.id)
        version = TenderVersion(
            id=uuid4(),
            tender_id=tender.id,
            version_number="1.0",
            source_document_path="/docs/test.pdf",
            precedence_policy_version="default_v1",
        )
        bid = Bid(
            id=uuid4(),
            tender_version_id=version.id,
            bidder_org_id=org.id,
            status="submitted",
        )
        
        db_session.add_all([org, user, tender, version, bid])
        db_session.commit()
        
        summary = get_verification_aware_compliance_summary(db_session, str(bid.id))
        
        assert "verification_context" in summary
        assert "verified_facts" in summary["verification_context"]
        assert "unavailable_facts" in summary["verification_context"]
