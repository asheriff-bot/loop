"""Tests for Locksmith EvalMetric definition and evaluator."""

from __future__ import annotations

from loop_engine.evaluator import WEIGHTS, LocksmithEvaluator


def test_weights_sum_to_one():
    assert round(sum(WEIGHTS.values()), 6) == 1.0


def test_eval_metric_passes_on_healthy_backend():
    # Skip nested pytest to avoid recursive suite runs during CI of this test.
    result = LocksmithEvaluator(target_score=0.8, run_pytest=False).evaluate()
    assert result.score >= 0.8
    assert result.met_target is True
    names = {c.name for c in result.components}
    assert names == set(WEIGHTS)


def test_eval_report_dict_shape():
    result = LocksmithEvaluator(target_score=1.0, run_pytest=False).evaluate()
    payload = result.to_dict()
    assert "score" in payload and "formula" in payload
    assert payload["formula"].startswith("S =")
