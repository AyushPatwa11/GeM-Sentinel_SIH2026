"""Tests for Phases 1-13: State Machine through Notifications."""
import pytest
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.models import (
    Bid, BidState, Document, DocumentVersion, OCRJob,
    ClarificationRequest, ClarificationResponse, OfficerDecision,
    Notification, ComplianceResult, RiskSignal, RiskAssessment
)
from app.services.state_machine import BidStateMachine, BidStatus
from app.services.document_service import DocumentService
from app.services.ocr_service import OCRService
from app.services.verification_service import VerificationService
from app.services.compliance_service import ComplianceService
from app.services.risk_service import RiskService
from app.services.clarification_service import ClarificationService
from app.services.officer_decision_service import OfficerDecisionService
from app.services.notification_service import NotificationService


class TestPhase1StateMachine:
    """Phase 1: State Machine transitions."""
    
    def test_bid_created_in_draft_state(self, test_db: Session, test_user_bidder):
        """Test that new bid starts in DRAFT state."""
        # Create bid
        bid = Bid(
            id=uuid.uuid4(),
            tender_version_id=uuid.uuid4(),
            bidder_org_id=uuid.uuid4(),
            status="draft",
            current_state="DRAFT",
        )
        test_db.add(bid)
        test_db.commit()
        
        assert bid.current_state == BidStatus.DRAFT
    
    def test_valid_state_transition(self, test_db: Session, test_user_bidder):
        """Test valid state transition DRAFT → SUBMITTED."""
        bid_id = uuid.uuid4()
        bid = Bid(
            id=bid_id,
            tender_version_id=uuid.uuid4(),
            bidder_org_id=uuid.uuid4(),
            status="draft",
            current_state="DRAFT",
        )
        test_db.add(bid)
        test_db.commit()
        
        # Transition DRAFT → SUBMITTED
        updated = BidStateMachine.transition(
            test_db,
            str(bid_id),
            BidStatus.SUBMITTED,
            str(test_user_bidder.id),
            {"reason": "test"},
        )
        
        assert updated.current_state == BidStatus.SUBMITTED
    
    def test_invalid_state_transition_rejected(self, test_db: Session, test_user_bidder):
        """Test that invalid transitions are rejected."""
        bid = Bid(
            id=uuid.uuid4(),
            tender_version_id=uuid.uuid4(),
            bidder_org_id=uuid.uuid4(),
            status="draft",
            current_state="DECIDED",
        )
        test_db.add(bid)
        test_db.commit()
        
        # Try invalid transition DECIDED → DRAFT
        with pytest.raises(ValueError, match="Invalid transition"):
            BidStateMachine.transition(
                test_db,
                str(bid.id),
                BidStatus.DRAFT,
                str(test_user_bidder.id),
            )
    
    def test_state_history_tracking(self, test_db: Session, test_user_bidder):
        """Test that state transitions are tracked in history."""
        bid = Bid(
            id=uuid.uuid4(),
            tender_version_id=uuid.uuid4(),
            bidder_org_id=uuid.uuid4(),
            status="draft",
            current_state="DRAFT",
        )
        test_db.add(bid)
        test_db.commit()
        
        # Multiple transitions
        for target_state in [BidStatus.SUBMITTED, BidStatus.VERIFYING]:
            BidStateMachine.transition(
                test_db,
                str(bid.id),
                target_state,
                str(test_user_bidder.id),
            )
        
        history = BidStateMachine.get_state_history(test_db, str(bid.id))
        
        assert len(history) == 2  # DRAFT → SUBMITTED, SUBMITTED → VERIFYING
        assert history[0]["state"] == BidStatus.SUBMITTED
        assert history[1]["state"] == BidStatus.VERIFYING


class TestPhase1DocumentVersioning:
    """Phase 1: Document versioning."""
    
    def test_create_document_with_initial_version(self, test_db: Session, test_user_bidder):
        """Test document creation with v1."""
        doc = DocumentService.create_document(
            test_db,
            str(uuid.uuid4()),
            "/uploads/test.pdf",
            "abcd1234",
            "GST_CERT",
            str(test_user_bidder.id),
        )
        
        assert doc.current_version == 1
        
        versions = DocumentService.get_version_history(test_db, str(doc.id))
        assert len(versions) == 1
        assert versions[0]["version_number"] == 1
    
    def test_upload_new_document_version(self, test_db: Session, test_user_bidder):
        """Test uploading new version of document."""
        doc = DocumentService.create_document(
            test_db,
            str(uuid.uuid4()),
            "/uploads/test_v1.pdf",
            "abcd1234",
            "GST_CERT",
            str(test_user_bidder.id),
        )
        
        # Upload v2
        v2 = DocumentService.upload_new_version(
            test_db,
            str(doc.id),
            "/uploads/test_v2.pdf",
            "efgh5678",
            str(test_user_bidder.id),
            "Updated GST certificate",
        )
        
        assert v2.version_number == 2
        
        updated_doc = DocumentService.get_document(test_db, str(doc.id))
        assert updated_doc.current_version == 2
        
        history = DocumentService.get_version_history(test_db, str(doc.id))
        assert len(history) == 2
    
    def test_version_immutability(self, test_db: Session, test_user_bidder):
        """Test that old versions are preserved."""
        doc = DocumentService.create_document(
            test_db,
            str(uuid.uuid4()),
            "/uploads/test_v1.pdf",
            "hash_v1",
            "PAN",
            str(test_user_bidder.id),
        )
        
        v1_id = doc.id
        original_hash = doc.file_hash
        
        # Upload v2
        DocumentService.upload_new_version(
            test_db,
            str(doc.id),
            "/uploads/test_v2.pdf",
            "hash_v2",
            str(test_user_bidder.id),
        )
        
        # Verify v1 is still accessible
        v1 = DocumentService.get_version(test_db, str(v1_id), 1)
        assert v1 is not None
        assert v1.file_hash == original_hash


class TestPhase3OCRExtraction:
    """Phase 3: OCR processing and field extraction."""
    
    def test_create_ocr_job(self, test_db: Session):
        """Test creating OCR job."""
        doc_id = str(uuid.uuid4())
        job = OCRService.create_ocr_job(test_db, doc_id, "TESSERACT_v5")
        
        assert job.status == "PENDING"
        assert job.ocr_engine == "TESSERACT_v5"
    
    def test_update_ocr_job_completion(self, test_db: Session):
        """Test updating OCR job with results."""
        doc_id = str(uuid.uuid4())
        job = OCRService.create_ocr_job(test_db, doc_id)
        
        updated = OCRService.update_ocr_job(
            test_db,
            str(job.id),
            "COMPLETED",
            text_content="GST Number: 27AAFCU5055K1Z5",
            confidence_score=0.95,
        )
        
        assert updated.status == "COMPLETED"
        assert updated.text_content is not None
        assert float(updated.confidence_score) == 0.95


class TestPhase5Compliance:
    """Phase 5: Deterministic compliance with immutability."""
    
    def test_create_compliance_result_immutable(self, test_db: Session, test_user_officer):
        """Test that compliance results are created as immutable."""
        result = ComplianceService.evaluate_compliance(
            test_db,
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            "PASS",
            {"rules_checked": ["GST_VALID"]},
            ["fact_id_1"],
            "1.0",
            str(test_user_officer.id),
        )
        
        assert result.is_immutable is True
        assert result.status == "PASS"
    
    def test_compliance_cannot_be_mutated(self, test_db: Session, test_user_officer):
        """Test that compliance results preserve original status even with overrides."""
        bid_id = str(uuid.uuid4())
        clause_id = str(uuid.uuid4())
        
        # Create FAIL result
        result = ComplianceService.evaluate_compliance(
            test_db,
            bid_id,
            clause_id,
            "FAIL",
            {"reason": "GST_INVALID"},
            [],
            "1.0",
            str(test_user_officer.id),
        )
        
        original_status = result.status
        
        # Verify result is still FAIL
        retrieved = ComplianceService.get_compliance_result(test_db, str(result.id))
        assert retrieved.status == original_status
        assert retrieved.is_immutable is True


class TestPhase6RiskScoring:
    """Phase 6: Risk scoring and signal decomposition."""
    
    def test_create_risk_signal(self, test_db: Session):
        """Test creating risk signal."""
        signal = RiskService.create_risk_signal(
            test_db,
            str(uuid.uuid4()),
            "FAILED_VERIFICATION",
            weight=0.8,
            severity=0.7,
        )
        
        assert signal.signal_type == "FAILED_VERIFICATION"
        assert float(signal.weight) == 0.8
    
    def test_risk_assessment(self, test_db: Session):
        """Test creating risk assessment."""
        bid_id = str(uuid.uuid4())
        
        assessment = RiskService.assess_risk(
            test_db,
            bid_id,
            total_score=65.5,
            risk_level="MEDIUM",
        )
        
        assert float(assessment.total_score) == 65.5
        assert assessment.risk_level == "MEDIUM"


class TestPhase7Clarification:
    """Phase 7: Clarification workflow."""
    
    def test_create_clarification_request(self, test_db: Session, test_user_officer):
        """Test officer creating clarification request."""
        request = ClarificationService.create_request(
            test_db,
            str(uuid.uuid4()),
            str(test_user_officer.id),
            "Can you provide updated GST certificate?",
        )
        
        assert request.status == "PENDING"
        assert "GST" in request.question_text
    
    def test_bidder_responds_to_clarification(self, test_db: Session, test_user_bidder, test_user_officer):
        """Test bidder responding to clarification."""
        bid_id = str(uuid.uuid4())
        
        request = ClarificationService.create_request(
            test_db,
            bid_id,
            str(test_user_officer.id),
            "Provide latest GST certificate",
        )
        
        response = ClarificationService.respond_to_request(
            test_db,
            str(request.id),
            str(test_user_bidder.id),
            "Attached updated GST certificate",
        )
        
        assert response.response_text is not None
        
        responses = ClarificationService.get_request_responses(
            test_db,
            str(request.id),
        )
        assert len(responses) == 1


class TestPhase8OfficerDecisionOverride:
    """Phase 8: Officer decisions with override tracking."""
    
    def test_make_officer_decision(self, test_db: Session, test_user_officer):
        """Test officer making decision."""
        decision = OfficerDecisionService.make_decision(
            test_db,
            str(uuid.uuid4()),
            str(test_user_officer.id),
            "NON_COMPLIANT",
            "VERIFIED",
            "Documents appear legitimate despite initial concerns",
        )
        
        assert decision.final_decision == "VERIFIED"
        assert decision.override_reason is not None
    
    def test_override_preserves_compliance_immutability(self, test_db: Session, test_user_officer):
        """Test that compliance result stays immutable even with override."""
        bid_id = str(uuid.uuid4())
        
        # Create compliance result FAIL
        compliance = ComplianceService.evaluate_compliance(
            test_db,
            bid_id,
            str(uuid.uuid4()),
            "FAIL",
            {},
            [],
            "1.0",
        )
        
        # Make officer decision that overrides
        decision = OfficerDecisionService.make_decision(
            test_db,
            bid_id,
            str(test_user_officer.id),
            "NON_COMPLIANT",
            "VERIFIED",
            "Manual review found documents valid",
        )
        
        # Record override
        override = OfficerDecisionService.record_override(
            test_db,
            str(decision.id),
            str(compliance.id),
            "FAIL",
            "VERIFIED",
            override_evidence={"manual_review": True},
            actor_id=str(test_user_officer.id),
        )
        
        # Verify original compliance is still FAIL (immutable)
        retrieved_compliance = ComplianceService.get_compliance_result(test_db, str(compliance.id))
        assert retrieved_compliance.status == "FAIL"
        assert retrieved_compliance.is_immutable is True
        
        # Verify override is separate record
        assert override.original_compliance_status == "FAIL"
        assert override.override_status == "VERIFIED"


class TestPhase13Notifications:
    """Phase 13: Notifications."""
    
    def test_create_notification(self, test_db: Session, test_user_bidder):
        """Test creating notification."""
        notif = NotificationService.create_notification(
            test_db,
            str(test_user_bidder.id),
            "STATUS_CHANGE",
            "Bid Status Updated",
            "Your bid has been moved to VERIFYING state",
            str(uuid.uuid4()),
        )
        
        assert notif.is_read is False
        assert notif.email_sent is False
    
    def test_mark_notification_read(self, test_db: Session, test_user_bidder):
        """Test marking notification as read."""
        notif = NotificationService.create_notification(
            test_db,
            str(test_user_bidder.id),
            "DECISION_MADE",
            "Decision Made",
            "Officer has decided on your bid",
        )
        
        NotificationService.mark_read(test_db, str(notif.id))
        
        retrieved = NotificationService.get_notification(test_db, str(notif.id))
        assert retrieved.is_read is True
    
    def test_get_unread_notifications(self, test_db: Session, test_user_bidder):
        """Test getting unread notifications."""
        for i in range(3):
            NotificationService.create_notification(
                test_db,
                str(test_user_bidder.id),
                "STATUS_CHANGE",
                f"Update {i}",
                f"Message {i}",
            )
        
        unread = NotificationService.get_user_notifications(
            test_db,
            str(test_user_bidder.id),
            unread_only=True,
        )
        
        assert len(unread) == 3


class TestPhaseIntegration:
    """Integration tests across phases."""
    
    def test_complete_bid_workflow(self, test_db: Session, test_user_bidder, test_user_officer):
        """Test complete workflow: create bid → submit → verify → decide."""
        bid_id = str(uuid.uuid4())
        tender_version_id = str(uuid.uuid4())
        bidder_org_id = str(uuid.uuid4())
        
        # Create bid (Phase 0)
        bid = Bid(
            id=bid_id,
            tender_version_id=tender_version_id,
            bidder_org_id=bidder_org_id,
            status="draft",
            current_state="DRAFT",
        )
        test_db.add(bid)
        test_db.commit()
        
        # Initialize state machine
        BidStateMachine.transition(
            test_db,
            bid_id,
            BidStatus.DRAFT,
            str(test_user_bidder.id),
        )
        
        # Submit bid (Phase 1)
        BidStateMachine.transition(
            test_db,
            bid_id,
            BidStatus.SUBMITTED,
            str(test_user_bidder.id),
        )
        
        # Verify bid (Phase 4)
        BidStateMachine.transition(
            test_db,
            bid_id,
            BidStatus.VERIFYING,
            str(test_user_officer.id),
        )
        
        # Request clarification (Phase 7)
        ClarificationService.create_request(
            test_db,
            bid_id,
            str(test_user_officer.id),
            "Need GST certificate",
        )
        
        BidStateMachine.transition(
            test_db,
            bid_id,
            BidStatus.CLARIFICATION,
            str(test_user_officer.id),
        )
        
        # Bidder responds
        clarifications = ClarificationService.get_bid_requests(test_db, bid_id)
        ClarificationService.respond_to_request(
            test_db,
            str(clarifications[0].id),
            str(test_user_bidder.id),
            "Updated certificate attached",
        )
        
        # Make decision (Phase 8)
        decision = OfficerDecisionService.make_decision(
            test_db,
            bid_id,
            str(test_user_officer.id),
            "VERIFIED",
            "VERIFIED",
        )
        
        BidStateMachine.transition(
            test_db,
            bid_id,
            BidStatus.DECIDED,
            str(test_user_officer.id),
        )
        
        # Create notification (Phase 13)
        NotificationService.notify_decision_made(
            test_db,
            bid_id,
            str(test_user_bidder.id),
            "VERIFIED",
        )
        
        # Verify final state
        final_bid = test_db.query(Bid).filter(Bid.id == bid_id).first()
        assert final_bid.current_state == BidStatus.DECIDED
        
        # Verify decision exists
        final_decision = OfficerDecisionService.get_bid_decision(test_db, bid_id)
        assert final_decision is not None
        assert final_decision.final_decision == "VERIFIED"
