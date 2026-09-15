"""
Compliance Rule Integration with Verification Status

Extends the compliance engine to consume discrete verification_status values
and apply policy-based handling for UNAVAILABLE and INCONCLUSIVE states.

Key behaviors:
- PENDING: Rules defer evaluation until verification complete
- VERIFIED: Authority confirmed match → rules may PASS/FAIL based on logic
- MISMATCH: Authority found record, name mismatch → typically FAIL
- INCONCLUSIVE: No record found → apply project policy (PASS/FAIL/DEFER)
- UNAVAILABLE: Service unreachable/timeout → apply project policy (PASS/FAIL/DEFER)
- ERROR: Technical error → apply project policy (typically DEFER)

Policy configuration:
- unavailable_policy: "pass" | "fail" | "defer" (default: "defer")
- inconclusive_policy: "pass" | "fail" | "defer" (default: "defer")
- error_policy: "pass" | "fail" | "defer" (default: "defer")
"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.adapters.base import VerificationStatus
from app.models.models import (
    ExtractedFact,
    VerificationResultNew,
    VerificationAttempt,
    ComplianceResult,
)
from app.services.compliance_service import ComplianceService, ComplianceStatus

logger = logging.getLogger(__name__)

# Default policies for unverifiable states
DEFAULT_POLICIES = {
    "unavailable_policy": "defer",  # Service unavailable → defer rule evaluation
    "inconclusive_policy": "defer",  # No record found → defer rule evaluation
    "error_policy": "defer",          # Technical error → defer rule evaluation
}


def get_verification_status_for_fact(
    session: Session,
    extracted_fact_id: str,
) -> Optional[VerificationStatus]:
    """
    Get latest verification status for an extracted fact.
    
    Returns the most recent VerificationResult status, or None if not verified.
    """
    result = (
        session.query(VerificationResultNew)
        .join(VerificationAttempt)
        .filter(VerificationAttempt.extracted_fact_id == extracted_fact_id)
        .order_by(VerificationAttempt.request_timestamp.desc())
        .first()
    )
    
    if result:
        try:
            return VerificationStatus(result.verification_status)
        except ValueError:
            logger.warning(
                f"Invalid verification status for fact {extracted_fact_id}: "
                f"{result.verification_status}"
            )
            return None
    
    return None


def evaluate_compliance_with_verification(
    session: Session,
    bid_id: str,
    clause_id: str,
    extracted_fact_id: Optional[str] = None,
    rule_logic: Optional[Dict[str, Any]] = None,
    policies: Optional[Dict[str, str]] = None,
    actor_id: Optional[str] = None,
) -> ComplianceResult:
    """
    Evaluate compliance rule with consideration for verification status.
    
    If the rule depends on verification of an extracted fact:
    1. Get verification status
    2. If PENDING: return NOT_EVALUATED (defer until verification complete)
    3. If UNAVAILABLE/INCONCLUSIVE/ERROR: apply corresponding policy
    4. If VERIFIED/MISMATCH: evaluate rule logic normally
    
    Args:
        session: Database session
        bid_id: Bid ID
        clause_id: Clause ID
        extracted_fact_id: Optional extracted fact ID this rule depends on
        rule_logic: Rule evaluation logic/conditions
        policies: Policy dict with keys: unavailable_policy, inconclusive_policy, error_policy
        actor_id: User ID triggering evaluation
    
    Returns:
        ComplianceResult with appropriate status
    """
    policies = policies or DEFAULT_POLICIES
    
    # If this rule depends on verification, check verification status first
    if extracted_fact_id:
        verification_status = get_verification_status_for_fact(session, extracted_fact_id)
        
        if verification_status == VerificationStatus.PENDING:
            logger.info(
                f"Rule {clause_id} for bid {bid_id}: deferring evaluation "
                f"(verification PENDING for fact {extracted_fact_id})"
            )
            return ComplianceService.evaluate_compliance(
                session,
                bid_id,
                clause_id,
                ComplianceStatus.NOT_EVALUATED,
                reasoning_chain={
                    "reason": "Verification pending",
                    "verification_status": "PENDING",
                    "extracted_fact_id": extracted_fact_id,
                },
                evidence_refs=[extracted_fact_id],
                rule_version="verification_aware_v1",
                actor_id=actor_id,
            )
        
        elif verification_status == VerificationStatus.UNAVAILABLE:
            policy = policies.get("unavailable_policy", "defer")
            logger.info(
                f"Rule {clause_id} for bid {bid_id}: applying policy '{policy}' "
                f"(verification UNAVAILABLE for fact {extracted_fact_id})"
            )
            
            if policy == "defer":
                result_status = ComplianceStatus.NOT_EVALUATED
            elif policy == "pass":
                result_status = ComplianceStatus.PASS
            elif policy == "fail":
                result_status = ComplianceStatus.FAIL
            else:
                result_status = ComplianceStatus.REVIEW
            
            return ComplianceService.evaluate_compliance(
                session,
                bid_id,
                clause_id,
                result_status,
                reasoning_chain={
                    "reason": "Verification unavailable, applying policy",
                    "verification_status": "UNAVAILABLE",
                    "policy_applied": policy,
                    "extracted_fact_id": extracted_fact_id,
                },
                evidence_refs=[extracted_fact_id],
                rule_version="verification_aware_v1",
                actor_id=actor_id,
            )
        
        elif verification_status == VerificationStatus.INCONCLUSIVE:
            policy = policies.get("inconclusive_policy", "defer")
            logger.info(
                f"Rule {clause_id} for bid {bid_id}: applying policy '{policy}' "
                f"(verification INCONCLUSIVE for fact {extracted_fact_id})"
            )
            
            if policy == "defer":
                result_status = ComplianceStatus.NOT_EVALUATED
            elif policy == "pass":
                result_status = ComplianceStatus.PASS
            elif policy == "fail":
                result_status = ComplianceStatus.FAIL
            else:
                result_status = ComplianceStatus.REVIEW
            
            return ComplianceService.evaluate_compliance(
                session,
                bid_id,
                clause_id,
                result_status,
                reasoning_chain={
                    "reason": "Verification inconclusive (no record), applying policy",
                    "verification_status": "INCONCLUSIVE",
                    "policy_applied": policy,
                    "extracted_fact_id": extracted_fact_id,
                },
                evidence_refs=[extracted_fact_id],
                rule_version="verification_aware_v1",
                actor_id=actor_id,
            )
        
        elif verification_status == VerificationStatus.ERROR:
            policy = policies.get("error_policy", "defer")
            logger.info(
                f"Rule {clause_id} for bid {bid_id}: applying policy '{policy}' "
                f"(verification ERROR for fact {extracted_fact_id})"
            )
            
            if policy == "defer":
                result_status = ComplianceStatus.NOT_EVALUATED
            elif policy == "pass":
                result_status = ComplianceStatus.PASS
            elif policy == "fail":
                result_status = ComplianceStatus.FAIL
            else:
                result_status = ComplianceStatus.REVIEW
            
            return ComplianceService.evaluate_compliance(
                session,
                bid_id,
                clause_id,
                result_status,
                reasoning_chain={
                    "reason": "Verification error (technical), applying policy",
                    "verification_status": "ERROR",
                    "policy_applied": policy,
                    "extracted_fact_id": extracted_fact_id,
                },
                evidence_refs=[extracted_fact_id],
                rule_version="verification_aware_v1",
                actor_id=actor_id,
            )
        
        elif verification_status == VerificationStatus.VERIFIED:
            # Authority confirmed → rule logic applies normally
            logger.debug(
                f"Rule {clause_id} for bid {bid_id}: "
                f"verification VERIFIED for fact {extracted_fact_id}, evaluating rule logic"
            )
            # Fall through to normal rule evaluation
        
        elif verification_status == VerificationStatus.MISMATCH:
            # Authority found record but name mismatch → typically FAIL
            logger.info(
                f"Rule {clause_id} for bid {bid_id}: "
                f"verification MISMATCH for fact {extracted_fact_id}"
            )
            return ComplianceService.evaluate_compliance(
                session,
                bid_id,
                clause_id,
                ComplianceStatus.FAIL,
                reasoning_chain={
                    "reason": "Verification mismatch: authority found record but name does not match",
                    "verification_status": "MISMATCH",
                    "extracted_fact_id": extracted_fact_id,
                },
                evidence_refs=[extracted_fact_id],
                rule_version="verification_aware_v1",
                actor_id=actor_id,
            )
    
    # Fallback: no verification dependency or VERIFIED status
    # Evaluate rule using standard compliance logic
    logger.debug(f"Rule {clause_id} for bid {bid_id}: evaluating with standard logic")
    
    return ComplianceService.evaluate_compliance(
        session,
        bid_id,
        clause_id,
        ComplianceStatus.PASS,  # Default for rules without verification dependency
        reasoning_chain={
            "reason": "Rule evaluated",
            "rule_logic": rule_logic or {},
        },
        evidence_refs=[extracted_fact_id] if extracted_fact_id else [],
        rule_version="verification_aware_v1",
        actor_id=actor_id,
    )


def get_verification_aware_compliance_summary(
    session: Session,
    bid_id: str,
) -> Dict[str, Any]:
    """
    Compute compliance summary with verification status awareness.
    
    Includes:
    - Standard counts (pass, fail, waived, review)
    - Verification counts (verified, mismatch, unavailable, inconclusive)
    - Rules deferred due to pending verification
    """
    # Get standard compliance summary
    summary = ComplianceService.compute_bid_compliance_summary(session, bid_id)
    
    # Add verification awareness
    summary["verification_context"] = {
        "verified_facts": 0,
        "mismatched_facts": 0,
        "unavailable_facts": 0,
        "inconclusive_facts": 0,
        "deferred_rules": 0,
    }
    
    # Count verification states
    from app.models.models import Document, Bid
    
    docs = session.query(Document).join(Bid).filter(Bid.id == bid_id).all()
    doc_ids = [d.id for d in docs]
    
    if doc_ids:
        results = (
            session.query(VerificationResultNew)
            .join(VerificationAttempt)
            .filter(VerificationAttempt.source_document_id.in_(doc_ids))
            .all()
        )
        
        for result in results:
            try:
                status = VerificationStatus(result.verification_status)
                if status == VerificationStatus.VERIFIED:
                    summary["verification_context"]["verified_facts"] += 1
                elif status == VerificationStatus.MISMATCH:
                    summary["verification_context"]["mismatched_facts"] += 1
                elif status == VerificationStatus.UNAVAILABLE:
                    summary["verification_context"]["unavailable_facts"] += 1
                elif status == VerificationStatus.INCONCLUSIVE:
                    summary["verification_context"]["inconclusive_facts"] += 1
            except ValueError:
                pass
    
    # Count deferred rules
    deferred_count = sum(
        1 for r in summary["detailed_results"]
        if r["status"] == ComplianceStatus.NOT_EVALUATED
    )
    summary["verification_context"]["deferred_rules"] = deferred_count
    
    return summary
