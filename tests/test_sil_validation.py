"""Regression tests of the fusion logic on synthetic scenarios.

They run the synthetic bench with SYNTHETIC_REFERENCE_FUSION (the configuration
tuned on the synthetic sensor models) and check that its verdicts do not change.
They are NOT evidence for the requirements: the synthetic sensor models are not
calibrated against real sensors (docs/08_Real_Data_Results.md). Requirement
evidence comes from tests/test_l3_requirements.py (real nuScenes data).
Only the reproducibility tests (REQ-16) are about the bench itself.
"""

import pytest
import json
import os
import subprocess
import sys
from pathlib import Path
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


@pytest.mark.parametrize("seed", SEEDS)
def test_far_vehicles_detected_by_fused_system(reports, seed):
    assert reports[seed]["requirements"]["REQ-05"]["verdict"] == "PASS"


@pytest.mark.parametrize("seed", SEEDS)
def test_recall_vehicles_below_30m(reports, seed):
    assert reports[seed]["requirements"]["REQ-08"]["verdict"] == "PASS"


@pytest.mark.parametrize("seed", SEEDS)
def test_precision(reports, seed):
    assert reports[seed]["requirements"]["REQ-09"]["verdict"] == "PASS"


def test_latency_fusion_stage(reports):
    assert reports[42]["requirements"]["REQ-10"]["verdict"] == "PASS"

def _metrics_in_fresh_process(hash_seed: str) -> dict:
    """Run the runner in a NEW Python process with a given hash seed."""
    code = ("import json; from src.test_harness.runner import run; "
            "print(json.dumps(run(seed=42, frames=300)['metrics']['overall_<80m']))")
    env = {**os.environ, "PYTHONHASHSEED": hash_seed}
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                         text=True, check=True, cwd=Path(__file__).resolve().parents[1])
    return json.loads(out.stdout)


@pytest.mark.requirement("REQ-16")
def test_runner_is_reproducible_across_processes():
    """Same seed -> identical metrics, even in separate Python processes.

    Python randomizes the iteration order of sets of strings in every new
    process (PYTHONHASHSEED). A test that runs twice in the SAME process
    cannot detect that; this one can.
    """
    assert _metrics_in_fresh_process("0") == _metrics_in_fresh_process("2")