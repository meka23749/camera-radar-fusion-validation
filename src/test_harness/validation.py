"""Validation: compares system output against ground truth.

For each frame it matches detected obstacles to ground-truth objects by
spatial proximity, counts true positives / false positives / false negatives,
and computes recall (REQ-08) and precision (REQ-09).
"""

from dataclasses import dataclass
from src.interfaces import ObstacleList, GroundTruthObject
from src.geometry import distance
import math

UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Metrics computed for one comparison."""
    true_positives: int
    false_positives: int
    false_negatives: int
    recall: float
    precision: float

class Validation:
    """Compares detections against ground truth and computes metrics."""

    def __init__(self, distance_threshold: float = 2.0, class_aware: bool = False):
        """Create the validator.

        Args:
            distance_threshold: max distance (meters) for a detection to count
                as matching a ground-truth object.
            class_aware: if True, a detection with a known class can only match
                a ground-truth object of the same class ("unknown" matches any).
        """
        self._distance_threshold = distance_threshold
        self._class_aware = class_aware

    def _compatible(self, det, gt) -> bool:
        """Can this detection match this ground-truth object?"""
        if not self._class_aware or det.object_class == UNKNOWN:
            return True
        return det.object_class == gt.object_class

    def evaluate(
        self,
        detections: ObstacleList,
        ground_truth: list[GroundTruthObject],
        classes: set[str] | None = None,
        max_range: float | None = None,
    ) -> ValidationResult:
        """Compare detections to ground truth for one frame.

        Args:
            detections: the obstacles produced by the system.
            ground_truth: the true objects (annotations) for the frame.
            classes: if given, only ground-truth objects of these classes are evaluated.
            max_range: if given, only ground-truth objects closer than this (m) are evaluated.
        """
        def in_scope(obj) -> bool:
            if classes is not None and obj.object_class not in classes:
                return False
            return max_range is None or math.hypot(obj.x, obj.y) < max_range

        scoped_gt = [g for g in ground_truth if in_scope(g)]
        out_of_scope_gt = [g for g in ground_truth if not in_scope(g)]

        matched_gt_indices: set[int] = set()
        true_positives = 0
        false_positives = 0

        # Most confident detections claim ground truth first: the result
        # must not depend on the (meaningless) order of the input list.
        for det in sorted(detections.objects, key=lambda d: d.confidence, reverse=True):
            best_index = -1
            best_distance = self._distance_threshold

            for i, gt in enumerate(scoped_gt):
                if i in matched_gt_indices or not self._compatible(det, gt):
                    continue
                d = distance(det, gt)
                if d < best_distance:
                    best_distance = d
                    best_index = i

            if best_index >= 0:
                true_positives += 1
                matched_gt_indices.add(best_index)
            elif self._is_false_positive(det, classes, max_range, out_of_scope_gt):
                false_positives += 1

        false_negatives = len(scoped_gt) - len(matched_gt_indices)
        return _make_result(true_positives, false_positives, false_negatives)

    def _is_false_positive(self, det, classes, max_range, out_of_scope_gt) -> bool:
        """An unmatched detection is a false alarm only if it lies inside the scope
        and does not sit on a real object that is simply outside the scope."""
        if max_range is not None and math.hypot(det.x, det.y) >= max_range:
            return False
        if classes is not None and det.object_class not in classes and det.object_class != UNKNOWN:
            return False
        return all(distance(det, g) >= self._distance_threshold for g in out_of_scope_gt)


def _ratio(num: int, den: int) -> float:
    """Safe division: 0.0 when the denominator is 0."""
    return num / den if den > 0 else 0.0


def _make_result(tp: int, fp: int, fn: int) -> ValidationResult:
    return ValidationResult(
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        recall=_ratio(tp, tp + fn),
        precision=_ratio(tp, tp + fp),
    )


def aggregate(results) -> ValidationResult:
    """Micro-average over frames: sum TP/FP/FN first, THEN compute the ratios.

    Averaging per-frame ratios would give a frame with 1 object the same
    weight as a frame with 30 objects.
    """
    results = list(results)
    return _make_result(
        sum(r.true_positives for r in results),
        sum(r.false_positives for r in results),
        sum(r.false_negatives for r in results),
    )