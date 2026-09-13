"""Officer decision service with override tracking for Phase 8."""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.models import (
    OfficerDecision, OfficerDecisionOverride, ComplianceResult, Bid, AuditEvent
)
import uuid
import hashlib


class DecisionStatus:
    """Officer decision constants."""
    VERIFIED = "VERIFIED"
    NON_COMPLIANT = "NON_COMPLIANT"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class OfficerDecisionService:
    """Manage officer decisions with override tracking and immutability."""
    
    @staticmethod
    def make_decision(
        db: Session,
        bid_id: str,
        officer_id: str,
        ai_recommendation: str,
        final_decision: str,
        override_reason: Optional[str] = None,
    ) -> OfficerDecision:
        """Create officer decision.
        
        Args:
            db: Database session
            bid_id: Bid ID
            officer_id: Officer user ID
            ai_recommendation: AI system recommendation
            final_decision: Final decision (VERIFIED, NON_COMPLIANT, NEEDS_CLARIFICATION)
            override_reason: Reason if overriding AI recommendation
            
        Returns:
            Created OfficerDecision object
        """
        # Convert string IDs to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        officer_id_uuid = uuid.UUID(officer_id) if isinstance(officer_id, str) else officer_id
        
        # Build reason from ai_recommendation and override_reason
        reason_text = f"AI Recommendation: {ai_recommendation}"
        if override_reason:
            reason_text += f" | Override Reason: {override_reason}"
        
        decision = OfficerDecision(
            id=uuid.uuid4(),
            bid_id=bid_id_uuid,
            officer_id=officer_id_uuid,
            decision=final_decision,
            reason=reason_text,
        )
        db.add(decision)
        db.flush()
        
        # Log audit
        OfficerDecisionService._log_audit_event(
            db,
            "OFFICER_DECISION_MADE",
            str(bid_id_uuid),
            officer_id_uuid,
            {
                "ai_recommendation": ai_recommendation,
                "final_decision": final_decision,
                "override_reason": override_reason,
                "is_override": ai_recommendation != final_decision,
            },
        )
        
        db.commit()
        return decision
    
    @staticmethod
    def record_override(
        db: Session,
        decision_id: str,
        compliance_result_id: str,
        original_compliance_status: str,
        override_status: str,
        override_evidence: Optional[Dict[str, Any]] = None,
        override_rule_version: Optional[str] = None,
        actor_id: Optional[str] = None,
    ) -> OfficerDecisionOverride:
        """Record an override of a compliance result.
        
        IMPORTANT: The original compliance result is IMMUTABLE. This override
        is a separate artifact showing that an officer overrode the result.
        
        Args:
            db: Database session
            decision_id: Officer decision ID
            compliance_result_id: Compliance result ID being overridden
            original_compliance_status: Original compliance status (PASS/FAIL/etc.)
            override_status: New override status
            override_evidence: Supporting evidence for override
            override_rule_version: Rule version override
            actor_id: User ID making override
            
        Returns:
            Created OfficerDecisionOverride object
        """
        # Convert string IDs to UUID if needed
        decision_id_uuid = uuid.UUID(decision_id) if isinstance(decision_id, str) else decision_id
        compliance_result_id_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id if actor_id else None
        
        # Get compliance result to verify it exists
        compliance = db.query(ComplianceResult).filter(
            ComplianceResult.id == compliance_result_id_uuid
        ).first()
        if not compliance:
            raise ValueError(f"Compliance result {compliance_result_id} not found")
        
        # Create override record
        override = OfficerDecisionOverride(
            id=uuid.uuid4(),
            officer_decision_id=decision_id_uuid,
            compliance_result_id=compliance_result_id_uuid,
            original_compliance_status=original_compliance_status,
            override_status=override_status,
            override_evidence=override_evidence,
            override_rule_version=override_rule_version,
        )
        db.add(override)
        db.flush()
        
        # Mark compliance result as having been overridden (but keep immutable)
        compliance.original_status_before_override = original_compliance_status
        
        # Log audit
        OfficerDecisionService._log_audit_event(
            db,
            "COMPLIANCE_OVERRIDDEN",
            str(compliance.bid_id),
            actor_id_uuid or compliance.bid_id,  # Default to bid if no actor
            {
                "decision_id": str(decision_id_uuid),
                "compliance_result_id": str(compliance_result_id_uuid),
                "original_status": original_compliance_status,
                "override_status": override_status,
                "compliance_remains_immutable": True,
            },
        )
        
        db.commit()
        return override
    
    @staticmethod
    def get_decision(db: Session, decision_id: str) -> Optional[OfficerDecision]:
        """Get officer decision by ID."""
        # Convert string ID to UUID if needed
        decision_id_uuid = uuid.UUID(decision_id) if isinstance(decision_id, str) else decision_id
        return db.query(OfficerDecision).filter(
            OfficerDecision.id == decision_id_uuid
        ).first()
    
    @staticmethod
    def get_bid_decision(db: Session, bid_id: str) -> Optional[OfficerDecision]:
        """Get latest officer decision for a bid."""
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        return db.query(OfficerDecision).filter(
            OfficerDecision.bid_id == bid_id_uuid
        ).order_by(OfficerDecision.decided_at.desc()).first()
    
    @staticmethod
    def get_decision_overrides(
        db: Session,
        decision_id: str,
    ) -> list:
        """Get all overrides associated with a decision."""
        # Convert string ID to UUID if needed
        decision_id_uuid = uuid.UUID(decision_id) if isinstance(decision_id, str) else decision_id
        return db.query(OfficerDecisionOverride).filter(
            OfficerDecisionOverride.officer_decision_id == decision_id_uuid
        ).all()
    
    @staticmethod
    def get_compliance_overrides(
        db: Session,
        compliance_result_id: str,
    ) -> list:
        """Get all overrides for a specific compliance result."""
        # Convert string ID to UUID if needed
        compliance_result_id_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        return db.query(OfficerDecisionOverride).filter(
            OfficerDecisionOverride.compliance_result_id == compliance_result_id_uuid
        ).order_by(OfficerDecisionOverride.created_at.desc()).all()
    
    @staticmethod
    def has_overrides(db: Session, bid_id: str) -> bool:
        """Check if bid has any compliance overrides."""
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        count = db.query(OfficerDecisionOverride).join(
            OfficerDecision,
            OfficerDecisionOverride.officer_decision_id == OfficerDecision.id,
        ).filter(
            OfficerDecision.bid_id == bid_id_uuid
        ).count()
        return count > 0
    
    @staticmethod
    def verify_immutability(db: Session, compliance_result_id: str) -> Dict[str, Any]:
        """Verify that compliance result remains immutable even with overrides.
        
        Returns dict with:
        - compliance_id: Compliance result ID
        - is_immutable: Always True
        - original_status: Original evaluation status
        - has_overrides: Whether overrides exist
        - overrides: List of override records
        """
        # Convert string ID to UUID if needed
        compliance_result_id_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        
        compliance = db.query(ComplianceResult).filter(
            ComplianceResult.id == compliance_result_id_uuid
        ).first()
        
        if not compliance:
            raise ValueError(f"Compliance result {compliance_result_id} not found")
        
        overrides = OfficerDecisionService.get_compliance_overrides(
            db,
            str(compliance_result_id_uuid),
        )
        
        return {
            "compliance_id": str(compliance_result_id_uuid),
            "is_immutable": compliance.is_immutable,
            "original_status": compliance.status,
            "original_status_before_override": compliance.original_status_before_override,
            "has_overrides": len(overrides) > 0,
            "override_count": len(overrides),
            "overrides": [
                {
                    "override_id": str(o.id),
                    "override_status": o.override_status,
                    "created_at": o.created_at.isoformat() if o.created_at else None,
                }
                for o in overrides
            ],
        }
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        event_type: str,
        entity_id: str,
        actor_id: str,
        payload: dict,
    ):
        """Log decision operation as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        event_data = f"{event_type}:decision:{entity_id}:{actor_id}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Convert string IDs to UUID if needed
        entity_id_uuid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_type="decision",
            entity_id=entity_id_uuid,
            actor_id=actor_id_uuid,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
