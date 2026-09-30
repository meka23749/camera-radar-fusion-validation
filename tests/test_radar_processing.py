"""Tests for Radar Processing (src/perception/radar_processing.py)."""

import pytest
from src.perception.radar_processing import RadarProcessing
from src.interfaces import RadarPoint, RadarPoints, DetectedObject


# Not tagged REQ-04: the radar RANGE is a sensor property; it needs real radar data.
def test_distant_points_become_separate_detections():
    """Two echoes far apart come from two different objects."""
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

def test_echoes_of_one_object_are_clustered():
    """Several echoes from the same car become ONE detection at their mean position."""
    radar = RadarPoints(
        points=[
            RadarPoint(x=20.0, y=1.0, velocity=-5.0),
            RadarPoint(x=20.5, y=1.8, velocity=-5.2),
            RadarPoint(x=21.0, y=0.6, velocity=-4.8),
        ],
        timestamp=1.0,
    )
    result = RadarProcessing().process(radar)
    assert len(result) == 1
    assert abs(result[0].x - 20.5) < 1e-9
    assert abs(result[0].velocity - (-5.0)) < 1e-9


def test_more_echoes_give_more_confidence():
    """A 3-echo cluster is more trustworthy than a single isolated echo."""
    single = RadarPoints(points=[RadarPoint(x=20.0, y=1.0, velocity=-5.0)], timestamp=1.0)
    triple = RadarPoints(
        points=[
            RadarPoint(x=20.0, y=1.0, velocity=-5.0),
            RadarPoint(x=20.5, y=1.8, velocity=-5.2),
            RadarPoint(x=21.0, y=0.6, velocity=-4.8),
        ],
        timestamp=1.0,
    )
    c1 = RadarProcessing().process(single)[0].confidence
    c3 = RadarProcessing().process(triple)[0].confidence
    assert c3 > c1