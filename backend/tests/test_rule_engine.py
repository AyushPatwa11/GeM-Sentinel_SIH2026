import pytest

from app.services.rules.evaluator import aggregate_bid_status, evaluate_clause
from app.services.rules.schema import (
    ClauseStatus,
    Condition,
    Exception_,
    Fact,
    LogicNode,
    Operator,
    VerificationStatus,
)


def test_leaf_pass():
    node = LogicNode(
        type="LEAF",
        condition=Condition(field="annual_turnover", operator=Operator.GTE, value=10_000_000),
    )
    facts = [Fact(field="annual_turnover", value=12_000_000, evidence_ref="fact-1")]
    result = evaluate_clause(node, facts)
    assert result.status == ClauseStatus.PASS
    assert "fact-1" in result.evidence_refs


def test_leaf_fail_threshold_not_met():
    node = LogicNode(
        type="LEAF",
        condition=Condition(field="annual_turnover", operator=Operator.GTE, value=10_000_000),
    )
    facts = [Fact(field="annual_turnover", value=5_000_000, evidence_ref="fact-1")]
    result = evaluate_clause(node, facts)
    assert result.status == ClauseStatus.FAIL


def test_leaf_review_when_fact_missing():
    node = LogicNode(
        type="LEAF",
        condition=Condition(field="annual_turnover", operator=Operator.GTE, value=10_000_000),
    )
    result = evaluate_clause(node, facts=[])
    assert result.status == ClauseStatus.REVIEW


def test_and_rule_gstn_and_pan():
    node = LogicNode(
        type="AND",
        children=[
            LogicNode(type="LEAF", condition=Condition(field="gst_valid", operator=Operator.EQ, value=True)),
            LogicNode(type="LEAF", condition=Condition(field="pan_valid", operator=Operator.EQ, value=True)),
        ],
    )
    facts = [
        Fact(field="gst_valid", value=True, evidence_ref="gst-1"),
        Fact(field="pan_valid", value=False, evidence_ref="pan-1"),
    ]
    result = evaluate_clause(node, facts)
    assert result.status == ClauseStatus.FAIL  # one branch fails -> AND fails


def test_or_rule_turnover_or_similar_projects():
    node = LogicNode(
        type="OR",
        children=[
            LogicNode(type="LEAF", condition=Condition(field="annual_turnover", operator=Operator.GTE, value=10_000_000)),
            LogicNode(type="LEAF", condition=Condition(field="similar_project_count", operator=Operator.GTE, value=2)),
        ],
    )
    facts = [
        Fact(field="annual_turnover", value=2_000_000, evidence_ref="fact-1"),  # fails
        Fact(field="similar_project_count", value=3, evidence_ref="fact-2"),    # passes
    ]
    result = evaluate_clause(node, facts)
    assert result.status == ClauseStatus.PASS  # OR: one branch passing is enough


def test_exception_waives_emd_for_msme():
    node = LogicNode(
        type="LEAF",
        condition=Condition(field="emd_paid", operator=Operator.EQ, value=True),
        exceptions=[Exception_(applies_if=Condition(field="msme_exemption", operator=Operator.EQ, value=True))],
    )
    facts = [
        Fact(field="emd_paid", value=False, evidence_ref="emd-1"),
        Fact(field="msme_exemption", value=True, evidence_ref="msme-1"),
    ]
    result = evaluate_clause(node, facts)
    assert result.status == ClauseStatus.WAIVED  # exemption fires before the base check


def test_unavailable_source_never_becomes_fail():
    node = LogicNode(
        type="LEAF",
        condition=Condition(field="gstin", operator=Operator.EQ, value="22ABCDE1234F1Z5"),
    )
    facts = [
        Fact(
            field="gstin",
            value="22ABCDE1234F1Z5",
            evidence_ref="gstin-1",
            verification_status=VerificationStatus.UNAVAILABLE,
        )
    ]
    result = evaluate_clause(node, facts)
    assert result.status == ClauseStatus.REVIEW  # never auto-FAIL on API downtime


def test_mismatch_source_becomes_fail_not_review():
    node = LogicNode(
        type="LEAF",
        condition=Condition(field="gstin", operator=Operator.EQ, value="22ABCDE1234F1Z5"),
    )
    facts = [
        Fact(
            field="gstin",
            value="22ABCDE1234F1Z5",
            evidence_ref="gstin-1",
            verification_status=VerificationStatus.MISMATCH,
        )
    ]
    result = evaluate_clause(node, facts)
    assert result.status == ClauseStatus.FAIL


def test_low_confidence_fact_forces_review_not_silent_pass():
    node = LogicNode(
        type="LEAF",
        condition=Condition(field="annual_turnover", operator=Operator.GTE, value=10_000_000),
    )
    facts = [
        Fact(field="annual_turnover", value=15_000_000, meets_threshold=False, evidence_ref="fact-1")
    ]
    result = evaluate_clause(node, facts)
    assert result.status == ClauseStatus.REVIEW


def test_hard_gate_mandatory_failure_overrides_high_pass_rate():
    outcomes = [
        (True, ClauseStatus.PASS),
        (True, ClauseStatus.PASS),
        (True, ClauseStatus.PASS),
        (True, ClauseStatus.FAIL),  # one mandatory failure
        (False, ClauseStatus.PASS),
    ]
    assert aggregate_bid_status(outcomes) == "NON_COMPLIANT"


def test_mandatory_review_blocks_auto_compliant():
    outcomes = [
        (True, ClauseStatus.PASS),
        (True, ClauseStatus.REVIEW),
    ]
    assert aggregate_bid_status(outcomes) == "NEEDS_REVIEW"


def test_all_mandatory_pass_gives_compliant():
    outcomes = [
        (True, ClauseStatus.PASS),
        (True, ClauseStatus.WAIVED),
        (False, ClauseStatus.PASS),
    ]
    assert aggregate_bid_status(outcomes) == "COMPLIANT"


def test_nested_and_or_tree():
    # (gst_valid AND pan_valid) AND (turnover>=10cr OR similar_projects>=2)
    node = LogicNode(
        type="AND",
        children=[
            LogicNode(
                type="AND",
                children=[
                    LogicNode(type="LEAF", condition=Condition(field="gst_valid", operator=Operator.EQ, value=True)),
                    LogicNode(type="LEAF", condition=Condition(field="pan_valid", operator=Operator.EQ, value=True)),
                ],
            ),
            LogicNode(
                type="OR",
                children=[
                    LogicNode(type="LEAF", condition=Condition(field="annual_turnover", operator=Operator.GTE, value=10_000_000)),
                    LogicNode(type="LEAF", condition=Condition(field="similar_project_count", operator=Operator.GTE, value=2)),
                ],
            ),
        ],
    )
    facts = [
        Fact(field="gst_valid", value=True, evidence_ref="g1"),
        Fact(field="pan_valid", value=True, evidence_ref="p1"),
        Fact(field="annual_turnover", value=1_000, evidence_ref="t1"),
        Fact(field="similar_project_count", value=5, evidence_ref="s1"),
    ]
    result = evaluate_clause(node, facts)
    assert result.status == ClauseStatus.PASS
