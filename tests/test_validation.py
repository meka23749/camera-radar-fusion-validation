"""Tests for Validation (src/test_harness/validation.py)."""

import pytest
from src.test_harness.validation import Validation, ValidationResult
from src.interfaces import DetectedObject, ObstacleList, GroundTruthObject


def _det(x, y, t=1.0):
    """Helper: a system detection at (x, y)."""
    return DetectedObject(object_class="car", x=x, y=y,
                          velocity=0.0, confidence=0.9, timestamp=t)


def _gt(x, y, t=1.0):
    """Helper: a ground-truth object at (x, y)."""
    return GroundTruthObject(object_class="car", x=x, y=y,
                             velocity=0.0, timestamp=t)


def test_perfect_detection():
    """One detection exactly on one ground-truth object: recall=1, precision=1."""
    detections = ObstacleList(objects=[_det(10.0, 0.0)], timestamp=1.0)
    ground_truth = [_gt(10.0, 0.0)]
    result = Validation().evaluate(detections, ground_truth)
    assert result.true_positives == 1
    assert result.false_positives == 0
    assert result.false_negatives == 0
    assert result.recall == 1.0
    assert result.precision == 1.0


@pytest.mark.requirement("REQ-08")
def test_missed_object_lowers_recall():
    """Two real objects, system detects only one: recall = 0.5."""
    detections = ObstacleList(objects=[_det(10.0, 0.0)], timestamp=1.0)
    ground_truth = [_gt(10.0, 0.0), _gt(30.0, 0.0)]   # second one missed
    result = Validation().evaluate(detections, ground_truth)
    assert result.true_positives == 1
    assert result.false_negatives == 1
    assert result.recall == 0.5
    assert result.precision == 1.0


@pytest.mark.requirement("REQ-09")
def test_invented_object_lowers_precision():
    """One real object, system reports two: one is a false positive."""
    detections = ObstacleList(
        objects=[_det(10.0, 0.0), _det(50.0, 0.0)],   # second one invented
        timestamp=1.0,
    )
    ground_truth = [_gt(10.0, 0.0)]
    result = Validation().evaluate(detections, ground_truth)
    assert result.true_positives == 1
    assert result.false_positives == 1
    assert result.precision == 0.5
    assert result.recall == 1.0


def test_far_detection_does_not_match():
    """A detection far from any ground truth is a false positive, not a match."""
    detections = ObstacleList(objects=[_det(10.0, 0.0)], timestamp=1.0)
    ground_truth = [_gt(40.0, 0.0)]   # too far to match
    result = Validation().evaluate(detections, ground_truth)
    assert result.true_positives == 0
    assert result.false_positives == 1
    assert result.false_negatives == 1
    assert result.recall == 0.0
    assert result.precision == 0.0


def test_empty_everything_gives_zero_metrics():
    """No detections and no ground truth: metrics default to 0.0 (no crash)."""
    detections = ObstacleList(objects=[], timestamp=1.0)
    result = Validation().evaluate(detections, [])
    assert result.recall == 0.0
    assert result.precision == 0.0