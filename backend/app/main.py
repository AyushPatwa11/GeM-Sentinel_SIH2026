"""
GeM Sentinel — FastAPI entry point.

Provides health check and compliance/risk evaluation endpoints.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from app.services.rules.schema import LogicNode, Fact, ClauseResult
from app.services.rules.evaluator import evaluate_clause, aggregate_bid_status
from app.services.risk.scoring import RiskSignal, RiskAssessment, score_bid

app = FastAPI(
    title="GeM Sentinel",
    description="Bid verification and compliance engine for GeM procurement",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok"}


# ── Compliance Evaluation ────────────────────────────────────────────
class EvaluateClauseRequest(BaseModel):
    logic_tree: LogicNode
    facts: List[Fact]


@app.post("/api/v1/compliance/evaluate-clause", response_model=ClauseResult)
def api_evaluate_clause(body: EvaluateClauseRequest):
    """Evaluate a single clause's logic tree against a set of bidder facts."""
    return evaluate_clause(body.logic_tree, body.facts)


class ClauseOutcome(BaseModel):
    mandatory: bool
    status: str


class AggregateBidRequest(BaseModel):
    clause_outcomes: List[ClauseOutcome]


class AggregateBidResponse(BaseModel):
    bid_status: str


@app.post("/api/v1/compliance/aggregate-bid", response_model=AggregateBidResponse)
def api_aggregate_bid(body: AggregateBidRequest):
    """Aggregate clause outcomes into a bid-level compliance decision."""
    from app.services.rules.schema import ClauseStatus

    outcomes = [(c.mandatory, ClauseStatus(c.status)) for c in body.clause_outcomes]
    return AggregateBidResponse(bid_status=aggregate_bid_status(outcomes))


# ── Risk Scoring ─────────────────────────────────────────────────────
class RiskSignalRequest(BaseModel):
    signal_type: str
    severity: float
    evidence_ref: str


class ScoreBidRequest(BaseModel):
    signals: List[RiskSignalRequest]


class RiskAssessmentResponse(BaseModel):
    total_score: float
    risk_level: str
    policy_version: str


@app.post("/api/v1/risk/score-bid", response_model=RiskAssessmentResponse)
def api_score_bid(body: ScoreBidRequest):
    """Score a bid's risk level from a set of risk signals."""
    signals = [
        RiskSignal(
            signal_type=s.signal_type,
            severity=s.severity,
            evidence_ref=s.evidence_ref,
        )
        for s in body.signals
    ]
    assessment = score_bid(signals)
    return RiskAssessmentResponse(
        total_score=assessment.total_score,
        risk_level=assessment.risk_level.value,
        policy_version=assessment.policy_version,
    )
