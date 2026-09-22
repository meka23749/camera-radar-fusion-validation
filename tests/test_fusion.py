"""Tests for Fusion (src/perception/fusion.py)."""

import pytest
from src.perception.fusion import Fusion
from src.interfaces import DetectedObject, ObstacleList


def _cam(object_class, x, y, conf=0.9, t=1.0):
    """Helper: a camera-style detection."""
    return DetectedObject(object_class=object_class, x=x, y=y,
                          velocity=0.0, confidence=conf, timestamp=t)


def _rad(x, y, vel=-5.0, conf=0.5, t=1.0):
    """Helper: a radar-style detection (class 'unknown')."""
    return DetectedObject(object_class="unknown", x=x, y=y,
                          velocity=vel, confidence=conf, timestamp=t)


@pytest.mark.requirement("REQ-05")
def test_close_camera_and_radar_merge_into_one():
    """A camera and a radar detection at the same spot become ONE object."""
    camera = [_cam("car", x=14.0, y=1.0)]
    radar = [_rad(x=15.0, y=1.0, vel=-8.0)]
    result = Fusion().fuse(camera, radar, timestamp=1.0)
    assert isinstance(result, ObstacleList)
    assert len(result.objects) == 1                 # merged, not duplicated
    obj = result.objects[0]
    assert obj.object_class == "car"                # class from camera
    assert obj.x == 15.0 and obj.velocity == -8.0   # position/velocity from radar


def test_camera_without_radar_is_kept():
    """A camera detection with no nearby radar stays in the output."""
    camera = [_cam("pedestrian", x=8.0, y=-2.0)]
    radar = []
    result = Fusion().fuse(camera, radar, timestamp=1.0)
    assert len(result.objects) == 1
    assert result.objects[0].object_class == "pedestrian"


def test_radar_without_camera_is_kept_as_unknown():
    """A radar detection with no nearby camera stays, class stays 'unknown'."""
    camera = []
    radar = [_rad(x=40.0, y=0.0)]
    result = Fusion().fuse(camera, radar, timestamp=1.0)
    assert len(result.objects) == 1
    assert result.objects[0].object_class == "unknown"


def test_far_camera_and_radar_do_not_merge():
    """A camera and a radar far apart are two separate objects."""
    camera = [_cam("car", x=10.0, y=0.0)]
    radar = [_rad(x=50.0, y=0.0)]
    result = Fusion().fuse(camera, radar, timestamp=1.0)
    assert len(result.objects) == 2                 # not merged: too far apart


def test_output_timestamp_is_set():
    """The output ObstacleList carries the given frame timestamp."""
    result = Fusion().fuse([], [], timestamp=7.0)
    assert result.timestamp == 7.0
    assert result.objects == []