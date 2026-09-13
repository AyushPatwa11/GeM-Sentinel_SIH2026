"""Evidence Traceability for Phase 4 - Link evidence to compliance rules."""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import (
    ComplianceResult, RiskSignal, ExtractedFact, Document, 
    AuditEvent, VerificationAttempt, VerificationResultNew
)
import uuid
import hashlib


class EvidenceTraceabilityPhase4:
    """Track evidence chains for compliance decisions."""
    
    @staticmethod
    def create_compliance_evidence_chain(
        db: Session,
        compliance_result_id: str,
        bid_id: str,
        rule_id: str,
        evidence_items: List[Dict[str, Any]],
        actor_id: str,
    ) -> Dict[str, Any]:
        """Create immutable evidence chain for compliance decision.
        
        Args:
            db: Database session
            compliance_result_id: ComplianceResult ID
            bid_id: Bid ID
            rule_id: Rule ID evaluated
            evidence_items: List of evidence references
                [
                    {"type": "document", "id": doc_id, "version": 1},
                    {"type": "extracted_fact", "id": fact_id},
                    {"type": "verification", "id": verification_id},
                ]
            actor_id: User creating evidence chain
            
        Returns:
            Evidence chain metadata with traceability info
        """
        compliance_result_id_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        # Verify compliance result exists
        compliance_result = db.query(ComplianceResult).filter(
            ComplianceResult.id == compliance_result_id_uuid
        ).first()
        if not compliance_result:
            raise ValueError(f"ComplianceResult {compliance_result_id} not found")
        
        # Build chain with all evidence hashes
        evidence_chain = []
        for idx, evidence in enumerate(evidence_items):
            evidence_hash = EvidenceTraceabilityPhase4._hash_evidence(evidence)
            evidence_chain.append({
                "index": idx,
                "type": evidence.get("type"),
                "id": evidence.get("id"),
                "hash": evidence_hash,
                "verified_at": __import__('datetime').datetime.utcnow().isoformat(),
            })
        
        # Compute chain hash (hash of all hashes)
        chain_data = "|".join(e["hash"] for e in evidence_chain)
        chain_hash = hashlib.sha256(chain_data.encode()).hexdigest()
        
        # Create audit trail
        EvidenceTraceabilityPhase4._log_evidence_chain(
            db,
            compliance_result_id_uuid,
            bid_id_uuid,
            rule_id,
            evidence_chain,
            chain_hash,
            actor_id_uuid,
        )
        
        return {
            "compliance_result_id": str(compliance_result_id_uuid),
            "chain_hash": chain_hash,
            "evidence_count": len(evidence_chain),
            "evidence_chain": evidence_chain,
            "created_at": __import__('datetime').datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def verify_evidence_chain(
        db: Session,
        compliance_result_id: str,
        chain_hash: str,
    ) -> Dict[str, Any]:
        """Verify integrity of evidence chain (immutability check).
        
        Args:
            db: Database session
            compliance_result_id: ComplianceResult ID
            chain_hash: Previously computed chain hash
            
        Returns:
            Verification result with integrity status
        """
        compliance_result_id_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        
        # Retrieve audit events for this compliance result
        audit_events = db.query(AuditEvent).filter(
            AuditEvent.entity_type == "compliance",
            AuditEvent.entity_id == compliance_result_id_uuid,
            AuditEvent.event_type == "EVIDENCE_CHAIN_CREATED",
        ).order_by(AuditEvent.created_at.asc()).all()
        
        if not audit_events:
            return {
                "compliance_result_id": str(compliance_result_id_uuid),
                "is_valid": False,
                "reason": "No evidence chain found",
            }
        
        # Reconstruct chain from audit and verify
        chain_data = audit_events[0].payload.get("chain_data", "")
        computed_hash = hashlib.sha256(chain_data.encode()).hexdigest()
        
        is_valid = computed_hash == chain_hash
        
        return {
            "compliance_result_id": str(compliance_result_id_uuid),
            "is_valid": is_valid,
            "expected_hash": chain_hash,
            "computed_hash": computed_hash,
            "evidence_count": len(audit_events),
            "verified_at": __import__('datetime').datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def trace_compliance_to_evidence(
        db: Session,
        compliance_result_id: str,
    ) -> Dict[str, Any]:
        """Trace compliance decision back to source evidence.
        
        Args:
            db: Database session
            compliance_result_id: ComplianceResult ID
            
        Returns:
            Full traceability chain from decision to evidence
        """
        compliance_result_id_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        
        compliance_result = db.query(ComplianceResult).filter(
            ComplianceResult.id == compliance_result_id_uuid
        ).first()
        if not compliance_result:
            raise ValueError(f"ComplianceResult {compliance_result_id} not found")
        
        # Retrieve evidence references from result
        evidence_refs = compliance_result.evidence_refs or []
        
        evidence_details = []
        for ref in evidence_refs:
            if isinstance(ref, str):
                ref = {"type": "unknown", "id": ref}
            
            evidence_type = ref.get("type", "unknown")
            evidence_id = ref.get("id")
            
            details = {
                "type": evidence_type,
                "id": evidence_id,
                "content": None,
            }
            
            # Fetch detailed evidence based on type
            try:
                if evidence_type == "extracted_fact":
                    fact_id = uuid.UUID(evidence_id) if isinstance(evidence_id, str) else evidence_id
                    fact = db.query(ExtractedFact).filter(ExtractedFact.id == fact_id).first()
                    if fact:
                        details["content"] = {
                            "fact_type": fact.fact_type,
                            "extracted_value": fact.extracted_value,
                            "confidence": float(fact.confidence_score) if fact.confidence_score else None,
                        }
                
                elif evidence_type == "document":
                    doc_id = uuid.UUID(evidence_id) if isinstance(evidence_id, str) else evidence_id
                    doc = db.query(Document).filter(Document.id == doc_id).first()
                    if doc:
                        details["content"] = {
                            "doc_type": doc.doc_type,
                            "file_hash": doc.file_hash,
                            "ocr_status": doc.ocr_status,
                            "version": doc.current_version,
                        }
                
                elif evidence_type == "verification":
                    verify_id = uuid.UUID(evidence_id) if isinstance(evidence_id, str) else evidence_id
                    result = db.query(VerificationResultNew).filter(VerificationResultNew.id == verify_id).first()
                    if result:
                        details["content"] = {
                            "status": result.verification_status,
                            "authority_value": result.authority_value,
                            "api_response_code": result.api_response_code,
                        }
            except Exception as e:
                details["error"] = str(e)
            
            evidence_details.append(details)
        
        return {
            "compliance_result_id": str(compliance_result_id_uuid),
            "compliance_status": compliance_result.explanation,
            "rule_version": compliance_result.rule_version,
            "evaluated_at": compliance_result.evaluated_at.isoformat() if compliance_result.evaluated_at else None,
            "evidence_chain_length": len(evidence_details),
            "evidence_details": evidence_details,
            "is_immutable": compliance_result.is_immutable,
        }
    
    @staticmethod
    def create_risk_signal_from_compliance(
        db: Session,
        bid_id: str,
        compliance_result_id: str,
        rule_id: str,
        signal_weight: float,
        actor_id: str,
    ) -> Dict[str, Any]:
        """Create risk signal when compliance rule fails.
        
        Args:
            db: Database session
            bid_id: Bid ID
            compliance_result_id: ComplianceResult ID
            rule_id: Rule ID that triggered signal
            signal_weight: Weight/severity of signal
            actor_id: User creating signal
            
        Returns:
            Created risk signal details
        """
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        compliance_result_id_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        # Check compliance result
        compliance_result = db.query(ComplianceResult).filter(
            ComplianceResult.id == compliance_result_id_uuid
        ).first()
        if not compliance_result:
            raise ValueError(f"ComplianceResult {compliance_result_id} not found")
        
        # Create risk signal
        risk_signal = RiskSignal(
            id=uuid.uuid4(),
            bid_id=bid_id_uuid,
            signal_type="COMPLIANCE_VIOLATION",
            weight=signal_weight,
            severity=signal_weight / 5.0,  # Normalize to 0-1
            compliance_result_id=compliance_result_id_uuid,
            policy_version="1.0.0",
        )
        db.add(risk_signal)
        db.flush()
        
        # Log audit
        EvidenceTraceabilityPhase4._log_signal_creation(
            db,
            str(risk_signal.id),
            bid_id_uuid,
            rule_id,
            signal_weight,
            actor_id_uuid,
        )
        db.commit()
        
        return {
            "signal_id": str(risk_signal.id),
            "bid_id": str(bid_id_uuid),
            "signal_type": risk_signal.signal_type,
            "weight": signal_weight,
            "severity": float(risk_signal.severity),
            "created_at": risk_signal.created_at.isoformat() if risk_signal.created_at else None,
        }
    
    @staticmethod
    def _hash_evidence(evidence: Dict[str, Any]) -> str:
        """Compute SHA256 hash of evidence."""
        data = f"{evidence.get('type')}:{evidence.get('id')}:{evidence.get('version', '1')}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def _log_evidence_chain(
        db: Session,
        compliance_result_id: uuid.UUID,
        bid_id: uuid.UUID,
        rule_id: str,
        evidence_chain: List[Dict],
        chain_hash: str,
        actor_id: uuid.UUID,
    ):
        """Log evidence chain creation as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        payload = {
            "rule_id": rule_id,
            "evidence_count": len(evidence_chain),
            "chain_hash": chain_hash,
            "chain_data": "|".join(e["hash"] for e in evidence_chain),
        }
        event_data = f"EVIDENCE_CHAIN_CREATED:compliance:{str(compliance_result_id)}:{str(actor_id)}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type="EVIDENCE_CHAIN_CREATED",
            entity_type="compliance",
            entity_id=compliance_result_id,
            actor_id=actor_id,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
    
    @staticmethod
    def _log_signal_creation(
        db: Session,
        signal_id: str,
        bid_id: uuid.UUID,
        rule_id: str,
        weight: float,
        actor_id: uuid.UUID,
    ):
        """Log risk signal creation as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        payload = {
            "signal_id": signal_id,
            "rule_id": rule_id,
            "weight": weight,
        }
        event_data = f"RISK_SIGNAL_CREATED:risk:{str(bid_id)}:{str(actor_id)}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type="RISK_SIGNAL_CREATED",
            entity_type="risk",
            entity_id=bid_id,
            actor_id=actor_id,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
