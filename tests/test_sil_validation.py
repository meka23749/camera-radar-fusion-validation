"""End-to-end SiL validation on synthetic scenarios (verification level L2).

These tests verify requirements on the MEASURED behaviour of the system,
not only on the metric code. Three seeds guard against a result that only
holds by luck.
"""

import pytest
from src.test_harness.runner import run

SEEDS = [42, 7, 123]


@pytest.fixture(scope="module")
def reports():
    """Run the system once per seed and share the reports between tests."""
    return {s: run(seed=s, frames=200) for s in SEEDS}


@pytest.mark.requirement("REQ-16")
def test_runner_is_reproducible():
    """Same seed -> identical metrics."""
    a, b = run(seed=1, frames=30), run(seed=1, frames=30)
    assert a["metrics"]["overall_<80m"] == b["metrics"]["overall_<80m"]


@pytest.mark.requirement("REQ-16")
def test_report_contains_all_verdicts(reports):
    assert set(reports[42]["requirements"]) == {"REQ-05", "REQ-08", "REQ-09", "REQ-10"}


@pytest.mark.requirement("REQ-05")
@pytest.mark.parametrize("seed", SEEDS)
def test_far_vehicles_detected_by_fused_system(reports, seed):
    assert reports[seed]["requirements"]["REQ-05"]["verdict"] == "PASS"


@pytest.mark.requirement("REQ-08")
@pytest.mark.parametrize("seed", SEEDS)
def test_recall_vehicles_below_30m(reports, seed):
    assert reports[seed]["requirements"]["REQ-08"]["verdict"] == "PASS"


@pytest.mark.requirement("REQ-09")
@pytest.mark.xfail(strict=True, reason="Known defect: precision ~0.50-0.62, see steps 7-8")
@pytest.mark.parametrize("seed", SEEDS)
def test_precision(reports, seed):
    assert reports[seed]["requirements"]["REQ-09"]["verdict"] == "PASS"


@pytest.mark.requirement("REQ-10")
def test_latency_fusion_stage(reports):
    assert reports[42]["requirements"]["REQ-10"]["verdict"] == "PASS"