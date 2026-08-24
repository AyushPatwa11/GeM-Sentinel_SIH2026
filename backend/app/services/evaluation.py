"""
Orchestrates one bid evaluation end-to-end:

  facts (+ live adapter check for identity) -> rule engine -> risk engine
  -> aggregate status -> officer-facing payload

This is the synchronous MVP version of the request flow from the
architecture review (no queue — acceptable at hackathon data volume).
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.adapters.base import VerificationClaim
from app.adapters.mock_adapters import BlacklistMockAdapter, GSTNMockAdapter
from app.demo_data import BIDS, CLAUSES_BY_TENDER_VERSION
from app.services.risk.scoring import RiskSignal, score_bid
from app.services.rules.evaluator import aggregate_bid_status, evaluate_clause
from app.services.rules.schema import ClauseStatus, Condition, Fact, LogicNode, VerificationStatus

_gstn = GSTNMockAdapter()
_blacklist = BlacklistMockAdapter()


def _dict_to_node(d: dict) -> LogicNode:
    return LogicNode(
        type=d["type"],
        condition=Condition(**d["condition"]) if d.get("condition") else None,
        children=[_dict_to_node(c) for c in d.get("children", [])],
        exceptions=[
            {"applies_if": Condition(**e["applies_if"]), "waives": e.get("waives", True)}
            for e in d.get("exceptions", [])
        ],
    )


async def _resolve_identity_match(bid: dict) -> tuple[bool, VerificationStatus, str]:
    """Live-checks GSTIN identity against the mock GSTN registry — this is
    the actual contradiction-detection mechanism, not a hardcoded flag."""
    result = await _gstn.verify(VerificationClaim(field_name="gstin", claimed_value=bid["gstin"]))
    if result.status == VerificationStatus.UNAVAILABLE:
        return False, VerificationStatus.UNAVAILABLE, "GSTN registry unavailable — retry required"
    if result.status == VerificationStatus.INCONCLUSIVE:
        return False, VerificationStatus.INCONCLUSIVE, "GSTIN not found in GSTN registry"

    registry_name = (result.data or {}).get("legal_name", "").strip().lower()
    claimed_name = bid["bidder_org_name"].strip().lower()
    match = registry_name == claimed_name
    status = VerificationStatus.VERIFIED if match else VerificationStatus.MISMATCH
    evidence = (
        f"GSTN registry legal_name = '{result.data.get('legal_name')}' "
        f"vs bid organization = '{bid['bidder_org_name']}'"
    )
    return match, status, evidence


async def _resolve_debarment(bid: dict) -> tuple[bool, VerificationStatus, str]:
    result = await _blacklist.verify(VerificationClaim(field_name="debarment_status", claimed_value=bid["gstin"]))
    clear = result.status == VerificationStatus.VERIFIED
    return clear, result.status, result.evidence or ""


async def evaluate_bid(bid_id: str, custom_bid: dict | None = None) -> Dict[str, Any]:
    bid = custom_bid or BIDS[bid_id]

    # Resolve the live adapter checks
    identity_match, identity_status, identity_evidence = await _resolve_identity_match(bid)
    debarment_clear, debarment_status, debarment_evidence = await _resolve_debarment(bid)

    # Base facts or dynamically constructed facts
    facts_dict: Dict[str, dict] = {}
    if "facts" in bid and bid["facts"]:
        for f in bid["facts"]:
            facts_dict[f["field"]] = dict(f)
    else:
        # Default fact generator for new submissions based on uploaded documents & claims
        has_gst = any(d.get("doc_type") == "GST_CERT" for d in bid.get("documents", []))
        has_pan = any(d.get("doc_type") == "PAN" for d in bid.get("documents", []))
        has_fin = any(d.get("doc_type") == "FINANCIAL_STMT" for d in bid.get("documents", []))
        has_exp = any(d.get("doc_type") == "EXPERIENCE_CERT" for d in bid.get("documents", []))
        has_udyam = any(d.get("doc_type") == "UDYAM_CERT" for d in bid.get("documents", []))

        turnover = bid.get("annual_turnover", 15_000_000 if has_fin else 0)
        project_count = bid.get("similar_project_count", 3 if has_exp else 0)
        emd_paid = bid.get("emd_paid", True if not has_udyam else False)
        msme = bid.get("msme_exemption", has_udyam)

        facts_dict = {
            "gst_valid": {"field": "gst_valid", "value": has_gst, "confidence": 0.98 if has_gst else 0.0, "evidence_ref": "doc-gst", "evidence_span": f"GSTIN {bid.get('gstin', '')} registration certificate"},
            "pan_valid": {"field": "pan_valid", "value": has_pan, "confidence": 0.97 if has_pan else 0.0, "evidence_ref": "doc-pan", "evidence_span": f"PAN {bid.get('pan', '')} verification"},
            "gstin_identity_match": {"field": "gstin_identity_match", "value": identity_match, "confidence": 0.98, "evidence_ref": "doc-gst", "evidence_span": identity_evidence},
            "annual_turnover": {"field": "annual_turnover", "value": turnover, "confidence": 0.95 if has_fin else 0.0, "evidence_ref": "doc-fin", "evidence_span": f"Declared Annual Turnover: ₹{turnover:,}"},
            "similar_project_count": {"field": "similar_project_count", "value": project_count, "confidence": 0.90 if has_exp else 0.0, "evidence_ref": "doc-exp", "evidence_span": f"{project_count} similar completed project contracts"},
            "emd_paid": {"field": "emd_paid", "value": emd_paid, "confidence": 0.95, "evidence_ref": "doc-emd", "evidence_span": "EMD payment receipt" if emd_paid else "No EMD receipt"},
            "msme_exemption": {"field": "msme_exemption", "value": msme, "confidence": 0.94 if msme else 0.90, "evidence_ref": "doc-udyam", "evidence_span": "Udyam MSME Certificate" if msme else "No MSME exemption claimed"},
            "debarment_clear": {"field": "debarment_clear", "value": debarment_clear, "confidence": 1.0, "evidence_ref": "doc-gst", "evidence_span": debarment_evidence},
            "experience_cert_present": {"field": "experience_cert_present", "value": has_exp, "confidence": 0.90 if has_exp else 0.0, "evidence_ref": "doc-exp" if has_exp else None, "evidence_span": "Experience certificate attached" if has_exp else None},
        }

    facts_by_field: Dict[str, Fact] = {}
    for field_name, f in facts_dict.items():
        vstatus = None
        if field_name == "gstin_identity_match":
            f["value"] = identity_match
            vstatus = identity_status
        if field_name == "debarment_clear":
            f["value"] = debarment_clear
            vstatus = debarment_status
        facts_by_field[field_name] = Fact(
            field=f["field"],
            value=f["value"],
            meets_threshold=f["confidence"] >= 0.75 if f.get("confidence") is not None else False,
            verification_status=vstatus,
            evidence_ref=f.get("evidence_ref"),
        )

    facts = list(facts_by_field.values())

    compliance_results: List[Dict[str, Any]] = []
    clause_outcomes: List[tuple[bool, ClauseStatus]] = []
    risk_signals: List[RiskSignal] = []

    tender_version_id = bid.get("tender_version_id", "tv-101-v1")
    clauses = CLAUSES_BY_TENDER_VERSION.get(tender_version_id, CLAUSES_BY_TENDER_VERSION["tv-101-v1"])

    for clause in clauses:
        node = _dict_to_node(clause["logic_tree"])

        if clause.get("ambiguity_flag"):
            result_status = ClauseStatus.REVIEW
            reasoning = [f"Clause flagged ambiguous: {clause.get('ambiguity_reason')}"]
            evidence_refs: List[str] = []
        else:
            result = evaluate_clause(node, facts)
            result_status = result.status
            reasoning = result.reasoning_chain
            evidence_refs = result.evidence_refs

        compliance_results.append(
            {
                "clause_id": clause["id"],
                "clause_text": clause["raw_text"],
                "mandatory": clause["mandatory"],
                "status": result_status.value,
                "reasoning_chain": reasoning,
                "evidence_refs": evidence_refs,
            }
        )
        clause_outcomes.append((clause["mandatory"], result_status))

        if result_status == ClauseStatus.FAIL and clause["id"] in ("clause-gstin-identity", "clause-102-gst-pan"):
            risk_signals.append(
                RiskSignal(signal_type="IDENTIFIER_MISMATCH", severity=1.0, evidence_ref=identity_evidence)
            )
        if result_status == ClauseStatus.FAIL and clause["mandatory"]:
            risk_signals.append(
                RiskSignal(signal_type="MISSING_MANDATORY_DOC", severity=0.6, evidence_ref=clause["id"])
            )

    # Risk signals for return defaulters and missing experience
    for f in facts_dict.values():
        if f.get("field") == "gst_valid" and "DEFAULTER" in (f.get("evidence_span") or ""):
            risk_signals.append(
                RiskSignal(signal_type="UNRESOLVED_REQUIREMENT", severity=0.7, evidence_ref=f.get("evidence_ref") or "gst_defaulter")
            )
        if f.get("field") == "experience_cert_present" and not f.get("value"):
            risk_signals.append(
                RiskSignal(signal_type="UNRESOLVED_REQUIREMENT", severity=0.4, evidence_ref="experience_cert_missing")
            )

    risk_assessment = score_bid(risk_signals)
    bid_status = aggregate_bid_status(clause_outcomes)

    ai_recommendation = {
        "NON_COMPLIANT": "NON_COMPLIANT",
        "NEEDS_REVIEW": "NEEDS_CLARIFICATION",
        "COMPLIANT_WITH_FLAGS": "VERIFIED",
        "COMPLIANT": "VERIFIED",
    }[bid_status]

    return {
        "bid_id": bid_id,
        "bidder_org_name": bid["bidder_org_name"],
        "documents": bid.get("documents", []),
        "compliance_status": bid_status,
        "compliance_results": compliance_results,
        "risk_assessment": {
            "total_score": risk_assessment.total_score,
            "risk_level": risk_assessment.risk_level.value,
            "policy_version": risk_assessment.policy_version,
            "signals": [
                {
                    "signal_type": s.signal_type,
                    "weight": s.weight,
                    "severity": s.severity,
                    "contribution": s.contribution,
                    "evidence_ref": s.evidence_ref,
                }
                for s in risk_assessment.signals
            ],
        },
        "ai_recommendation": ai_recommendation,
    }
