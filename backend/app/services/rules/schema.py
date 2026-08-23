"""
Structured schema for the compliance rule engine.

A clause is never a flat rule. It is a logic tree of LEAF / AND / OR nodes,
where a LEAF carries one condition and optional waiver exceptions. This is
what lets the engine correctly evaluate real tender language such as:

  "Bidder must have GST registration AND PAN"                -> AND of two LEAFs
  "Turnover >= 10cr OR two similar projects"                  -> OR of two LEAFs
  "EMD required unless MSME exemption applies"                -> LEAF with an exception
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional, Union

from pydantic import BaseModel, Field, model_validator


class Operator(str, Enum):
    GTE = ">="
    LTE = "<="
    GT = ">"
    LT = "<"
    EQ = "=="
    NEQ = "!="


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    MISMATCH = "MISMATCH"
    UNAVAILABLE = "UNAVAILABLE"
    INCONCLUSIVE = "INCONCLUSIVE"
    PENDING = "PENDING"
    NOT_REQUIRED = "NOT_REQUIRED"


class ClauseStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WAIVED = "WAIVED"
    REVIEW = "REVIEW"
    NOT_EVALUATED = "NOT_EVALUATED"


class Condition(BaseModel):
    field: str
    operator: Operator
    value: Union[float, str, bool]
    unit: Optional[str] = None


class Exception_(BaseModel):
    """A waiver: if `applies_if` is satisfied, the parent LEAF is WAIVED
    instead of evaluated normally (e.g. MSME exemption waives EMD)."""

    applies_if: Condition
    waives: bool = True


class LogicNode(BaseModel):
    type: str = Field(..., pattern="^(LEAF|AND|OR)$")
    condition: Optional[Condition] = None
    children: List["LogicNode"] = Field(default_factory=list)
    exceptions: List[Exception_] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_shape(self):
        if self.type == "LEAF" and self.condition is None:
            raise ValueError("LEAF node requires a condition")
        if self.type in ("AND", "OR") and not self.children:
            raise ValueError(f"{self.type} node requires at least one child")
        return self


LogicNode.model_rebuild()


class Fact(BaseModel):
    """A single extracted/normalized bidder fact used to evaluate a LEAF."""

    field: str
    value: Union[float, str, bool]
    meets_threshold: bool = True
    verification_status: Optional[VerificationStatus] = None
    evidence_ref: Optional[str] = None  # extracted_fact_id or verification_result_id


class ClauseResult(BaseModel):
    status: ClauseStatus
    reasoning_chain: List[str]
    evidence_refs: List[str]
