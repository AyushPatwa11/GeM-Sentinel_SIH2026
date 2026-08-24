"""
GeM Sentinel API — hackathon-runnable FastAPI app.

Uses an in-memory store (app.demo_data) instead of live Postgres so the
whole stack runs with zero infra setup. Every response shape matches the
locked API contracts; swapping in real DB-backed queries later changes
only this file's internals, not the frontend or the contract.
"""
from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.demo_data import BIDS, CLAUSES_BY_TENDER_VERSION, TENDER, TENDER_VERSION, TENDERS, TENDER_VERSIONS
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
_uploaded_documents: dict[str, list[dict]] = {}


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


def _tender_for_bid(bid: dict) -> dict:
    version = TENDER_VERSIONS[bid["tender_version_id"]]
    tender = TENDERS[version["tender_id"]]
    return {**tender, "version": version["version_number"]}


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
    return [{**tender, "version": TENDER_VERSIONS[next(v for v in TENDER_VERSIONS if TENDER_VERSIONS[v]["tender_id"] == tender_id)]["version_number"]} for tender_id, tender in TENDERS.items()]


@app.get("/api/officer/tenders/{tender_id}/clauses")
def get_clauses(tender_id: str):
    version = next((version for version in TENDER_VERSIONS.values() if version["tender_id"] == tender_id), None)
    if version is None:
        raise HTTPException(404, "tender not found")
    return CLAUSES_BY_TENDER_VERSION[version["id"]]


@app.get("/api/officer/bids")
def list_bids():
    out = []
    for bid_id, bid in BIDS.items():
        cached = _evaluation_cache.get(bid_id)
        out.append(
            {
                "bid_id": bid_id,
                "bidder_org_name": bid["bidder_org_name"],
                "tender": _tender_for_bid(bid),
                "status": bid["status"].upper(),
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
    BIDS[bid_id]["status"] = {
        "VERIFIED": "VERIFIED",
        "NON_COMPLIANT": "NON_COMPLIANT",
        "NEEDS_CLARIFICATION": "CLARIFICATION_REQUIRED",
    }[body.final_decision]
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
    return list_tenders()


@app.get("/api/bidder/tenders/{tender_id}/requirements")
def bidder_requirements(tender_id: str):
    version = next((version for version in TENDER_VERSIONS.values() if version["tender_id"] == tender_id), None)
    if version is None:
        raise HTTPException(404, "tender not found")
    return [
        {"clause_id": c["id"], "raw_text": c["raw_text"], "category": c["category"], "mandatory": c["mandatory"]}
        for c in CLAUSES_BY_TENDER_VERSION[version["id"]]
    ]


@app.get("/api/bidder/bids")
def bidder_bids():
    return [
        {
            "id": bid_id,
            "status": bid["status"],
            "bidder_org_name": bid["bidder_org_name"],
            "tender": _tender_for_bid(bid),
        }
        for bid_id, bid in BIDS.items()
    ]


@app.post("/api/bidder/tenders/{tender_id}/bids")
def create_bid_draft(tender_id: str):
    version = next((version for version in TENDER_VERSIONS.values() if version["tender_id"] == tender_id), None)
    if version is None or TENDERS[tender_id]["status"] != "published":
        raise HTTPException(404, "published tender not found")

    existing = next((bid_id for bid_id, bid in BIDS.items() if bid.get("tender_version_id") == version["id"] and bid.get("created_from_bidder_portal")), None)
    if existing:
        return {"id": existing, "status": BIDS[existing]["status"], "tender": _tender_for_bid(BIDS[existing])}

    template = deepcopy(BIDS["bid-northline"])
    bid_id = f"bid-draft-{uuid.uuid4().hex[:8]}"
    template.update(
        {
            "id": bid_id,
            "tender_version_id": version["id"],
            "status": "DRAFT",
            "documents": [],
            "created_from_bidder_portal": True,
        }
    )
    BIDS[bid_id] = template
    _audit("BID_DRAFT_CREATED", bid_id, {"tender_id": tender_id, "tender_version_id": version["id"]})
    return {"id": bid_id, "status": template["status"], "tender": _tender_for_bid(template)}


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

    return {"readiness_percent": readiness_percent, "items": items, "tender": _tender_for_bid(BIDS[bid_id])}


@app.get("/api/bidder/bids/{bid_id}/documents")
def bidder_documents(bid_id: str):
    if bid_id not in BIDS:
        raise HTTPException(404, "bid not found")
    return _uploaded_documents.get(bid_id, [])


@app.post("/api/bidder/bids/{bid_id}/documents")
async def upload_bidder_documents(bid_id: str, files: list[UploadFile] = File(...)):
    """Store document metadata for the demo flow.

    The hackathon app deliberately keeps documents in memory, but the endpoint
    follows a normal multipart upload contract and can be swapped for object
    storage without changing the frontend.
    """
    if bid_id not in BIDS:
        raise HTTPException(404, "bid not found")
    if not files:
        raise HTTPException(422, "select at least one document")

    documents = _uploaded_documents.setdefault(bid_id, [])
    uploaded = []
    for file in files:
        content = await file.read()
        if not file.filename:
            raise HTTPException(422, "each document needs a file name")
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(413, f"{file.filename} exceeds the 10 MB limit")
        document = {
            "id": str(uuid.uuid4()),
            "filename": file.filename,
            "content_type": file.content_type or "application/octet-stream",
            "size_bytes": len(content),
            "uploaded_at": datetime.now(timezone.utc).isoformat(),
        }
        documents.append(document)
        uploaded.append(document)

    # In the demo, document extraction is represented by a deterministic
    # confirmation that the selected bid now has supporting experience
    # evidence.  Keep this scoped to the current bid; uploads for one tender
    # must never alter another bid application's readiness.
    experience_fact = next((fact for fact in BIDS[bid_id]["facts"] if fact["field"] == "experience_cert_present"), None)
    if experience_fact:
        experience_fact.update(
            {
                "value": True,
                "confidence": 0.9,
                "evidence_ref": uploaded[-1]["id"],
                "evidence_span": f"Supporting document uploaded: {uploaded[-1]['filename']}",
            }
        )

    _audit("BIDDER_DOCUMENTS_UPLOADED", bid_id, {"document_ids": [d["id"] for d in uploaded]})
    return uploaded


@app.post("/api/bidder/bids/{bid_id}/submit")
async def submit_bid(bid_id: str):
    if bid_id not in BIDS:
        raise HTTPException(404, "bid not found")
    if BIDS[bid_id]["status"].upper() == "SUBMITTED":
        previous_submission = next(
            (event["payload"] for event in reversed(_audit_log)
             if event["entity_id"] == bid_id and event["event_type"] == "BID_SUBMITTED"),
            None,
        )
        return previous_submission or {
            "bid_id": bid_id,
            "status": "SUBMITTED",
            "submitted_at": None,
            "document_count": len(_uploaded_documents.get(bid_id, [])),
        }

    result = await readiness(bid_id)
    if any(item["status"] == "MISSING" for item in result["items"]):
        raise HTTPException(422, "resolve all mandatory readiness items before submitting")

    BIDS[bid_id]["status"] = "SUBMITTED"
    submission = {
        "bid_id": bid_id,
        "status": "SUBMITTED",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "document_count": len(_uploaded_documents.get(bid_id, [])),
    }
    _audit("BID_SUBMITTED", bid_id, submission)
    return submission


@app.get("/api/bidder/bids/{bid_id}/status")
def bidder_bid_status(bid_id: str):
    """Shared bidder-facing view of the same status and officer decision
    used by the procurement dashboard."""
    if bid_id not in BIDS:
        raise HTTPException(404, "bid not found")
    return {
        "bid_id": bid_id,
        "status": BIDS[bid_id]["status"].upper(),
        "tender": _tender_for_bid(BIDS[bid_id]),
        "decision": _decisions.get(bid_id),
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}
