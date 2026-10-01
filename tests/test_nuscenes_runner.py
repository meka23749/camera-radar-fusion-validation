"""Tests for the semi-real nuScenes runner (src/test_harness/nuscenes_runner.py)."""

import os

import pytest

from src.test_harness.nuscenes_runner import run_nuscenes, wilson_interval, verdict, to_markdown
from tests.nuscenes_fixture import make_dataset


def test_wilson_interval_known_values():
    """Reference values of the Wilson score interval (z = 1.96)."""
    assert wilson_interval(0, 0) == (0.0, 1.0)                  # no data: anything is possible
    low, high = wilson_interval(10, 15)
    assert (round(low, 3), round(high, 3)) == (0.417, 0.848)
    low, high = wilson_interval(900, 1000)
    assert (round(low, 3), round(high, 3)) == (0.880, 0.917)


def test_verdict_needs_the_whole_interval():
    assert verdict(990, 1000, 0.90) == "PASS"          # interval entirely above 0.90
    assert verdict(500, 1000, 0.90) == "FAIL"          # interval entirely below
    assert verdict(14, 15, 0.90) == "INCONCLUSIVE"     # 0.93 looks good, but n = 15 is too small


def test_runner_on_hand_made_dataset(tmp_path):
    report = run_nuscenes(make_dataset(tmp_path), seed=1)
    m = report["metrics"]
    assert report["config"]["frames"] == 2
    # vehicles evaluated in the fixture: car at 30 m and bus at 40 m (sample 1), car at 50 m (sample 2)
    assert m["radar_only_recall_vehicles"]["30-80 m"]["n"] == 3
    assert m["recall_vehicles_80-180m_fused"]["n"] == 0
    assert set(report["requirements"]) == {"REQ-04", "REQ-05", "REQ-08", "REQ-09", "REQ-10"}
    assert "MODELED" in to_markdown(report)

def test_chance_level_is_reported(tmp_path):
    """Frame 1 is compared with the ground truth of frame 2 and vice versa.

    Frame 1's radar point (24.5 m) is far from frame 2's car (50 m), and frame 2
    has no radar point: chance recall is 0 out of 3 vehicles.
    """
    band = run_nuscenes(make_dataset(tmp_path), seed=1)["metrics"]["radar_only_recall_vehicles"]["30-80 m"]
    assert (band["chance"]["k"], band["chance"]["n"]) == (0, 3)


def test_one_match_threshold_for_every_range(tmp_path):
    report = run_nuscenes(make_dataset(tmp_path), seed=1)
    assert report["config"]["match_threshold_m"] == 2.0

def test_runner_is_reproducible(tmp_path):
    root = make_dataset(tmp_path)
    a, b = run_nuscenes(root, seed=3), run_nuscenes(root, seed=3)
    assert a["metrics"]["precision_overall"] == b["metrics"]["precision_overall"]


@pytest.mark.skipif("NUSCENES_ROOT" not in os.environ, reason="nuScenes data not available")
def test_runner_on_real_data():
    report = run_nuscenes(os.environ["NUSCENES_ROOT"], max_frames=20)
    assert report["metrics"]["recall_overall"]["n"] > 0

def test_scene_split_alternates_sorted_names(tmp_path):
    from src.test_harness.nuscenes_runner import scene_split
    split = scene_split(make_dataset(tmp_path))
    assert split == {"all": ["scene-0001"], "tune": ["scene-0001"], "validate": []}


def test_empty_split_is_an_error(tmp_path):
    """An empty run would report nothing wrong: it must fail loudly instead."""
    with pytest.raises(ValueError, match="no frames"):
        run_nuscenes(make_dataset(tmp_path), split="validate")