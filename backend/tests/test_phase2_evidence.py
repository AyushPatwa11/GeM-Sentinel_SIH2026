"""Tests for Phase 2: Evidence Traceability."""
import pytest
import uuid
from sqlalchemy.orm import Session

from app.models.models import (
    ComplianceResult, ExtractedFact, VerificationResult, Document,
    RiskSignal, Clause, Bid
)
from app.services.evidence_traceability import EvidenceTraceability


class TestPhase2EvidenceTraceability:
    """Phase 2: Evidence traceability and drill-down."""
    
    def test_trace_compliance_result_complete_chain(self, test_db: Session):
        """Test tracing compliance result through complete evidence chain."""
        # Setup: Create bid, document, fact, verification, compliance
        bid_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        fact_id = uuid.uuid4()
        verification_id = uuid.uuid4()
        compliance_id = uuid.uuid4()
        clause_id = uuid.uuid4()
        
        # Create bid
        bid = Bid(
            id=bid_id,
            tender_version_id=uuid.uuid4(),
            bidder_org_id=uuid.uuid4(),
        )
        test_db.add(bid)
        
        # Create clause
        clause = Clause(
            id=clause_id,
            tender_version_id=uuid.uuid4(),
            raw_text="Must have valid GST certificate",
            category="FINANCIAL",
            mandatory=True,
            logic_tree={"type": "leaf", "field": "gst_valid"},
        )
        test_db.add(clause)
        
        # Create document
        doc = Document(
            id=doc_id,
            bid_id=bid_id,
            file_path="/uploads/gst.pdf",
            file_hash="abc123",
            doc_type="GST_CERT",
        )
        test_db.add(doc)
        
        # Create extracted fact
        fact = ExtractedFact(
            id=fact_id,
            document_id=doc_id,
            field_name="gst_number",
            field_value="27AAFCU5055K1Z5",
            confidence=0.95,
            evidence_span="GST: 27AAFCU5055K1Z5",
            meets_threshold=True,
        )
        test_db.add(fact)
        
        # Create verification
        verification = VerificationResult(
            id=verification_id,
            extracted_fact_id=fact_id,
            adapter_source="GSTN",
            status="VERIFIED",
            checked_at=__import__("datetime").datetime.utcnow(),
            evidence="GST registration found and valid",
        )
        test_db.add(verification)
        
        # Create compliance result
        compliance = ComplianceResult(
            id=compliance_id,
            bid_id=bid_id,
            clause_id=clause_id,
            status="PASS",
            reasoning_chain={"rule": "gst_valid", "result": "pass"},
            evidence_refs=[str(fact_id)],
            rule_version="1.0",
        )
        test_db.add(compliance)
        test_db.commit()
        
        # Test trace
        trace = EvidenceTraceability.trace_compliance_result(
            test_db,
            str(compliance_id),
        )
        
        assert trace["compliance_result_id"] == str(compliance_id)
        assert trace["compliance_status"] == "PASS"
        assert len(trace["extracted_facts"]) == 1
        assert trace["extracted_facts"][0]["field_name"] == "gst_number"
        assert len(trace["documents"]) == 1
        assert len(trace["documents"][0]["verifications"]) == 1
        assert trace["documents"][0]["verifications"][0]["status"] == "VERIFIED"
    
    def test_trace_risk_signal_to_verification(self, test_db: Session):
        """Test tracing risk signal to verification result."""
        # Setup
        bid_id = uuid.uuid4()
        fact_id = uuid.uuid4()
        verification_id = uuid.uuid4()
        signal_id = uuid.uuid4()
        
        # Create fact
        fact = ExtractedFact(
            id=fact_id,
            document_id=uuid.uuid4(),
            field_name="director_name",
            field_value="John Doe",
            confidence=0.8,
            evidence_span="Director: John Doe",
            meets_threshold=True,
        )
        test_db.add(fact)
        
        # Create verification (MISMATCH)
        verification = VerificationResult(
            id=verification_id,
            extracted_fact_id=fact_id,
            adapter_source="MCA",
            status="MISMATCH",
            checked_at=__import__("datetime").datetime.utcnow(),
            evidence="Director name does not match MCA records",
        )
        test_db.add(verification)
        
        # Create risk signal
        signal = RiskSignal(
            id=signal_id,
            bid_id=bid_id,
            signal_type="DIRECTOR_MISMATCH",
            weight=0.8,
            severity=0.7,
            verification_result_id=verification_id,
        )
        test_db.add(signal)
        test_db.commit()
        
        # Test trace
        trace = EvidenceTraceability.trace_risk_signal(
            test_db,
            str(signal_id),
        )
        
        assert trace["signal_type"] == "DIRECTOR_MISMATCH"
        assert trace["source"]["type"] == "verification"
        assert trace["source"]["status"] == "MISMATCH"
        assert "Director" in trace["source"]["evidence"]
    
    def test_bid_evidence_summary(self, test_db: Session):
        """Test getting complete bid evidence summary."""
        bid_id = uuid.uuid4()
        
        # Create bid
        bid = Bid(
            id=bid_id,
            tender_version_id=uuid.uuid4(),
            bidder_org_id=uuid.uuid4(),
        )
        test_db.add(bid)
        
        # Create 2 documents
        for i in range(2):
            doc = Document(
                id=uuid.uuid4(),
                bid_id=bid_id,
                file_path=f"/uploads/doc{i}.pdf",
                file_hash=f"hash{i}",
                doc_type=["GST_CERT", "PAN_CERT"][i],
            )
            test_db.add(doc)
        
        # Create 2 compliance results
        for i in range(2):
            compliance = ComplianceResult(
                id=uuid.uuid4(),
                bid_id=bid_id,
                clause_id=uuid.uuid4(),
                status=["PASS", "FAIL"][i],
                reasoning_chain={},
                evidence_refs=[],
                rule_version="1.0",
            )
            test_db.add(compliance)
        
        # Create 1 risk signal
        signal = RiskSignal(
            id=uuid.uuid4(),
            bid_id=bid_id,
            signal_type="TEST_SIGNAL",
            weight=0.5,
            severity=0.5,
        )
        test_db.add(signal)
        test_db.commit()
        
        # Test summary
        summary = EvidenceTraceability.get_bid_evidence_summary(test_db, str(bid_id))
        
        assert summary["bid_id"] == str(bid_id)
        assert summary["compliance_count"] == 2
        assert summary["risk_signal_count"] == 1
        assert summary["document_count"] == 2
        assert len(summary["compliance_results"]) == 2
        assert len(summary["risk_signals"]) == 1
        assert len(summary["documents"]) == 2
    
    def test_drill_down_path_single_fact(self, test_db: Session):
        """Test drill-down path from compliance through fact to verification."""
        # Setup
        clause_id = uuid.uuid4()
        compliance_id = uuid.uuid4()
        fact_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        verification_id = uuid.uuid4()
        
        # Create clause
        clause = Clause(
            id=clause_id,
            tender_version_id=uuid.uuid4(),
            raw_text="Test clause",
            category="TECHNICAL",
            mandatory=True,
            logic_tree={},
        )
        test_db.add(clause)
        
        # Create document
        doc = Document(
            id=doc_id,
            bid_id=uuid.uuid4(),
            file_path="/uploads/test.pdf",
            file_hash="testhash",
            doc_type="TEST",
        )
        test_db.add(doc)
        
        # Create fact
        fact = ExtractedFact(
            id=fact_id,
            document_id=doc_id,
            field_name="test_field",
            field_value="test_value",
            confidence=0.9,
            evidence_span="test evidence",
            meets_threshold=True,
        )
        test_db.add(fact)
        
        # Create verification
        verification = VerificationResult(
            id=verification_id,
            extracted_fact_id=fact_id,
            adapter_source="TEST_ADAPTER",
            status="VERIFIED",
            checked_at=__import__("datetime").datetime.utcnow(),
        )
        test_db.add(verification)
        
        # Create compliance
        compliance = ComplianceResult(
            id=compliance_id,
            bid_id=uuid.uuid4(),
            clause_id=clause_id,
            status="PASS",
            reasoning_chain={},
            evidence_refs=[str(fact_id)],
            rule_version="1.0",
        )
        test_db.add(compliance)
        test_db.commit()
        
        # Test drill-down
        chain = EvidenceTraceability.get_drill_down_path(
            test_db,
            str(compliance_id),
        )
        
        # Should have: compliance → clause → fact → document → verification
        assert len(chain) >= 3
        assert chain[0].level == "compliance"
        
        # Find fact in chain
        fact_links = [link for link in chain if link.level == "fact"]
        assert len(fact_links) > 0
        assert fact_links[0].details["field_name"] == "test_field"
