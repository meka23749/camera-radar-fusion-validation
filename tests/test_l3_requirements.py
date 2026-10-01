"""Requirement verification on REAL data (level L3, semi-real).

nuScenes v1.0-mini, VALIDATE scenes (never used for tuning), real radar, real
ground truth, MODELED camera, default system configuration. These tests need
the dataset, so they run locally only (skipped in CI).

Known failures are marked xfail(strict=True): they document what the system does
NOT achieve on real data. If a failure is fixed, the test passes and strict=True
turns that into an error, forcing the marker (and the matrix) to be updated.
"""

import os

import pytest

pytestmark = pytest.mark.skipif("NUSCENES_ROOT" not in os.environ,
                                reason="nuScenes data not available")


@pytest.fixture(scope="module")
def report():
    from src.test_harness.nuscenes_runner import run_nuscenes
    return run_nuscenes(os.environ["NUSCENES_ROOT"], split="validate")


def _verdict(report, req):
    return report["requirements"][req]["verdict"]


@pytest.mark.requirement("REQ-04")
@pytest.mark.xfail(strict=True, reason="INCONCLUSIVE: only 3 vehicles at 120-180 m in v1.0-mini validate")
def test_radar_range(report):
    assert _verdict(report, "REQ-04") == "PASS"


@pytest.mark.requirement("REQ-05")
@pytest.mark.xfail(strict=True, reason="FAIL: 0.21 at 80-180 m; slow far vehicles dropped with the clutter")
def test_system_range(report):
    assert _verdict(report, "REQ-05") == "PASS"


@pytest.mark.requirement("REQ-08")
@pytest.mark.xfail(strict=True, reason="FAIL: 0.78 for vehicles < 30 m (target 0.90)")
def test_recall_near_vehicles(report):
    assert _verdict(report, "REQ-08") == "PASS"


@pytest.mark.requirement("REQ-09")
@pytest.mark.xfail(strict=True, reason="FAIL: precision 0.47 with real radar clutter (target 0.80)")
def test_precision(report):
    assert _verdict(report, "REQ-09") == "PASS"


@pytest.mark.requirement("REQ-10")
def test_latency(report):
    assert _verdict(report, "REQ-10") == "PASS"