"""
Deterministic compliance rule engine.

Zero dependency on any LLM client — this module must never import
app.services.llm_client. That is a structural guarantee (enforced by
tests/test_no_llm_dependency.py) that no AI model can influence a
compliance verdict, even indirectly.

Public entry points:
  evaluate_clause(node, facts)          -> ClauseResult for one clause
  aggregate_bid_status(clause_outcomes) -> bid-level hard-gate decision
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from app.services.rules.schema import (
    ClauseResult,
    ClauseStatus,
    Condition,
    Fact,
    LogicNode,
    Operator,
    VerificationStatus,
)

# Aggregation severity ranking used by AND/OR combination.
# Higher number = "worse" outcome for AND, "better" outcome is PASS/WAIVED for OR.
_SEVERITY = {
    ClauseStatus.FAIL: 3,
    ClauseStatus.REVIEW: 2,
    ClauseStatus.NOT_EVALUATED: 2,
    ClauseStatus.WAIVED: 1,
    ClauseStatus.PASS: 0,
}

_GOODNESS = {
    ClauseStatus.PASS: 3,
    ClauseStatus.WAIVED: 3,
    ClauseStatus.REVIEW: 1,
    ClauseStatus.NOT_EVALUATED: 1,
    ClauseStatus.FAIL: 0,
}


def _compare(actual, operator: Operator, expected) -> bool:
    if operator == Operator.GTE:
        return actual >= expected
    if operator == Operator.LTE:
        return actual <= expected
    if operator == Operator.GT:
        return actual > expected
    if operator == Operator.LT:
        return actual < expected
    if operator == Operator.EQ:
        return actual == expected
    if operator == Operator.NEQ:
        return actual != expected
    raise ValueError(f"Unsupported operator: {operator}")


def _condition_met(condition: Condition, facts: Dict[str, Fact]) -> bool:
    fact = facts.get(condition.field)
    if fact is None:
        return False
    return _compare(fact.value, condition.operator, condition.value)


def _evaluate_leaf(node: LogicNode, facts: Dict[str, Fact]) -> Tuple[ClauseStatus, str, List[str]]:
    # Exceptions/waivers are checked FIRST — a waived clause is satisfied,
    # not failed, even if the underlying condition would otherwise fail.
    for exc in node.exceptions:
        if _condition_met(exc.applies_if, facts) and exc.waives:
            waiver_fact = facts.get(exc.applies_if.field)
            ref = [waiver_fact.evidence_ref] if waiver_fact and waiver_fact.evidence_ref else []
            return (
                ClauseStatus.WAIVED,
                f"Waived: exception condition '{exc.applies_if.field} "
                f"{exc.applies_if.operator.value} {exc.applies_if.value}' was met",
                ref,
            )

    condition = node.condition
    fact = facts.get(condition.field)

    if fact is None:
        return (
            ClauseStatus.REVIEW,
            f"No fact provided for required field '{condition.field}'",
            [],
        )

    if not fact.meets_threshold:
        return (
            ClauseStatus.REVIEW,
            f"Fact '{condition.field}' confidence below required threshold",
            [fact.evidence_ref] if fact.evidence_ref else [],
        )

    if fact.verification_status == VerificationStatus.UNAVAILABLE:
        return (
            ClauseStatus.REVIEW,
            f"Authoritative source unavailable for '{condition.field}' — retry/manual review required",
            [fact.evidence_ref] if fact.evidence_ref else [],
        )

    if fact.verification_status == VerificationStatus.INCONCLUSIVE:
        return (
            ClauseStatus.REVIEW,
            f"Verification inconclusive for '{condition.field}'",
            [fact.evidence_ref] if fact.evidence_ref else [],
        )

    if fact.verification_status == VerificationStatus.MISMATCH:
        return (
            ClauseStatus.FAIL,
            f"Authoritative source contradicts claimed value for '{condition.field}'",
            [fact.evidence_ref] if fact.evidence_ref else [],
        )

    passed = _compare(fact.value, condition.operator, condition.value)
    status = ClauseStatus.PASS if passed else ClauseStatus.FAIL
    reason = (
        f"{condition.field} = {fact.value} {condition.operator.value} "
        f"{condition.value}{' ' + condition.unit if condition.unit else ''} "
        f"-> {status.value}"
    )
    return status, reason, ([fact.evidence_ref] if fact.evidence_ref else [])


def _evaluate_node(node: LogicNode, facts: Dict[str, Fact]) -> Tuple[ClauseStatus, List[str], List[str]]:
    if node.type == "LEAF":
        status, reason, refs = _evaluate_leaf(node, facts)
        return status, [reason], refs

    child_results = [_evaluate_node(child, facts) for child in node.children]
    statuses = [r[0] for r in child_results]
    reasons: List[str] = []
    refs: List[str] = []
    for r in child_results:
        reasons.extend(r[1])
        refs.extend(r[2])

    if node.type == "AND":
        worst = max(statuses, key=lambda s: _SEVERITY[s])
        reasons.insert(0, f"AND branch resolves to {worst.value} (worst-of-children)")
        return worst, reasons, refs

    if node.type == "OR":
        best = max(statuses, key=lambda s: _GOODNESS[s])
        reasons.insert(0, f"OR branch resolves to {best.value} (best-of-children)")
        return best, reasons, refs

    raise ValueError(f"Unknown node type: {node.type}")


def evaluate_clause(node: LogicNode, facts: List[Fact]) -> ClauseResult:
    """Evaluate one clause's logic tree against a set of bidder facts.

    This function is a pure deterministic function of its inputs — same
    node + same facts always yields the same result. No network calls,
    no LLM calls, no randomness.
    """
    facts_by_field = {f.field: f for f in facts}
    status, reasoning_chain, evidence_refs = _evaluate_node(node, facts_by_field)
    return ClauseResult(
        status=status,
        reasoning_chain=reasoning_chain,
        evidence_refs=list(dict.fromkeys(r for r in evidence_refs if r)),  # de-dup, drop None
    )


def aggregate_bid_status(
    clause_outcomes: List[Tuple[bool, ClauseStatus]],
) -> str:
    """Hard-gate aggregation across all clauses of a bid.

    clause_outcomes: list of (mandatory: bool, status: ClauseStatus)

    A mandatory FAIL always makes the bid NON_COMPLIANT regardless of how
    many other clauses PASS — a 95% pass rate never hides one mandatory
    failure. This is the concrete mechanism behind the plan's hard-gate
    requirement.
    """
    mandatory_outcomes = [status for mandatory, status in clause_outcomes if mandatory]

    if any(s == ClauseStatus.FAIL for s in mandatory_outcomes):
        return "NON_COMPLIANT"
    if any(s == ClauseStatus.REVIEW or s == ClauseStatus.NOT_EVALUATED for s in mandatory_outcomes):
        return "NEEDS_REVIEW"

    non_mandatory = [status for mandatory, status in clause_outcomes if not mandatory]
    if any(s == ClauseStatus.FAIL for s in non_mandatory):
        return "COMPLIANT_WITH_FLAGS"

    return "COMPLIANT"
