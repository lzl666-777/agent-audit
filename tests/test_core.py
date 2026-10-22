import pytest

from agent_audit import Auditor, Check, SKIP, safe_eval


# --------------------------------------------------------------------------- #
# threshold
# --------------------------------------------------------------------------- #

def test_threshold_pass():
    report = Auditor([Check.threshold("x", max=1)]).check({"x": 0.5})
    assert report.passed
    assert report.issues == []
    assert report.checked == 1


def test_threshold_fail():
    report = Auditor([Check.threshold("x", max=1)]).check({"x": 2})
    assert not report.passed
    assert len(report.errors) == 1
    assert report.errors[0].field == "x"


def test_threshold_min():
    report = Auditor([Check.threshold("margin", min=0.30)]).check({"margin": 0.28})
    assert not report.passed


def test_threshold_skip_when_missing():
    report = Auditor([Check.threshold("x", max=1)]).check({})
    assert report.skipped == 1
    assert report.checked == 0


# --------------------------------------------------------------------------- #
# consistency
# --------------------------------------------------------------------------- #

def test_consistency_ok():
    report = Auditor([Check.consistency("revenue", "price * qty")]).check(
        {"revenue": 100, "price": 10, "qty": 10}
    )
    assert report.passed


def test_consistency_fail():
    # 80 vs 10*10=100 -> 20% off, well outside the default 1% tolerance
    report = Auditor([Check.consistency("revenue", "price * qty")]).check(
        {"revenue": 80, "price": 10, "qty": 10}
    )
    assert not report.passed
    assert report.errors[0].expected == 100


def test_consistency_uses_source_for_missing_components():
    report = Auditor([Check.consistency("revenue", "price * qty")]).check(
        {"revenue": 100}, source={"price": 10, "qty": 10}
    )
    assert report.passed


def test_consistency_skips_without_components():
    report = Auditor([Check.consistency("revenue", "price * qty")]).check({"revenue": 100})
    assert report.skipped == 1


def test_consistency_tolerance():
    # 100.5 vs 100 -> 0.5% off, inside the default 1% tolerance
    report = Auditor([Check.consistency("v", "x * 1", tolerance=0.01)]).check(
        {"v": 100.5, "x": 100}
    )
    assert report.passed


# --------------------------------------------------------------------------- #
# freshness
# --------------------------------------------------------------------------- #

def test_freshness_warns_but_passes():
    report = Auditor([Check.freshness("ts", max_age_days=30)]).check({"ts": "2020-01-01"})
    assert report.passed  # warning only
    assert len(report.warnings) == 1


def test_freshness_ok():
    from datetime import datetime, timezone

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    report = Auditor([Check.freshness("ts", max_age_days=30, now=now)]).check(
        {"ts": "2025-12-20"}
    )
    assert report.passed
    assert report.warnings == []


# --------------------------------------------------------------------------- #
# custom + report
# --------------------------------------------------------------------------- #

def test_custom_check():
    def no_negative_claims(claims, source):
        if claims.get("qty", 0) < 0:
            from agent_audit import AuditIssue

            return AuditIssue("custom", "qty", "quantity is negative")
        return None

    report = Auditor([Check.custom("no_negative", no_negative_claims)]).check({"qty": -1})
    assert not report.passed


def test_report_markdown_contains_status():
    report = Auditor([Check.threshold("x", max=1)]).check({"x": 2})
    md = report.to_markdown()
    assert "FAIL" in md and "threshold(x)" in md
    assert "| x |" in md


def test_broken_check_does_not_crash():
    def boom(claims, source):
        raise RuntimeError("boom")

    report = Auditor([Check.custom("boom", boom)]).check({})
    assert not report.passed
    assert "crashed" in report.errors[0].message


# --------------------------------------------------------------------------- #
# safe_eval
# --------------------------------------------------------------------------- #

def test_safe_eval_basic():
    assert safe_eval("a + b * 2", {"a": 1, "b": 3}) == 7


def test_safe_eval_rejects_calls():
    with pytest.raises(Exception):
        safe_eval("__import__('os').system('echo hi')", {})


def test_safe_eval_rejects_attributes():
    with pytest.raises(Exception):
        safe_eval("a.__class__", {"a": 1})


def test_skip_sentinel_exists():
    assert repr(SKIP) == "SKIP"
