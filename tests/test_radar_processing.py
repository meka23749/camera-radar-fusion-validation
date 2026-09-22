"""Tests for Radar Processing (src/perception/radar_processing.py)."""

import pytest
from src.perception.radar_processing import RadarProcessing
from src.interfaces import RadarPoint, RadarPoints, DetectedObject


@pytest.mark.requirement("REQ-04")
def test_each_point_becomes_a_detection():
    """Every radar point produces one DetectedObject."""
    radar = RadarPoints(
        points=[
            RadarPoint(x=10.0, y=1.0, velocity=-5.0),
            RadarPoint(x=25.0, y=-2.0, velocity=-12.0),
        ],
        timestamp=4.0,
    )
    result = RadarProcessing().process(radar)
    assert len(result) == 2
    assert all(isinstance(obj, DetectedObject) for obj in result)


def test_position_and_velocity_come_from_the_point():
    """The detection reuses the real position and velocity of the radar point."""
    radar = RadarPoints(
        points=[RadarPoint(x=15.0, y=3.0, velocity=-8.0)],
        timestamp=1.0,
    )
    obj = RadarProcessing().process(radar)[0]
    assert obj.x == 15.0
    assert obj.y == 3.0
    assert obj.velocity == -8.0


def test_class_is_unknown():
    """Radar cannot classify, so the class is 'unknown'."""
    radar = RadarPoints(points=[RadarPoint(x=5.0, y=0.0, velocity=0.0)], timestamp=1.0)
    obj = RadarProcessing().process(radar)[0]
    assert obj.object_class == "unknown"


@pytest.mark.requirement("REQ-12")
def test_detections_carry_frame_timestamp():
    """Detections keep the timestamp of the radar frame (synchronization)."""
    radar = RadarPoints(points=[RadarPoint(x=5.0, y=0.0, velocity=0.0)], timestamp=9.0)
    result = RadarProcessing().process(radar)
    assert all(obj.timestamp == 9.0 for obj in result)


def test_empty_radar_gives_empty_list():
    """No radar points → empty detection list (edge case)."""
    radar = RadarPoints(points=[], timestamp=1.0)
    result = RadarProcessing().process(radar)
    assert result == []