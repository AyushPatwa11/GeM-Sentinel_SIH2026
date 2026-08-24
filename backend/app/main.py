"""
GeM Sentinel API — hackathon-runnable FastAPI app.

Uses an in-memory store (app.demo_data) instead of live Postgres so the
whole stack runs with zero infra setup. Every response shape matches the
locked API contracts; swapping in real DB-backed queries later changes
only this file's internals, not the frontend or the contract.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.demo_data import BIDS, CLAUSES, TENDER, TENDER_VERSION
from app.services.evaluation import evaluate_bid

app = FastAPI(title="GeM Sentinel API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # hackathon demo only — restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- in-memory state ----
_evaluation_cache: dict[str, dict] = {}
_decisions: dict[str, dict] = {}
_audit_log: list[dict] = []


def _audit(event_type: str, entity_id: str, payload: dict):
    _audit_log.append(
        {
            "id": str(uuid.uuid4()),
            "event_type": event_type,
            "entity_id": entity_id,
            "payload": payload,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )


# =========================================================
# Auth (stub — role inferred from a query flag for demo speed)
# =========================================================

class LoginRequest(BaseModel):
    email: str
    password: str
    role: str = "officer"


@app.post("/api/auth/login")
def login(body: LoginRequest):
    if body.role not in ("officer", "bidder"):
        raise HTTPException(400, "role must be 'officer' or 'bidder'")
    return {
        "access_token": f"demo-token-{body.role}-{uuid.uuid4().hex[:8]}",
        "role": body.role,
        "name": "Ravi Sharma" if body.role == "officer" else "Bidder User",
    }


# =========================================================
# Officer portal
# =========================================================

@app.get("/api/officer/tenders")
def list_tenders():
    return [{**TENDER, "version": TENDER_VERSION["version_number"]}]


@app.get("/api/officer/tenders/{tender_id}/clauses")
def get_clauses(tender_id: str):
    if tender_id != TENDER["id"]:
        raise HTTPException(404, "tender not found")
    return CLAUSES


@app.get("/api/officer/bids")
def list_bids():
    out = []
    for bid_id, bid in BIDS.items():
        cached = _evaluation_cache.get(bid_id)
        out.append(
            {
                "bid_id": bid_id,
                "bidder_org_name": bid["bidder_org_name"],
                "status": bid["status"],
                "compliance_status": cached["compliance_status"] if cached else "NOT_EVALUATED",
                "risk_level": cached["risk_assessment"]["risk_level"] if cached else None,
                "decision": _decisions.get(bid_id, {}).get("final_decision", "PENDING"),
            }
        )
    # sort risk-desc (HIGH > MEDIUM > LOW > None) to match the dashboard's default sort
    order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, None: 3}
    out.sort(key=lambda b: order.get(b["risk_level"], 3))
    return out


@app.get("/api/officer/bids/{bid_id}")
async def get_bid_detail(bid_id: str):
    if bid_id not in BIDS:
        raise HTTPException(404, "bid not found")
    if bid_id not in _evaluation_cache:
        _evaluation_cache[bid_id] = await evaluate_bid(bid_id)
    result = dict(_evaluation_cache[bid_id])
    result["decision"] = _decisions.get(bid_id)
    return result


@app.post("/api/officer/bids/{bid_id}/evaluate")
async def evaluate(bid_id: str):
    if bid_id not in BIDS:
        raise HTTPException(404, "bid not found")
    result = await evaluate_bid(bid_id)
    _evaluation_cache[bid_id] = result
    _audit("BID_EVALUATED", bid_id, {"compliance_status": result["compliance_status"]})
    return result


class DecisionRequest(BaseModel):
    final_decision: str  # VERIFIED | NON_COMPLIANT | NEEDS_CLARIFICATION
    override_reason: Optional[str] = None


@app.post("/api/officer/bids/{bid_id}/decision")
async def decide(bid_id: str, body: DecisionRequest):
    if bid_id not in BIDS:
        raise HTTPException(404, "bid not found")
    if bid_id not in _evaluation_cache:
        _evaluation_cache[bid_id] = await evaluate_bid(bid_id)

    ai_rec = _evaluation_cache[bid_id]["ai_recommendation"]
    if body.final_decision != ai_rec and not body.override_reason:
        raise HTTPException(422, "override_reason is required when diverging from the AI recommendation")

    decision = {
        "bid_id": bid_id,
        "ai_recommendation": ai_rec,
        "final_decision": body.final_decision,
        "override_reason": body.override_reason,
        "decided_at": datetime.now(timezone.utc).isoformat(),
    }
    _decisions[bid_id] = decision
    _audit("OFFICER_DECISION", bid_id, decision)
    return decision


@app.get("/api/officer/audit/bids/{bid_id}")
def get_audit(bid_id: str):
    return [e for e in _audit_log if e["entity_id"] == bid_id]


# =========================================================
# Bidder portal
# =========================================================

@app.get("/api/bidder/tenders")
def bidder_tenders():
    return [{**TENDER, "version": TENDER_VERSION["version_number"]}]


@app.get("/api/bidder/tenders/{tender_id}/requirements")
def bidder_requirements(tender_id: str):
    if tender_id != TENDER["id"]:
        raise HTTPException(404, "tender not found")
    return [
        {"clause_id": c["id"], "raw_text": c["raw_text"], "category": c["category"], "mandatory": c["mandatory"]}
        for c in CLAUSES
    ]


@app.get("/api/bidder/bids/{bid_id}/readiness")
async def readiness(bid_id: str):
    """Read-only rerun of the rule engine for pre-submission feedback —
    does not persist to compliance_results/audit, matching the locked
    contract (bidder can iterate freely without polluting the record)."""
    if bid_id not in BIDS:
        raise HTTPException(404, "bid not found")
    result = await evaluate_bid(bid_id)
    total_clauses = len(result["compliance_results"])
    satisfied = sum(1 for c in result["compliance_results"] if c["status"] == "PASS")
    readiness_percent = round(100 * satisfied / total_clauses) if total_clauses else 0

    items = []
    for c in result["compliance_results"]:
        label = {
            "PASS": "SATISFIED",
            "FAIL": "MISSING" if c["mandatory"] else "WEAK_EVIDENCE",
            "WAIVED": "SATISFIED",
            "REVIEW": "REVIEW",
            "NOT_EVALUATED": "REVIEW",
        }[c["status"]]
        items.append({"clause_id": c["clause_id"], "requirement_summary": c["clause_text"], "status": label})

    return {"readiness_percent": readiness_percent, "items": items}


@app.get("/api/health")
def health():
    return {"status": "ok"}
