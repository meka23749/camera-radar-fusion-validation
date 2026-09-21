"""Tests for Output (src/perception/output.py)."""

from src.perception.output import Output
from src.interfaces import DetectedObject, ObstacleList


def _obj(confidence, t=1.0):
    """Helper: a detection with a given confidence."""
    return DetectedObject(object_class="car", x=10.0, y=0.0,
                          velocity=-5.0, confidence=confidence, timestamp=t)


def test_low_confidence_objects_are_removed():
    """Detections below the threshold are filtered out."""
    obstacles = ObstacleList(
        objects=[_obj(0.9), _obj(0.1), _obj(0.5)],
        timestamp=1.0,
    )
    result = Output(confidence_threshold=0.3).finalize(obstacles)
    assert len(result.objects) == 2          # 0.9 and 0.5 kept, 0.1 removed


def test_high_confidence_objects_are_kept():
    """A detection exactly at or above the threshold is kept."""
    obstacles = ObstacleList(objects=[_obj(0.3)], timestamp=1.0)
    result = Output(confidence_threshold=0.3).finalize(obstacles)
    assert len(result.objects) == 1          # 0.3 >= 0.3, kept


def test_timestamp_is_preserved():
    """Filtering keeps the original timestamp."""
    obstacles = ObstacleList(objects=[_obj(0.9, t=5.0)], timestamp=5.0)
    result = Output(confidence_threshold=0.3).finalize(obstacles)
    assert result.timestamp == 5.0


def test_empty_list_stays_empty():
    """An empty obstacle list stays empty after filtering."""
    obstacles = ObstacleList(objects=[], timestamp=1.0)
    result = Output().finalize(obstacles)
    assert result.objects == []


def test_input_is_not_modified():
    """finalize returns a new list and does not modify the input."""
    obstacles = ObstacleList(objects=[_obj(0.9), _obj(0.1)], timestamp=1.0)
    Output(confidence_threshold=0.3).finalize(obstacles)
    assert len(obstacles.objects) == 2       # original untouched