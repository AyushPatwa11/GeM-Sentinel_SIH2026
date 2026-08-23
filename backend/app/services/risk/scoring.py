"""
Risk engine — independent axis from compliance, per locked design.

Compliance asks "does the bidder satisfy the tender rules".
Risk asks "are there signals here that deserve human attention, regardless
of whether the bidder technically passed".

Zero LLM dependency, same as the rule engine — risk is a transparent
weighted sum of verified signals, never a black-box model output.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


# Versioned, documented weights — not hardcoded magic numbers scattered in code.
RISK_POLICY_VERSION = "risk_policy_v1.1"

SIGNAL_WEIGHTS = {
    "MISSING_MANDATORY_DOC": 3.0,
    "IDENTIFIER_MISMATCH": 3.0,
    "CROSS_SOURCE_CONTRADICTION": 2.5,
    "EXPIRED_CERTIFICATE": 2.0,
    "LOW_OCR_CONFIDENCE": 1.0,
    "DUPLICATE_DOCUMENT": 1.5,
    "UNRESOLVED_REQUIREMENT": 1.5,
    "CORRIGENDUM_IMPACT": 1.0,
}

# Thresholds also versioned alongside weights.
RISK_LEVEL_THRESHOLDS = {
    "LOW_MAX": 3.0,
    "MEDIUM_MAX": 8.0,
    # total_score > MEDIUM_MAX -> HIGH
}


@dataclass
class RiskSignal:
    signal_type: str
    severity: float  # 0.0-1.0, how severe this particular instance is
    evidence_ref: str
    weight: float = field(init=False)

    def __post_init__(self):
        if self.signal_type not in SIGNAL_WEIGHTS:
            raise ValueError(f"Unknown risk signal type: {self.signal_type}")
        self.weight = SIGNAL_WEIGHTS[self.signal_type]

    @property
    def contribution(self) -> float:
        return round(self.weight * self.severity, 3)


@dataclass
class RiskAssessment:
    total_score: float
    risk_level: RiskLevel
    signals: List[RiskSignal]
    policy_version: str = RISK_POLICY_VERSION


def score_bid(signals: List[RiskSignal]) -> RiskAssessment:
    total = round(sum(s.contribution for s in signals), 3)

    if total <= RISK_LEVEL_THRESHOLDS["LOW_MAX"]:
        level = RiskLevel.LOW
    elif total <= RISK_LEVEL_THRESHOLDS["MEDIUM_MAX"]:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.HIGH

    return RiskAssessment(total_score=total, risk_level=level, signals=signals)
