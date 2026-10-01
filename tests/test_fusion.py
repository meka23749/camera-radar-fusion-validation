"""Tests for Fusion (src/perception/fusion.py)."""

import math

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

def test_association_is_globally_optimal_not_greedy():
    """Greedy matching would leave one camera object unmatched here; optimal matches both."""
    camera = [_cam("car", x=10.0, y=0.0), _cam("car", x=12.0, y=0.0)]
    radar = [_rad(x=11.8, y=0.0), _rad(x=8.0, y=0.0)]
    result = Fusion(distance_threshold=3.0).fuse(camera, radar, timestamp=1.0)
    assert len(result.objects) == 2
    assert all(o.object_class == "car" for o in result.objects)


def test_result_does_not_depend_on_input_order():
    """Same detections in another order give the same fused objects."""
    camera = [_cam("car", 10.0, 0.0), _cam("truck", 12.0, 0.0)]
    radar = [_rad(11.8, 0.0), _rad(8.0, 0.0)]
    a = Fusion().fuse(camera, radar, 1.0).objects
    b = Fusion().fuse(camera[::-1], radar[::-1], 1.0).objects
    key = lambda o: (o.object_class, o.x)
    assert sorted(map(key, a)) == sorted(map(key, b))

def test_range_dependent_gate_merges_far_objects():
    """At 60 m the camera depth error is several meters: a fixed 3 m gate misses the pair."""
    camera, radar = [_cam("car", 60.0, 0.0)], [_rad(64.0, 0.0)]
    assert len(Fusion(3.0, gate_per_meter=0.0).fuse(camera, radar, 1.0).objects) == 2
    assert len(Fusion(3.0, gate_per_meter=0.08).fuse(camera, radar, 1.0).objects) == 1

@pytest.mark.requirement("REQ-12")
def test_detections_from_another_frame_are_rejected():
    """Fusing a detection from another frame is a synchronization error (REQ-12)."""
    from src.perception.fusion import SynchronizationError
    with pytest.raises(SynchronizationError):
        Fusion().fuse([_cam("car", 10.0, 0.0, t=2.0)], [], timestamp=1.0)


def test_small_timestamp_offset_is_accepted():
    """Camera and radar are never sampled at exactly the same instant: 20 ms is fine."""
    result = Fusion().fuse([_cam("car", 10.0, 0.0, t=1.02)], [], timestamp=1.0)
    assert len(result.objects) == 1

def test_unconfirmed_static_radar_object_is_dropped():
    """With a minimum speed, a static radar object that no camera confirms is removed."""
    static, moving = _rad(40.0, 5.0, vel=0.2), _rad(60.0, -5.0, vel=-8.0)
    result = Fusion(radar_only_min_speed=1.0).fuse([], [static, moving], 1.0)
    assert [o.x for o in result.objects] == [60.0]


def test_confirmed_static_radar_object_is_kept():
    """A parked car seen by the camera AND the radar is fused, even if it does not move."""
    parked = _rad(20.5, 0.0, vel=0.0)
    result = Fusion(radar_only_min_speed=1.0).fuse([_cam("car", 20.0, 0.0)], [parked], 1.0)
    assert [(o.object_class, o.x) for o in result.objects] == [("car", 20.5)]


def test_without_minimum_speed_every_radar_object_is_kept():
    static = _rad(40.0, 5.0, vel=0.0)
    assert len(Fusion(radar_only_min_speed=None).fuse([], [static], 1.0).objects) == 1

def test_elliptical_gate_rejects_clutter_beside_the_object():
    """A radar cluster 2.5 m BESIDE the car (e.g. a guard rail) is not the car."""
    camera, radar = [_cam("car", 20.0, 0.0)], [_rad(20.0, 2.5)]
    assert len(Fusion(gate_per_meter=0.0, lateral_gate=None)
               .fuse(camera, radar, 1.0).objects) == 1                                 # circle: merged     # circle: merged
    assert len(Fusion(gate_per_meter=0.0, lateral_gate=1.0)
               .fuse(camera, radar, 1.0).objects) == 2                                 # ellipse: kept apart


def test_elliptical_gate_accepts_depth_error():
    """The camera misjudged the depth by 2.5 m: same bearing, so the radar is the car."""
    result = Fusion(gate_per_meter=0.0, lateral_gate=1.0).fuse(
        [_cam("car", 20.0, 0.0)], [_rad(22.5, 0.0)], 1.0)
    assert [(o.object_class, o.x) for o in result.objects] == [("car", 22.5)]


def test_elliptical_gate_follows_the_line_of_sight():
    """For an object at 45 deg, 'depth' is along the diagonal, not along x."""
    s = 2.0 / math.sqrt(2.0)
    along = Fusion(gate_per_meter=0.0, lateral_gate=1.0).fuse(
        [_cam("car", 30.0, 30.0)], [_rad(30.0 + s, 30.0 + s)], 1.0)
    across = Fusion(gate_per_meter=0.0, lateral_gate=1.0).fuse(
        [_cam("car", 30.0, 30.0)], [_rad(30.0 - s, 30.0 + s)], 1.0)
    assert len(along.objects) == 1 and len(across.objects) == 2


def test_elliptical_cost_prefers_the_radar_on_the_line_of_sight():
    """2.5 m deeper (0.83 of the depth gate) beats 0.9 m aside (0.90 of the lateral gate)."""
    result = Fusion(gate_per_meter=0.0, lateral_gate=1.0).fuse(
        [_cam("car", 20.0, 0.0)], [_rad(22.5, 0.0), _rad(20.0, 0.9)], 1.0)
    car = next(o for o in result.objects if o.object_class == "car")
    assert (car.x, car.y) == (22.5, 0.0)

