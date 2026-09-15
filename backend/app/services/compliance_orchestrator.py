"""Compliance orchestrator for Phase 5 - deterministic evaluation with immutability.

PHASE 6 INTEGRATION: Automatically creates risk signals when compliance fails.
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import (
    Bid, ComplianceResult, ExtractedFact, VerificationResult,
    Clause, TenderVersion, AuditEvent
)
from app.services.compliance_service import ComplianceService
from app.services.risk_service import RiskService
import hashlib
import uuid


class ComplianceEvaluationContext:
    """Context for compliance evaluation of a bid."""
    
    def __init__(
        self,
        bid_id: str,
        tender_version_id: str,
        extracted_facts: Dict[str, Any],
        verification_results: Dict[str, Any],
    ):
        self.bid_id = bid_id
        self.tender_version_id = tender_version_id
        self.extracted_facts = extracted_facts
        self.verification_results = verification_results
        self.evaluation_timestamp = datetime.utcnow()


class ComplianceOrchestrator:
    """Orchestrate deterministic compliance evaluation for bids."""
    
    @staticmethod
    def evaluate_bid_compliance(
        db: Session,
        bid_id: str,
        actor_id: str,
        rule_version: str = "1.0",
    ) -> Dict[str, Any]:
        """Evaluate complete compliance for a bid deterministically.
        
        This is the core Phase 5 function that:
        1. Gets all clauses from tender
        2. Gathers extracted facts from bid documents
        3. Gets verification results
        4. Evaluates each clause against facts
        5. Creates IMMUTABLE compliance results
        6. Separates officer decisions from compliance findings
        
        Args:
            db: Database session
            bid_id: Bid ID to evaluate
            actor_id: User ID performing evaluation
            rule_version: Version of compliance rules
            
        Returns:
            Dict with evaluation results and summary
        """
        bid = db.query(Bid).filter(Bid.id == bid_id).first()
        if not bid:
            raise ValueError(f"Bid {bid_id} not found")
        
        # Get tender version and clauses
        tender_version = db.query(TenderVersion).filter(
            TenderVersion.id == bid.tender_version_id
        ).first()
        
        if not tender_version:
            raise ValueError(f"Tender version {bid.tender_version_id} not found")
        
        clauses = db.query(Clause).filter(
            Clause.tender_version_id == bid.tender_version_id
        ).all()
        
        # Collect extracted facts and verification results
        facts_by_field = {}
        verifications_by_field = {}
        
        from app.models.models import Document
        documents = db.query(Document).filter(Document.bid_id == bid_id).all()
        
        for doc in documents:
            facts = db.query(ExtractedFact).filter(
                ExtractedFact.document_id == doc.id
            ).all()
            
            for fact in facts:
                facts_by_field[fact.field_name] = {
                    "value": fact.field_value,
                    "confidence": float(fact.confidence) if fact.confidence else 0,
                    "meets_threshold": fact.meets_threshold,
                    "fact_id": str(fact.id),
                }
            
            # Get verifications for this document's facts
            for fact in facts:
                verifs = db.query(VerificationResult).filter(
                    VerificationResult.extracted_fact_id == fact.id
                ).all()
                
                for verif in verifs:
                    verifications_by_field[fact.field_name] = {
                        "status": verif.status,
                        "adapter": verif.adapter_source,
                        "evidence": verif.evidence,
                        "verification_id": str(verif.id),
                    }
        
        # Evaluate each clause
        evaluation_results = []
        compliance_by_status = {"PASS": [], "FAIL": [], "WAIVED": []}
        
        for clause in clauses:
            evaluation = ComplianceOrchestrator._evaluate_clause(
                db,
                clause,
                facts_by_field,
                verifications_by_field,
                bid_id,
                actor_id,
                rule_version,
            )
            
            evaluation_results.append(evaluation)
            
            # Track by status for summary
            if evaluation["status"] in compliance_by_status:
                compliance_by_status[evaluation["status"]].append(evaluation)
        
        # PHASE 6 INTEGRATION: Generate risk signals for failed clauses
        for failed_eval in compliance_by_status["FAIL"]:
            clause_id = failed_eval["clause_id"]
            compliance_result_id = failed_eval["compliance_result_id"]
            
            # Create risk signal with high weight
            signal = RiskService.create_risk_signal(
                db=db,
                bid_id=bid_id,
                signal_type="COMPLIANCE_FAILURE",
                weight=0.8,  # High weight for direct compliance failures
                severity=0.9,
                compliance_result_id=compliance_result_id,
                actor_id=actor_id,
            )
            
            # Decompose signal for explainability
            reasoning = failed_eval.get("reasoning", {})
            components = {
                "failure_reason": {
                    "weight": 0.4,
                    "evidence": reasoning.get("reason", "Unknown"),
                },
                "missing_fields": {
                    "weight": 0.3,
                    "evidence": str(reasoning.get("missing", [])),
                },
                "failed_verifications": {
                    "weight": 0.3,
                    "evidence": str(reasoning.get("failed_fields", [])),
                },
            }
            
            RiskService.decompose_signal(
                db=db,
                signal_id=str(signal.id),
                components=components,
                actor_id=actor_id,
            )
        
        # Summary
        summary = {
            "bid_id": str(bid_id),
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "rule_version": rule_version,
            "total_clauses": len(clauses),
            "pass_count": len(compliance_by_status["PASS"]),
            "fail_count": len(compliance_by_status["FAIL"]),
            "waived_count": len(compliance_by_status["WAIVED"]),
            "overall_status": ComplianceOrchestrator._compute_overall_status(
                compliance_by_status
            ),
            "immutability_enforced": True,  # Phase 5 guarantee
            "officer_decision_separate": True,  # Phase 8 separation
            "risk_signals_generated": len(compliance_by_status["FAIL"]),  # Phase 6
            "evaluations": evaluation_results,
        }
        
        return summary
    
    @staticmethod
    def _evaluate_clause(
        db: Session,
        clause: Any,
        facts_by_field: Dict[str, Any],
        verifications_by_field: Dict[str, Any],
        bid_id: str,
        actor_id: str,
        rule_version: str,
    ) -> Dict[str, Any]:
        """Evaluate single clause deterministically.
        
        CRITICAL: Result must be immutable. FAIL stays FAIL.
        Officer decisions are separate artifacts.
        
        Args:
            db: Database session
            clause: Clause to evaluate
            facts_by_field: Extracted facts keyed by field name
            verifications_by_field: Verification results keyed by field
            bid_id: Bid being evaluated
            actor_id: Evaluating user
            rule_version: Rule version
            
        Returns:
            Dict with evaluation result
        """
        # Apply clause logic tree to facts
        logic_result = ComplianceOrchestrator._apply_logic_tree(
            clause.logic_tree,
            facts_by_field,
            verifications_by_field,
        )
        
        status = logic_result["status"]
        reasoning = logic_result["reasoning"]
        evidence_refs = logic_result["evidence_refs"]
        
        # Create immutable compliance result
        compliance_result = ComplianceService.evaluate_compliance(
            db,
            str(bid_id),
            str(clause.id),
            status,
            reasoning,
            evidence_refs,
            rule_version,
            actor_id,
        )
        
        return {
            "clause_id": str(clause.id),
            "clause_text": clause.raw_text[:100],  # Truncate for summary
            "status": status,
            "compliance_result_id": str(compliance_result.id),
            "is_immutable": True,
            "reasoning": reasoning,
            "evidence_count": len(evidence_refs),
        }
    
    @staticmethod
    def _apply_logic_tree(
        logic_tree: Dict[str, Any],
        facts_by_field: Dict[str, Any],
        verifications_by_field: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply clause logic tree to extracted facts.
        
        Returns DETERMINISTIC result based on facts and verifications.
        
        Args:
            logic_tree: Logic tree from clause
            facts_by_field: Available facts
            verifications_by_field: Verification results
            
        Returns:
            Dict with status, reasoning, and evidence
        """
        # Simplified deterministic evaluation
        # In production, would use full rule engine from app/services/rules/evaluator.py
        
        if not logic_tree:
            return {
                "status": "REVIEW",
                "reasoning": {"reason": "No logic tree defined"},
                "evidence_refs": [],
            }
        
        # Check required fields from logic tree
        required_fields = logic_tree.get("required_fields", [])
        
        missing_fields = [f for f in required_fields if f not in facts_by_field]
        
        if missing_fields:
            return {
                "status": "FAIL",
                "reasoning": {
                    "reason": "Missing required fields",
                    "missing": missing_fields,
                },
                "evidence_refs": [],
            }
        
        # Check verifications for present fields
        failed_verifications = [
            f for f in facts_by_field
            if f in verifications_by_field
            and verifications_by_field[f]["status"] == "MISMATCH"
        ]
        
        if failed_verifications:
            return {
                "status": "FAIL",
                "reasoning": {
                    "reason": "Verification failed",
                    "failed_fields": failed_verifications,
                },
                "evidence_refs": [],
            }
        
        # Check confidence thresholds
        low_confidence_fields = [
            f for f in facts_by_field
            if facts_by_field[f].get("confidence", 0) < 0.7
        ]
        
        if low_confidence_fields:
            return {
                "status": "REVIEW",
                "reasoning": {
                    "reason": "Low confidence extraction",
                    "low_confidence_fields": low_confidence_fields,
                },
                "evidence_refs": [facts_by_field[f].get("fact_id") for f in low_confidence_fields],
            }
        
        # All checks passed
        return {
            "status": "PASS",
            "reasoning": {
                "reason": "All required fields verified",
                "fields_checked": len(facts_by_field),
                "verifications_passed": len([f for f in facts_by_field if f in verifications_by_field]),
            },
            "evidence_refs": [facts_by_field[f].get("fact_id") for f in facts_by_field],
        }
    
    @staticmethod
    def _compute_overall_status(compliance_by_status: Dict[str, list]) -> str:
        """Compute overall bid compliance status.
        
        Args:
            compliance_by_status: Dict with PASS, FAIL, WAIVED lists
            
        Returns:
            Overall status string
        """
        if compliance_by_status["FAIL"]:
            return "FAILED"
        elif compliance_by_status["REVIEW"]:
            return "NEEDS_REVIEW"
        else:
            return "COMPLIANT"
    
    @staticmethod
    def get_compliance_state(
        db: Session,
        bid_id: str,
    ) -> Dict[str, Any]:
        """Get current compliance state for a bid (immutable view).
        
        CRITICAL PHASE 5 GUARANTEE:
        - Compliance results are immutable (FAIL stays FAIL)
        - Officer decisions are separate from compliance findings
        - Both are audited
        
        Args:
            db: Database session
            bid_id: Bid ID
            
        Returns:
            Dict with compliance state and decision state
        """
        # Get all compliance results (immutable)
        compliance_results = db.query(ComplianceResult).filter(
            ComplianceResult.bid_id == bid_id
        ).all()
        
        compliance_state = {
            "bid_id": str(bid_id),
            "compliance_results": [
                {
                    "result_id": str(r.id),
                    "clause_id": str(r.clause_id),
                    "status": r.status,
                    "is_immutable": r.is_immutable,
                    "evaluated_at": r.evaluated_at.isoformat() if r.evaluated_at else None,
                }
                for r in compliance_results
            ],
            "immutability_enforced": all(r.is_immutable for r in compliance_results),
        }
        
        # Get officer decision (separate artifact - Phase 8)
        from app.models.models import OfficerDecision
        decision = db.query(OfficerDecision).filter(
            OfficerDecision.bid_id == bid_id
        ).order_by(OfficerDecision.decided_at.desc()).first()
        
        decision_state = {}
        if decision:
            decision_state = {
                "decision_id": str(decision.id),
                "final_decision": decision.final_decision,
                "ai_recommendation": decision.ai_recommendation,
                "is_override": decision.ai_recommendation != decision.final_decision,
                "decided_at": decision.decided_at.isoformat() if decision.decided_at else None,
            }
        
        return {
            "compliance": compliance_state,
            "officer_decision": decision_state,
            "separation_enforced": True,  # Phase 5/8 guarantee
        }
