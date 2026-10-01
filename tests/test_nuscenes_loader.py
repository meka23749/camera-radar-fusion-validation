"""Tests for the nuScenes loader (src/perception/nuscenes_loader.py).

They run on a tiny hand-made dataset (tests/nuscenes_fixture.py), so they also
run in CI. The last test runs on the real dataset only if NUSCENES_ROOT is set.
"""

import os

import numpy as np
import pytest

from src.perception.fusion import SynchronizationError
from src.perception.nuscenes_loader import NuScenesLoader
from tests.nuscenes_fixture import make_dataset, write_radar_pcd, RADAR_DTYPE, YAW_180


@pytest.mark.requirement("REQ-11")
def test_frames_follow_the_scene_order(tmp_path):
    """Samples are stored in reverse order in the file; frames are chronological."""
    loader = NuScenesLoader(make_dataset(tmp_path))
    assert loader.num_frames() == 2
    assert [loader.get_frame(i).sample_token for i in range(2)] == ["s1", "s2"]


def test_frame_uses_camera_timestamp_and_keyframes_only(tmp_path):
    frame = NuScenesLoader(make_dataset(tmp_path)).get_frame(0)
    assert frame.timestamp == pytest.approx(0.98)
    assert frame.radar.timestamp == frame.timestamp      # compensated to camera time
    assert frame.sync_offset == pytest.approx(0.020)
    assert frame.camera_path == tmp_path / "samples/CAM_FRONT/cam1.jpg"
    assert len(frame.radar.points) == 1                  # the sweep is ignored


def test_radar_mounting_is_applied(tmp_path):
    """No ego motion: point 20 m ahead of the sensor = 23.5 m ahead of the vehicle."""
    frame = NuScenesLoader(make_dataset(tmp_path, ego_shift=0.0)).get_frame(0)
    p = frame.radar.points[0]
    assert (p.x, p.y) == pytest.approx((23.5, 0.0))


def test_ego_motion_is_compensated(tmp_path):
    """The vehicle drove 1 m between camera and radar: at camera time the point is 24.5 m ahead."""
    frame = NuScenesLoader(make_dataset(tmp_path, ego_shift=1.0)).get_frame(0)
    assert frame.radar.points[0].x == pytest.approx(24.5)


def test_velocity_is_rotated_into_the_vehicle_frame(tmp_path):
    """A radar mounted backwards: +5 m/s in the sensor frame is -5 m/s for the vehicle."""
    frame = NuScenesLoader(make_dataset(tmp_path, ego_shift=0.0,
                                        radar_rotation=YAW_180)).get_frame(0)
    p = frame.radar.points[0]
    assert (p.x, p.velocity) == pytest.approx((3.5 - 20.0, -5.0))


@pytest.mark.requirement("REQ-12")
def test_measurements_too_far_apart_are_rejected(tmp_path):
    """Camera and radar 120 ms apart belong to different cycles (REQ-12: max 100 ms)."""
    loader = NuScenesLoader(make_dataset(tmp_path, radar_offset_us=120_000))
    with pytest.raises(SynchronizationError):
        loader.get_frame(0)


@pytest.mark.requirement("REQ-11")
@pytest.mark.skipif("NUSCENES_ROOT" not in os.environ, reason="nuScenes data not available")
def test_real_dataset_loads():
    """Smoke test on the real v1.0-mini dataset (runs locally only)."""
    loader = NuScenesLoader(os.environ["NUSCENES_ROOT"])
    assert loader.num_frames() == 404
    frames = [loader.get_frame(i) for i in range(0, 404, 40)]
    assert all(abs(f.sync_offset) <= 0.100 for f in frames)
    assert all(len(f.radar.points) > 0 for f in frames)
    assert all(f.camera_path.exists() for f in frames)

def _radar_points_with_states(states):
    """One radar point per (invalid_state, ambig_state, dyn_prop) triple, 20 m ahead."""
    points = np.zeros(len(states), dtype=RADAR_DTYPE)
    points["x"] = 20.0
    points["y"] = np.arange(len(states)) * 3.0           # spread out laterally
    for field_name, column in zip(("invalid_state", "ambig_state", "dyn_prop"), zip(*states)):
        points[field_name] = column
    return points


@pytest.mark.parametrize("radar_filter, expected_points", [
    ("none", 5),      # everything
    ("valid", 4),     # drops the point the radar declares invalid (outside its FOV)
    ("devkit", 1),    # also drops low RCS, ambiguous and "stopped" points
])
def test_radar_filters(tmp_path, radar_filter, expected_points):
    root = make_dataset(tmp_path)
    write_radar_pcd(root / "samples/RADAR_FRONT/rad1.pcd", _radar_points_with_states([
        (0, 3, 1),        # valid, unambiguous, stationary   -> kept by every filter
        (4, 3, 1),        # valid but low RCS                -> dropped by devkit
        (7, 3, 0),        # INVALID: outside sensor FOV      -> dropped by valid and devkit
        (0, 3, 7),        # valid, "stopped"                 -> dropped by devkit
        (0, 0, 1),        # valid, Doppler ambiguity invalid -> dropped by devkit
    ]))
    frame = NuScenesLoader(root, radar_filter=radar_filter).get_frame(0)
    assert len(frame.radar.points) == expected_points

def test_scenes_can_be_selected(tmp_path):
    root = make_dataset(tmp_path)
    assert NuScenesLoader(root, scenes=["scene-0001"]).num_frames() == 2
    assert NuScenesLoader(root, scenes=[]).num_frames() == 0


def test_unknown_scene_is_rejected(tmp_path):
    """A typo in a scene name must not silently give an empty (and 'perfect') run."""
    with pytest.raises(ValueError, match="scene-9999"):
        NuScenesLoader(make_dataset(tmp_path), scenes=["scene-9999"])