"""Evidence traceability service for Phase 2 - Trace compliance findings to source."""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.models import (
    ComplianceResult, ExtractedFact, VerificationResult, Document,
    RiskSignal, Clause, AuditEvent
)
import uuid
import hashlib


class EvidenceChain:
    """Represents a single link in the evidence chain."""
    
    def __init__(
        self,
        level: str,  # compliance, fact, document, verification
        entity_id: str,
        entity_type: str,
        details: Dict[str, Any],
    ):
        self.level = level
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.details = details


class EvidenceTraceability:
    """Trace compliance findings back to source documents and verification results."""
    
    @staticmethod
    def trace_compliance_result(
        db: Session,
        compliance_result_id: str,
    ) -> Dict[str, Any]:
        """Trace a compliance result to all evidence sources.
        
        Returns complete chain:
        - Compliance Result
        - Related Clause
        - Referenced Extracted Facts
        - Source Documents
        - Verification Results
        
        Args:
            db: Database session
            compliance_result_id: Compliance result ID to trace
            
        Returns:
            Dict with complete evidence chain
        """
        # Convert string ID to UUID if needed
        compliance_result_id_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        
        compliance = db.query(ComplianceResult).filter(
            ComplianceResult.id == compliance_result_id_uuid
        ).first()
        
        if not compliance:
            raise ValueError(f"Compliance result {compliance_result_id} not found")
        
        # Get clause
        clause = db.query(Clause).filter(
            Clause.id == compliance.clause_id
        ).first()
        
        # Parse evidence references from compliance result
        evidence_refs = compliance.evidence_refs or []
        
        # Collect extracted facts
        extracted_facts = []
        fact_ids = [ref for ref in evidence_refs if isinstance(ref, str)]
        
        for fact_id in fact_ids:
            try:
                fact_id_value = uuid.UUID(fact_id)
                fact = db.query(ExtractedFact).filter(
                    ExtractedFact.id == fact_id_value
                ).first()
                
                if fact:
                    extracted_facts.append({
                        "fact_id": str(fact.id),
                        "field_name": fact.field_name,
                        "field_value": fact.field_value,
                        "confidence": float(fact.confidence) if fact.confidence else None,
                        "evidence_span": fact.evidence_span,
                        "meets_threshold": fact.meets_threshold,
                    })
            except Exception:
                pass
        
        # Collect source documents and their verification results
        documents_chain = []
        document_ids = set()
        
        for fact in extracted_facts:
            fact_obj = db.query(ExtractedFact).filter(
                ExtractedFact.field_name == fact["field_name"],
                ExtractedFact.field_value == fact["field_value"],
            ).first()
            
            if fact_obj and fact_obj.document_id:
                document_ids.add(fact_obj.document_id)
        
        for doc_id in document_ids:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            
            if doc:
                # Get all verification results for facts in this document
                verifications = db.query(VerificationResult).join(
                    ExtractedFact,
                    VerificationResult.extracted_fact_id == ExtractedFact.id,
                ).filter(
                    ExtractedFact.document_id == doc_id
                ).all()
                
                documents_chain.append({
                    "document_id": str(doc.id),
                    "doc_type": doc.doc_type,
                    "file_hash": doc.file_hash,
                    "current_version": doc.current_version,
                    "ocr_status": doc.ocr_status,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                    "verifications": [
                        {
                            "verification_id": str(v.id),
                            "adapter_source": v.adapter_source,
                            "status": v.status,
                            "evidence": v.evidence,
                            "checked_at": v.checked_at.isoformat() if v.checked_at else None,
                        }
                        for v in verifications
                    ],
                })
        
        # Build complete chain
        return {
            "compliance_result_id": str(compliance.id),
            "bid_id": str(compliance.bid_id),
            "clause": {
                "clause_id": str(clause.id) if clause else None,
                "raw_text": clause.raw_text if clause else None,
                "category": clause.category if clause else None,
            },
            "compliance_status": compliance.status,
            "compliance_reasoning": compliance.reasoning_chain,
            "extracted_facts": extracted_facts,
            "documents": documents_chain,
        }
    
    @staticmethod
    def trace_risk_signal(
        db: Session,
        risk_signal_id: str,
    ) -> Dict[str, Any]:
        """Trace a risk signal to its root causes and evidence.
        
        Args:
            db: Database session
            risk_signal_id: Risk signal ID to trace
            
        Returns:
            Dict with risk signal evidence chain
        """
        # Convert string ID to UUID if needed
        risk_signal_id_uuid = uuid.UUID(risk_signal_id) if isinstance(risk_signal_id, str) else risk_signal_id
        
        signal = db.query(RiskSignal).filter(
            RiskSignal.id == risk_signal_id_uuid
        ).first()
        
        if not signal:
            raise ValueError(f"Risk signal {risk_signal_id} not found")
        
        chain = {
            "signal_id": str(signal.id),
            "signal_type": signal.signal_type,
            "weight": float(signal.weight),
            "severity": float(signal.severity),
            "bid_id": str(signal.bid_id),
        }
        
        # Trace back to source
        if signal.extracted_fact_id:
            fact = db.query(ExtractedFact).filter(
                ExtractedFact.id == signal.extracted_fact_id
            ).first()
            
            if fact:
                chain["source"] = {
                    "type": "extracted_fact",
                    "fact_id": str(fact.id),
                    "field_name": fact.field_name,
                    "field_value": fact.field_value,
                    "confidence": float(fact.confidence) if fact.confidence else None,
                }
                
                # Get document
                doc = db.query(Document).filter(
                    Document.id == fact.document_id
                ).first()
                
                if doc:
                    chain["document"] = {
                        "document_id": str(doc.id),
                        "doc_type": doc.doc_type,
                        "file_hash": doc.file_hash,
                    }
        
        elif signal.verification_result_id:
            verification = db.query(VerificationResult).filter(
                VerificationResult.id == signal.verification_result_id
            ).first()
            
            if verification:
                chain["source"] = {
                    "type": "verification",
                    "verification_id": str(verification.id),
                    "adapter_source": verification.adapter_source,
                    "status": verification.status,
                    "evidence": verification.evidence,
                }
        
        elif signal.compliance_result_id:
            compliance = db.query(ComplianceResult).filter(
                ComplianceResult.id == signal.compliance_result_id
            ).first()
            
            if compliance:
                chain["source"] = {
                    "type": "compliance",
                    "compliance_result_id": str(compliance.id),
                    "status": compliance.status,
                    "rule_version": compliance.rule_version,
                }
        
        return chain
    
    @staticmethod
    def get_bid_evidence_summary(
        db: Session,
        bid_id: str,
    ) -> Dict[str, Any]:
        """Get complete evidence summary for a bid showing all findings and traces.
        
        Args:
            db: Database session
            bid_id: Bid ID
            
        Returns:
            Dict with complete bid evidence analysis
        """
        # Convert string ID to UUID if needed
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        
        # Get all compliance results
        compliance_results = db.query(ComplianceResult).filter(
            ComplianceResult.bid_id == bid_id_uuid
        ).all()
        
        # Get all risk signals
        risk_signals = db.query(RiskSignal).filter(
            RiskSignal.bid_id == bid_id_uuid
        ).all()
        
        # Get all documents
        from app.models.models import Bid
        bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
        
        documents = []
        if bid:
            documents = db.query(Document).filter(
                Document.bid_id == bid_id_uuid
            ).all()
        
        # Build summary
        summary = {
            "bid_id": str(bid_id_uuid),
            "compliance_count": len(compliance_results),
            "risk_signal_count": len(risk_signals),
            "document_count": len(documents),
            "compliance_results": [],
            "risk_signals": [],
            "documents": [],
        }
        
        # Add compliance results with traces
        for comp in compliance_results:
            try:
                trace = EvidenceTraceability.trace_compliance_result(
                    db,
                    str(comp.id),
                )
                summary["compliance_results"].append(trace)
            except Exception:
                pass
        
        # Add risk signals with traces
        for signal in risk_signals:
            try:
                trace = EvidenceTraceability.trace_risk_signal(
                    db,
                    str(signal.id),
                )
                summary["risk_signals"].append(trace)
            except Exception:
                pass
        
        # Add document inventory
        for doc in documents:
            facts = db.query(ExtractedFact).filter(
                ExtractedFact.document_id == doc.id
            ).all()
            
            summary["documents"].append({
                "document_id": str(doc.id),
                "doc_type": doc.doc_type,
                "file_hash": doc.file_hash,
                "current_version": doc.current_version,
                "extracted_facts_count": len(facts),
                "ocr_status": doc.ocr_status,
            })
        
        return summary
    
    @staticmethod
    def get_drill_down_path(
        db: Session,
        compliance_result_id: str,
        fact_id: Optional[str] = None,
    ) -> List[EvidenceChain]:
        """Get drill-down path for officer investigation.
        
        Returns list of evidence chain links from compliance result
        down to source document and verification.
        
        Args:
            db: Database session
            compliance_result_id: Starting compliance result
            fact_id: Optional specific fact to drill into
            
        Returns:
            List of EvidenceChain objects
        """
        chain = []
        
        # Convert string IDs to UUID if needed
        compliance_result_id_uuid = uuid.UUID(compliance_result_id) if isinstance(compliance_result_id, str) else compliance_result_id
        fact_id_uuid = uuid.UUID(fact_id) if isinstance(fact_id, str) else fact_id if fact_id else None
        
        # Start with compliance result
        compliance = db.query(ComplianceResult).filter(
            ComplianceResult.id == compliance_result_id_uuid
        ).first()
        
        if not compliance:
            return chain
        
        chain.append(EvidenceChain(
            level="compliance",
            entity_id=str(compliance.id),
            entity_type="ComplianceResult",
            details={
                "status": compliance.status,
                "reasoning": compliance.reasoning_chain,
                "rule_version": compliance.rule_version,
            },
        ))
        
        # Get clause
        if compliance.clause_id:
            clause = db.query(Clause).filter(
                Clause.id == compliance.clause_id
            ).first()
            
            if clause:
                chain.append(EvidenceChain(
                    level="clause",
                    entity_id=str(clause.id),
                    entity_type="Clause",
                    details={
                        "raw_text": clause.raw_text,
                        "category": clause.category,
                    },
                ))
        
        # Get extracted facts
        evidence_refs = compliance.evidence_refs or []
        
        for ref in evidence_refs:
            try:
                fact_ref = uuid.UUID(ref)
                fact = db.query(ExtractedFact).filter(
                    ExtractedFact.id == fact_ref
                ).first()
                
                if fact and (fact_id_uuid is None or str(fact.id) == str(fact_id_uuid)):
                    chain.append(EvidenceChain(
                        level="fact",
                        entity_id=str(fact.id),
                        entity_type="ExtractedFact",
                        details={
                            "field_name": fact.field_name,
                            "field_value": fact.field_value,
                            "confidence": float(fact.confidence) if fact.confidence else None,
                        },
                    ))
                    
                    # Get document
                    if fact.document_id:
                        doc = db.query(Document).filter(
                            Document.id == fact.document_id
                        ).first()
                        
                        if doc:
                            chain.append(EvidenceChain(
                                level="document",
                                entity_id=str(doc.id),
                                entity_type="Document",
                                details={
                                    "doc_type": doc.doc_type,
                                    "file_hash": doc.file_hash,
                                    "current_version": doc.current_version,
                                },
                            ))
                        
                        # Get verifications
                        verifications = db.query(VerificationResult).join(
                            ExtractedFact,
                            VerificationResult.extracted_fact_id == ExtractedFact.id,
                        ).filter(
                            ExtractedFact.id == fact.id
                        ).all()
                        
                        for v in verifications:
                            chain.append(EvidenceChain(
                                level="verification",
                                entity_id=str(v.id),
                                entity_type="VerificationResult",
                                details={
                                    "adapter_source": v.adapter_source,
                                    "status": v.status,
                                    "evidence": v.evidence,
                                },
                            ))
            except Exception:
                pass
        
        return chain
    
    @staticmethod
    def _log_audit_event(
        db: Session,
        event_type: str,
        entity_id: str,
        actor_id: Optional[str],
        payload: dict,
    ):
        """Log evidence access as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        event_data = f"{event_type}:evidence:{entity_id}:{actor_id}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        # Convert string IDs to UUID if needed
        entity_id_uuid = uuid.UUID(entity_id) if isinstance(entity_id, str) else entity_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id if actor_id else None
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type=event_type,
            entity_type="evidence",
            entity_id=entity_id_uuid,
            actor_id=actor_id_uuid,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)
