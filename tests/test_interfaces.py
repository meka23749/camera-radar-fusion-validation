"""Tests for the data interfaces (src/interfaces.py)."""

from src.interfaces import (
    CameraImage,
    RadarPoint,
    RadarPoints,
    DetectedObject,
    ObstacleList,
    GroundTruthObject,
)
import numpy as np


def test_detected_object_has_all_fields():
    """A DetectedObject stores class, position, velocity, confidence, timestamp."""
    obj = DetectedObject(
        object_class="car",
        x=12.0,
        y=2.0,
        velocity=-30.0,
        confidence=0.87,
        timestamp=1000.0,
    )
    assert obj.object_class == "car"
    assert obj.x == 12.0
    assert obj.confidence == 0.87


def test_radar_points_groups_multiple_points():
    """A RadarPoints frame holds several RadarPoint echoes."""
    p1 = RadarPoint(x=10.0, y=1.0, velocity=-5.0)
    p2 = RadarPoint(x=25.0, y=0.0, velocity=-12.0)
    frame = RadarPoints(points=[p1, p2], timestamp=1000.0)
    assert len(frame.points) == 2
    assert frame.points[0].x == 10.0


def test_obstacle_list_starts_empty_by_default():
    """An ObstacleList created without arguments has an empty object list."""
    result = ObstacleList()
    assert result.objects == []