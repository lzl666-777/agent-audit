"""Regression tests for the three ways a broken claim could slip past the audit.

1. a non-numeric constant in a formula made ``consistency`` crash, and the crash
   was reported as a *failed claim* — the audit blamed the data for its own bug;
2. an unbounded ``**`` let one generated formula pin a worker;
3. a claim and a bound in different units (0.348 vs max=8.0) passed silently.
"""

import pytest

from agent_audit import Auditor, AuditIssue, Check, safe_eval


# --------------------------------------------------------------------------- #
# 1. only numbers may appear in a formula
# --------------------------------------------------------------------------- #
def test_rejects_string_constant():
    with pytest.raises(ValueError):
        safe_eval('"abc"', {})
    with pytest.raises(ValueError):
        safe_eval("x + 'a'", {"x": 1})


def test_rejects_boolean_constant():
    # True is an int in Python; a formula should not be able to use it.
    with pytest.raises(ValueError):
        safe_eval("x * True", {"x": 2})


def test_still_accepts_numbers_and_names():
    assert safe_eval("a * (1 - b / c) * 100", {"a": 1, "b": 3, "c": 4}) == 25.0
    assert safe_eval("-2 ** 3", {}) == -8


# --------------------------------------------------------------------------- #
# 2. exponent is bounded
# --------------------------------------------------------------------------- #
def test_rejects_huge_exponent():
    with pytest.raises(ValueError):
        safe_eval("2 ** 10 ** 9", {})


def test_allows_small_exponent():
    assert safe_eval("2 ** 10", {}) == 1024


# --------------------------------------------------------------------------- #
# 3. a check returning something else must not break the report
# --------------------------------------------------------------------------- #
def test_foreign_return_value_becomes_an_error():
    report = Auditor([Check.custom("weird", lambda claims, source: "oops")]).check({})
    assert not report.passed                      # fails closed
    assert isinstance(report.issues[0], AuditIssue)
    assert "expected None/AuditIssue/SKIP" in report.issues[0].message

    # and the report is still usable
    assert report.to_markdown().startswith("## Audit Report")


def test_skip_and_none_still_work():
    report = Auditor([
        Check.custom("skip", lambda claims, source: None),
        Check.threshold("missing", max=1),
    ]).check({})
    assert report.passed and report.checked == 1 and report.skipped == 1


# --------------------------------------------------------------------------- #
# 4. unit mismatch is an error, not a silent pass
# --------------------------------------------------------------------------- #
def test_unit_mismatch_is_flagged():
    # A ratio field (0..1) that receives a percentage from the report.
    report = Auditor([
        Check.threshold("conversion_rate", max=1.0, expect_range=(0, 1)),
    ]).check({"conversion_rate": 34.8})
    assert not report.passed
    assert "different units" in report.errors[0].message


def test_in_range_value_is_compared_normally():
    report = Auditor([
        Check.threshold("return_rate", max=8.0, expect_range=(0, 100)),
    ]).check({"return_rate": 21.82})
    assert not report.passed
    assert "exceeds max" in report.errors[0].message

    report = Auditor([
        Check.threshold("return_rate", max=8.0, expect_range=(0, 100)),
    ]).check({"return_rate": 7.5})
    assert report.passed


def test_expect_range_is_opt_in():
    # Backwards compatible: without expect_range nothing changes.
    report = Auditor([Check.threshold("x", max=10)]).check({"x": 0.5})
    assert report.passed


def test_range_guard_cannot_infer_units_inside_its_own_range():
    """Documented limit: 0.348 and 34.8 are both inside (0, 100).

    The guard catches a value from another *scale*; distinguishing a fraction
    from a percentage inside the same range needs ground truth, which is why
    real audits pass a ``source`` and compare against it.
    """
    report = Auditor([
        Check.threshold("return_rate", max=8.0, expect_range=(0, 100)),
    ]).check({"return_rate": 0.348})
    assert report.passed  # the guard is not a unit converter

