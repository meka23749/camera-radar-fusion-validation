"""Tests for the nuScenes loader (src/perception/nuscenes_loader.py).

They run on a tiny hand-made dataset (tests/nuscenes_fixture.py), so they also
run in CI. The last test runs on the real dataset only if NUSCENES_ROOT is set.
"""

import os

import pytest

from src.perception.fusion import SynchronizationError
from src.perception.nuscenes_loader import NuScenesLoader
from tests.nuscenes_fixture import make_dataset, YAW_180


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


@pytest.mark.skipif("NUSCENES_ROOT" not in os.environ, reason="nuScenes data not available")
def test_real_dataset_loads():
    """Smoke test on the real v1.0-mini dataset (runs locally only)."""
    loader = NuScenesLoader(os.environ["NUSCENES_ROOT"])
    assert loader.num_frames() == 404
    frames = [loader.get_frame(i) for i in range(0, 404, 40)]
    assert all(abs(f.sync_offset) <= 0.100 for f in frames)
    assert all(len(f.radar.points) > 0 for f in frames)
    assert all(f.camera_path.exists() for f in frames)