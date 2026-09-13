"""Compliance service for Phase 5 with immutability enforcement."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import (
    ComplianceResult, Clause, Bid, AuditEvent, OfficerDecisionOverride
)
import uuid
import hashlib


class ComplianceStatus:
    """Compliance result constants."""
    PASS = "PASS"
    FAIL = "FAIL"
    WAIVED = "WAIVED"
    REVIEW = "REVIEW"
    NOT_EVALUATED = "NOT_EVALUATED"


class ComplianceService:
    """Manage deterministic compliance evaluation with immutability."""
    
    @staticmethod
    def evaluate_compliance(
        db: Session,
        bid_id: str,
        clause_id: str,
        status: str,
        reasoning_chain: Dict[str, Any],
        evidence_refs: list,
        rule_version: str,
        actor_id: Optional[str] = None,
    ) -> ComplianceResult:
        """Create immutable compliance result.
        
        Args:
            db: Database session
            bid_id: Bid ID
            clause_id: Clause ID
            status: Compliance status (PASS, FAIL, WAIVED, REVIEW, NOT_EVALUATED)
            reasoning_chain: Detailed reasoning with proof steps
            evidence_refs: List of evidence references (fact IDs, verification IDs)
            rule_version: Version of rule engine used
            actor_id: User ID triggering evaluation
            
        Returns:
            Created ComplianceResult object
        """
        # Convert string IDs to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        clause_id_uuid = uuid.UUID(clause_id) if isinstance(clause_id, str) else clause_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id if actor_id else None
        
        # Check for existing result (should not update, only create new)
        existing = db.query(ComplianceResult).filter(
            ComplianceResult.bid_id == bid_id_uuid,
            ComplianceResult.clause_id == clause_id_uuid,
        ).order_by(ComplianceResult.evaluated_at.desc()).first()
        
        result = ComplianceResult(
            id=uuid.uuid4(),
            bid_id=bid_id_uuid,
            clause_id=clause_id_uuid,
            status=status,
            reasoning_chain=reasoning_chain,
            evidence_refs=evidence_refs,
            rule_version=rule_version,
            is_immutable=True,  # Mark as immutable
            original_status_before_override=None,  # No override yet
        )
        db.add(result)
        db.flush()
        
        # Log audit
        ComplianceService._log_audit_event(
            db,
            "COMPLIANCE_EVALUATED",
            str(bid_id_uuid),
            actor_id_uuid,
            {
                "clause_id": str(clause_id_uuid),
                "status": status,
                "rule_version": rule_version,
                "evidence_count": len(evidence_refs),
                "is_immutable": True,
            },
        )
        
        db.commit()
        return result
    
    @staticmethod
    def get_bid_compliance(db: Session, bid_id: str) -> list:
        """Get all compliance results for a bid (immutable view).
        
        Args:
            db: Database session
            bid_id: Bid ID
            
        Returns:
            List of ComplianceResult objects
        """
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        return db.query(ComplianceResult).filter(
            ComplianceResult.bid_id == bid_id_uuid
        ).order_by(ComplianceResult.evaluated_at.desc()).all()
    
    @staticmethod
    def get_clause_result(
        db: Session,
        bid_id: str,
        clause_id: str,
    ) -> Optional[ComplianceResult]:
        """Get latest compliance result for a bid/clause pair.
        
        Args:
            db: Database session
            bid_id: Bid ID
            clause_id: Clause ID
            
        Returns:
            ComplianceResult object or None
        """
        # Convert string IDs to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        clause_id_uuid = uuid.UUID(clause_id) if isinstance(clause_id, str) else clause_id
        
        return db.query(ComplianceResult).filter(
            ComplianceResult.bid_id == bid_id_uuid,
            ComplianceResult.clause_id == clause_id_uuid,
        ).order_by(ComplianceResult.evaluated_at.desc()).first()
    
    @staticmethod
    def get_compliance_result(db: Session, result_id: str) -> Optional[ComplianceResult]:
        """Get specific compliance result."""
        # Convert string ID to UUID if needed
        result_id_uuid = uuid.UUID(result_id) if isinstance(result_id, str) else result_id
        return db.query(ComplianceResult).filter(
            ComplianceResult.id == result_id_uuid
        ).first()
    
    @staticmethod
    def compute_bid_compliance_summary(db: Session, bid_id: str) -> Dict[str, Any]:
        """Compute compliance summary for bid.
        
        Returns dict with:
        - pass_count: Number of passing clauses
        - fail_count: Number of failing clauses
        - waived_count: Number of waived clauses
        - review_count: Number of review clauses
        - overall_status: Overall compliance (ALL_PASS, SOME_FAIL, REVIEW_NEEDED)
        - detailed_results: List of all results
        """
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        results = ComplianceService.get_bid_compliance(db, str(bid_id_uuid))
        
        pass_count = sum(1 for r in results if r.status == ComplianceStatus.PASS)
        fail_count = sum(1 for r in results if r.status == ComplianceStatus.FAIL)
        waived_count = sum(1 for r in results if r.status == ComplianceStatus.WAIVED)
        review_count = sum(1 for r in results if r.status == ComplianceStatus.REVIEW)
        
        if fail_count > 0:
            overall = "SOME_FAIL"
        elif review_count > 0:
            overall = "REVIEW_NEEDED"
        else:
            overall = "ALL_PASS"
        
        return {
            "pass_count": pass_count,
            "fail_count": fail_count,
            "waived_count": waived_count,
            "review_count": review_count,
            "overall_status": overall,
            "total_clauses": pass_count + fail_count + waived_count + review_count,
            "detailed_results": [
                {
                    "clause_id": str(r.clause_id),
                    "status": r.status,
                    "evaluated_at": r.evaluated_at.isoformat() if r.evaluated_at else None,
                    "is_immutable": r.is_immutable,
                }
                for r in results
            ],
        }
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        event_type: str,
        entity_id: str,
        actor_id: Optional[str],
        payload: dict,
    ):
        """Log compliance operation as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        event_data = f"{event_type}:compliance:{entity_id}:{actor_id}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Convert string IDs to UUID if needed
        entity_id_uuid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id if actor_id else None
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_type="compliance",
            entity_id=entity_id_uuid,
            actor_id=actor_id_uuid,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
