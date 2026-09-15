"""Officer Decision Support Engine for Phase 7 - AI recommendations and decision workflow."""
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import (
    Bid, BidState, ComplianceResult, RiskAssessment, 
    ClarificationRequest, AuditEvent
)
import uuid
import hashlib
import logging

logger = logging.getLogger(__name__)


class DecisionRecommendationEngine:
    """Generate AI-backed recommendations for officer decisions."""
    
    @staticmethod
    def generate_recommendation(
        bid_id: str,
        risk_assessment: Dict[str, Any],
        compliance_results: List[Dict[str, Any]],
        verification_failures: int = 0,
        clarifications_pending: int = 0,
    ) -> Dict[str, Any]:
        """Generate decision recommendation based on all signals.
        
        Args:
            bid_id: Bid ID
            risk_assessment: Risk assessment with total_score and risk_level
            compliance_results: List of compliance result summaries
            verification_failures: Count of failed verifications
            clarifications_pending: Count of pending clarifications
            
        Returns:
            Recommendation with:
            - recommendation: VERIFY, NEEDS_CLARIFICATION, REJECT
            - confidence: 0.0-1.0 confidence score
            - reasoning: List of reasoning steps
            - conditions: Any conditions for approval
            - warnings: Any warnings or concerns
        """
        
        risk_level = risk_assessment.get("risk_level", "MEDIUM")
        risk_score = risk_assessment.get("total_score", 50.0)
        
        # Count compliance results
        comply_count = sum(1 for c in compliance_results if c.get("passed"))
        fail_count = len(compliance_results) - comply_count
        
        reasoning = []
        warnings = []
        
        # === CRITICAL SIGNALS → AUTO REJECT ===
        if risk_level == "CRITICAL":
            reasoning.append("Critical risk level detected")
            return {
                "recommendation": "REJECT",
                "confidence": 0.95,
                "reasoning": reasoning,
                "conditions": [],
                "warnings": ["CRITICAL RISK - Auto-rejection recommended"],
            }
        
        # === VERIFICATION FAILURES ===
        if verification_failures >= 3:
            reasoning.append(f"{verification_failures} critical verifications failed")
            warnings.append(f"Multiple verification failures ({verification_failures})")
        elif verification_failures > 0:
            reasoning.append(f"{verification_failures} verification(s) failed")
        
        # === COMPLIANCE VIOLATIONS ===
        if fail_count >= 3:
            reasoning.append(f"{fail_count} compliance rule(s) violated")
            return {
                "recommendation": "REJECT",
                "confidence": 0.85,
                "reasoning": reasoning,
                "conditions": [],
                "warnings": ["Multiple compliance violations detected"],
            }
        elif fail_count > 0:
            reasoning.append(f"{fail_count} compliance issue(s) detected")
        
        # === HIGH RISK WITH ISSUES ===
        if risk_level == "HIGH" and (fail_count > 0 or verification_failures > 0):
            reasoning.append("HIGH risk with active compliance/verification issues")
            return {
                "recommendation": "NEEDS_CLARIFICATION",
                "confidence": 0.80,
                "reasoning": reasoning,
                "conditions": [
                    "Request clarification on compliance violations",
                    "Request additional documentation",
                ],
                "warnings": ["HIGH risk - clarification required"],
            }
        
        # === PENDING CLARIFICATIONS ===
        if clarifications_pending > 0:
            reasoning.append(f"{clarifications_pending} clarification(s) pending from bidder")
            return {
                "recommendation": "WAIT_FOR_CLARIFICATION",
                "confidence": 0.90,
                "reasoning": reasoning,
                "conditions": ["Await bidder response to clarification requests"],
                "warnings": [],
            }
        
        # === MEDIUM RISK ===
        if risk_level == "MEDIUM":
            if fail_count > 0:
                reasoning.append("MEDIUM risk with minor compliance issues")
                return {
                    "recommendation": "NEEDS_CLARIFICATION",
                    "confidence": 0.75,
                    "reasoning": reasoning,
                    "conditions": [
                        "Request clarification on compliance issues",
                        "Monitor during contract execution",
                    ],
                    "warnings": ["Recommend conditions for approval"],
                }
            else:
                reasoning.append("MEDIUM risk with no compliance violations")
                return {
                    "recommendation": "VERIFY",
                    "confidence": 0.70,
                    "reasoning": reasoning,
                    "conditions": ["Recommend conditions or monitoring"],
                    "warnings": ["MEDIUM risk - consider conditions"],
                }
        
        # === LOW RISK ===
        if risk_level == "LOW":
            if fail_count == 0 and verification_failures == 0:
                reasoning.append("LOW risk with all compliance rules passed")
                return {
                    "recommendation": "VERIFY",
                    "confidence": 0.95,
                    "reasoning": reasoning,
                    "conditions": [],
                    "warnings": [],
                }
            else:
                reasoning.append("LOW risk despite minor issues")
                return {
                    "recommendation": "VERIFY",
                    "confidence": 0.85,
                    "reasoning": reasoning,
                    "conditions": ["Minor issues identified but low overall risk"],
                    "warnings": [],
                }
        
        # === DEFAULT ===
        return {
            "recommendation": "MANUAL_REVIEW",
            "confidence": 0.50,
            "reasoning": ["Unable to auto-generate recommendation - manual review required"],
            "conditions": [],
            "warnings": ["Complex decision pattern detected"],
        }
    
    @staticmethod
    def validate_recommendation(
        recommendation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate recommendation before presenting to officer.
        
        Args:
            recommendation: Recommendation dict
            
        Returns:
            Validation result with:
            - is_valid: Boolean
            - issues: List of issues found
            - suggestion: Any suggestion for officer
        """
        
        issues = []
        
        # Check required fields
        if "recommendation" not in recommendation:
            issues.append("Missing recommendation field")
        
        if "confidence" not in recommendation:
            issues.append("Missing confidence score")
        else:
            conf = recommendation["confidence"]
            if not 0.0 <= conf <= 1.0:
                issues.append(f"Invalid confidence score: {conf}")
        
        if "reasoning" not in recommendation:
            issues.append("Missing reasoning list")
        
        # Validate recommendation value
        valid_recs = ["VERIFY", "REJECT", "NEEDS_CLARIFICATION", "WAIT_FOR_CLARIFICATION", "MANUAL_REVIEW"]
        if recommendation.get("recommendation") not in valid_recs:
            issues.append(f"Invalid recommendation: {recommendation.get('recommendation')}")
        
        # Check for risky low-confidence decisions
        if recommendation.get("confidence", 1.0) < 0.60:
            suggestion = "Low confidence score - recommend additional expert review"
        else:
            suggestion = None
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "suggestion": suggestion,
        }


class OfficerDecisionWorkflow:
    """Manage officer decision workflow with state transitions."""
    
    @staticmethod
    def can_make_decision(
        db: Session,
        bid_id: str,
    ) -> tuple:
        """Check if officer can make final decision on bid.
        
        Args:
            db: Database session
            bid_id: Bid ID
            
        Returns:
            Tuple of (can_decide, reason)
        """
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        
        bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
        if not bid:
            return False, "Bid not found"
        
        # Check bid status
        if bid.status != "SUBMITTED":
            return False, f"Bid must be in SUBMITTED status, currently: {bid.status}"
        
        # Check if all mandatory documents uploaded
        from app.models.models import Document
        doc_count = db.query(Document).filter(Document.bid_id == bid_id_uuid).count()
        if doc_count == 0:
            return False, "No documents uploaded for bid"
        
        # Check if pending clarifications exist
        pending_clarifications = db.query(ClarificationRequest).filter(
            ClarificationRequest.bid_id == bid_id_uuid,
            ClarificationRequest.status == "PENDING"
        ).count()
        
        if pending_clarifications > 0:
            return False, f"{pending_clarifications} pending clarification(s) must be resolved"
        
        return True, "Bid ready for decision"
    
    @staticmethod
    def transition_bid_state(
        db: Session,
        bid_id: str,
        from_state: str,
        to_state: str,
        actor_id: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Transition bid to new state with validation.
        
        Args:
            db: Database session
            bid_id: Bid ID
            from_state: Current state
            to_state: Target state
            actor_id: Officer user ID
            reason: Transition reason
            
        Returns:
            Transition result with status and details
        """
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        actor_id_uuid = uuid.UUID(actor_id) if isinstance(actor_id, str) else actor_id
        
        # Validate state transition
        valid_transitions = {
            "DRAFT": ["SUBMITTED"],
            "SUBMITTED": ["UNDER_REVIEW", "REJECTED", "VERIFIED"],
            "UNDER_REVIEW": ["VERIFIED", "REJECTED", "NEEDS_CLARIFICATION"],
            "NEEDS_CLARIFICATION": ["UNDER_REVIEW", "VERIFIED", "REJECTED"],
            "VERIFIED": ["APPROVED"],
            "REJECTED": [],  # Terminal state
            "APPROVED": [],  # Terminal state
        }
        
        if from_state not in valid_transitions:
            return {
                "success": False,
                "error": f"Unknown state: {from_state}",
            }
        
        if to_state not in valid_transitions.get(from_state, []):
            return {
                "success": False,
                "error": f"Invalid transition from {from_state} to {to_state}",
            }
        
        # Update bid status
        bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
        if not bid:
            return {"success": False, "error": "Bid not found"}
        
        bid.status = to_state
        db.flush()
        
        # Log state transition
        OfficerDecisionWorkflow._log_state_transition(
            db,
            bid_id_uuid,
            from_state,
            to_state,
            actor_id_uuid,
            reason,
        )
        
        db.commit()
        
        return {
            "success": True,
            "bid_id": str(bid_id_uuid),
            "from_state": from_state,
            "to_state": to_state,
            "transitioned_at": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def _log_state_transition(
        db: Session,
        bid_id: uuid.UUID,
        from_state: str,
        to_state: str,
        actor_id: uuid.UUID,
        reason: Optional[str],
    ):
        """Log state transition as audit event."""
        last_event = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).first()
        prev_hash = last_event.event_hash if last_event else "GENESIS_HASH"
        
        payload = {
            "from_state": from_state,
            "to_state": to_state,
            "reason": reason,
        }
        event_data = f"BID_STATE_TRANSITIONED:bid:{str(bid_id)}:{str(actor_id)}:{str(payload)}:{prev_hash}"
        event_hash = hashlib.sha256(event_data.encode()).hexdigest()
        
        audit_event = AuditEvent(
            id=uuid.uuid4(),
            event_type="BID_STATE_TRANSITIONED",
            entity_type="bid",
            entity_id=bid_id,
            actor_id=actor_id,
            payload=payload,
            prev_hash=prev_hash,
            event_hash=event_hash,
        )
        db.add(audit_event)


class OfficerDashboardHelper:
    """Helper for generating officer dashboard data."""
    
    @staticmethod
    def get_bid_summary(
        db: Session,
        bid_id: str,
    ) -> Dict[str, Any]:
        """Get comprehensive bid summary for officer dashboard.
        
        Args:
            db: Database session
            bid_id: Bid ID
            
        Returns:
            Summary with all key information for decision
        """
        bid_id_uuid = uuid.UUID(bid_id) if isinstance(bid_id, str) else bid_id
        
        bid = db.query(Bid).filter(Bid.id == bid_id_uuid).first()
        if not bid:
            return {}
        
        # Get compliance assessment
        compliance_results = db.query(ComplianceResult).filter(
            ComplianceResult.bid_id == bid_id_uuid
        ).all()
        
        compliance_pass = sum(1 for c in compliance_results if c.explanation == "PASS")
        compliance_fail = len(compliance_results) - compliance_pass
        
        # Get risk assessment
        risk = db.query(RiskAssessment).filter(
            RiskAssessment.bid_id == bid_id_uuid
        ).first()
        
        # Get pending clarifications
        pending_clarifs = db.query(ClarificationRequest).filter(
            ClarificationRequest.bid_id == bid_id_uuid,
            ClarificationRequest.status == "PENDING"
        ).count()
        
        return {
            "bid_id": str(bid_id_uuid),
            "bid_status": bid.status,
            "bidder_org_id": str(bid.bidder_org_id),
            "compliance": {
                "passed": compliance_pass,
                "failed": compliance_fail,
                "total": len(compliance_results),
            },
            "risk": {
                "score": float(risk.total_score) if risk else 0.0,
                "level": risk.risk_level if risk else "UNKNOWN",
            },
            "pending_clarifications": pending_clarifs,
            "ready_for_decision": pending_clarifs == 0,
        }
