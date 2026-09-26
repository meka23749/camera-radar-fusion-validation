"""Tests for Validation (src/test_harness/validation.py)."""

import pytest
from src.test_harness.validation import Validation, ValidationResult
from src.interfaces import DetectedObject, ObstacleList, GroundTruthObject
from src.test_harness.validation import aggregate


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

@pytest.mark.requirement("REQ-06")
def test_class_aware_matching_rejects_wrong_class():
    """A pedestrian detected on a car is not a correct detection."""
    ped = DetectedObject("pedestrian", 10.0, 0.0, 0.0, 0.9, 1.0)
    res = Validation(class_aware=True).evaluate(ObstacleList([ped], 1.0), [_gt(10.0, 0.0)])
    assert res.true_positives == 0 and res.false_negatives == 1


def test_unknown_radar_object_matches_any_class():
    """A radar-only object ('unknown') still counts as a detected obstacle."""
    radar_obj = DetectedObject("unknown", 10.0, 0.0, 0.0, 0.5, 1.0)
    res = Validation(class_aware=True).evaluate(ObstacleList([radar_obj], 1.0), [_gt(10.0, 0.0)])
    assert res.true_positives == 1

def test_result_does_not_depend_on_detection_order():
    """Same detections in another order give the same metrics."""
    v = Validation(distance_threshold=3.0)
    low = DetectedObject("car", 11.8, 0.0, 0.0, 0.2, 1.0)
    high = DetectedObject("car", 10.3, 0.0, 0.0, 0.9, 1.0)
    truth = [_gt(10.0, 0.0), _gt(14.0, 0.0)]
    a = v.evaluate(ObstacleList([low, high], 1.0), truth)
    b = v.evaluate(ObstacleList([high, low], 1.0), truth)
    assert a == b


def test_aggregate_is_micro_average():
    """1 found out of 1, then 0 found out of 3 -> recall 1/4, not mean(1.0, 0.0)."""
    f1 = Validation().evaluate(ObstacleList([_det(10.0, 0.0)], 1.0), [_gt(10.0, 0.0)])
    f2 = Validation().evaluate(ObstacleList([], 1.0),
                               [_gt(10.0, 0.0), _gt(20.0, 0.0), _gt(30.0, 0.0)])
    assert aggregate([f1, f2]).recall == 0.25