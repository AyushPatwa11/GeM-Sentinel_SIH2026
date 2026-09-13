"""Risk scoring and signal decomposition service for Phase 6."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.models import (
    RiskSignal, RiskAssessment, RiskSignalDecomposition, Bid, AuditEvent
)
import uuid
import hashlib


class RiskService:
    """Manage risk assessment and signal decomposition."""
    
    @staticmethod
    def create_risk_signal(
        db: Session,
        bid_id: str,
        signal_type: str,
        weight: float,
        severity: float,
        extracted_fact_id: Optional[str] = None,
        verification_result_id: Optional[str] = None,
        entity_resolution_result_id: Optional[str] = None,
        compliance_result_id: Optional[str] = None,
        policy_version: str = "1.0",
        actor_id: Optional[str] = None,
    ) -> RiskSignal:
        """Create a risk signal.
        
        Args:
            db: Database session
            bid_id: Bid ID
            signal_type: Type of risk (MISSING_DOC, FAILED_VERIFICATION, etc.)
            weight: Signal weight (0-1)
            severity: Severity level (0-1)
            extracted_fact_id: Optional reference to extracted fact
            verification_result_id: Optional reference to verification
            entity_resolution_result_id: Optional reference to entity resolution
            compliance_result_id: Optional reference to compliance
            policy_version: Risk policy version
            actor_id: User ID creating signal
            
        Returns:
            Created RiskSignal object
        """
        # Convert string IDs to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        compliance_result_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        extracted_fact_uuid = uuid.UUID(extracted_fact_id) if isinstance(extracted_fact_id, str) else extracted_fact_id
        verification_result_uuid = uuid.UUID(verification_result_id) if isinstance(verification_result_id, str) else verification_result_id
        entity_resolution_uuid = uuid.UUID(entity_resolution_result_id) if isinstance(entity_resolution_result_id, str) else entity_resolution_result_id
        
        signal = RiskSignal(
            id=uuid.uuid4(),
            bid_id=bid_id_uuid,
            signal_type=signal_type,
            weight=weight,
            severity=severity,
            extracted_fact_id=extracted_fact_uuid,
            verification_result_id=verification_result_uuid,
            entity_resolution_result_id=entity_resolution_uuid,
            compliance_result_id=compliance_result_uuid,
            policy_version=policy_version,
        )
        db.add(signal)
        db.flush()
        
        # Log audit
        RiskService._log_audit_event(
            db,
            "RISK_SIGNAL_CREATED",
            str(bid_id),
            actor_id,
            {
                "signal_type": signal_type,
                "weight": float(weight),
                "severity": float(severity),
            },
        )
        
        db.commit()
        return signal
    
    @staticmethod
    def decompose_signal(
        db: Session,
        signal_id: str,
        components: Dict[str, Dict[str, Any]],
        actor_id: Optional[str] = None,
    ) -> List[RiskSignalDecomposition]:
        """Decompose a risk signal into components for explainability.
        
        Args:
            db: Database session
            signal_id: Risk signal ID
            components: Dict of component_name -> {weight, evidence}
            actor_id: User ID creating decomposition
            
        Returns:
            List of created RiskSignalDecomposition objects
        """
        decompositions = []
        
        for component_name, component_data in components.items():
            decomp = RiskSignalDecomposition(
                id=uuid.uuid4(),
                risk_signal_id=signal_id,
                component_name=component_name,
                component_weight=component_data.get("weight", 0),
                component_evidence=component_data.get("evidence"),
            )
            db.add(decomp)
            decompositions.append(decomp)
        
        db.flush()
        
        # Log audit
        RiskService._log_audit_event(
            db,
            "SIGNAL_DECOMPOSED",
            str(signal_id),
            actor_id,
            {
                "component_count": len(components),
                "components": list(components.keys()),
            },
        )
        
        db.commit()
        return decompositions
    
    @staticmethod
    def assess_risk(
        db: Session,
        bid_id: str,
        total_score: float,
        risk_level: str,
        policy_version: str = "1.0",
        actor_id: Optional[str] = None,
    ) -> RiskAssessment:
        """Create or update risk assessment for a bid.
        
        Args:
            db: Database session
            bid_id: Bid ID
            total_score: Total risk score (0-100)
            risk_level: Risk level (LOW, MEDIUM, HIGH)
            policy_version: Risk policy version
            actor_id: User ID creating assessment
            
        Returns:
            Created or updated RiskAssessment object
        """
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        
        # Check for existing assessment
        existing = db.query(RiskAssessment).filter(
            RiskAssessment.bid_id == bid_id_uuid
        ).first()
        
        if existing:
            # Update instead of create
            existing.total_score = total_score
            existing.risk_level = risk_level
            existing.computed_at = datetime.utcnow()
            assessment = existing
        else:
            assessment = RiskAssessment(
                id=uuid.uuid4(),
                bid_id=bid_id_uuid,
                total_score=total_score,
                risk_level=risk_level,
                policy_version=policy_version,
            )
            db.add(assessment)
        
        db.flush()
        
        # Log audit
        RiskService._log_audit_event(
            db,
            "RISK_ASSESSED",
            str(bid_id),
            actor_id,
            {
                "total_score": float(total_score),
                "risk_level": risk_level,
                "policy_version": policy_version,
            },
        )
        
        db.commit()
        return assessment
    
    @staticmethod
    def get_bid_risk_assessment(db: Session, bid_id: str) -> Optional[RiskAssessment]:
        """Get risk assessment for a bid."""
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        return db.query(RiskAssessment).filter(
            RiskAssessment.bid_id == bid_id_uuid
        ).first()
    
    @staticmethod
    def get_bid_signals(db: Session, bid_id: str) -> List[RiskSignal]:
        """Get all risk signals for a bid."""
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        return db.query(RiskSignal).filter(
            RiskSignal.bid_id == bid_id_uuid
        ).all()
    
    @staticmethod
    def get_signal_decomposition(
        db: Session,
        signal_id: str,
    ) -> List[RiskSignalDecomposition]:
        """Get decomposition of a risk signal."""
        return db.query(RiskSignalDecomposition).filter(
            RiskSignalDecomposition.risk_signal_id == signal_id
        ).all()
    
    @staticmethod
    def compute_risk_level(total_score: float) -> str:
        """Map numeric risk score to level."""
        if total_score < 33:
            return "LOW"
        elif total_score < 67:
            return "MEDIUM"
        else:
            return "HIGH"
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        event_type: str,
        entity_id: str,
        actor_id: Optional[str],
        payload: dict,
    ):
        """Log risk operation as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        event_data = f"{event_type}:risk:{entity_id}:{actor_id}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Convert entity_id to UUID if string
        entity_id_uuid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_type="risk",
            entity_id=entity_id_uuid,
            actor_id=actor_id_uuid,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
