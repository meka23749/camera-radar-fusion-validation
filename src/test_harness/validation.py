"""Validation: compares system output against ground truth.

For each frame it matches detected obstacles to ground-truth objects by
spatial proximity, counts true positives / false positives / false negatives,
and computes recall (REQ-08) and precision (REQ-09).
"""

from dataclasses import dataclass
from src.interfaces import ObstacleList, GroundTruthObject
from src.geometry import distance

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
    ) -> ValidationResult:
        """Compare detections to ground truth for one frame.

        Args:
            detections: the obstacles produced by the system.
            ground_truth: the true objects (annotations) for the frame.

        Returns:
            A ValidationResult with TP, FP, FN, recall and precision.
        """
        matched_gt_indices = set()
        true_positives = 0

        # Most confident detections claim ground truth first: the result
        # must not depend on the (meaningless) order of the input list.
        for det in sorted(detections.objects, key=lambda d: d.confidence, reverse=True):
            best_index = -1
            best_distance = self._distance_threshold

            for i, gt in enumerate(ground_truth):
                if i in matched_gt_indices or not self._compatible(det, gt):
                    continue
                d = distance(det, gt)
                if d < best_distance:
                    best_distance = d
                    best_index = i

            if best_index >= 0:
                true_positives += 1
                matched_gt_indices.add(best_index)

        # False positives: detections that matched no ground-truth object
        false_positives = len(detections.objects) - true_positives

        # False negatives: ground-truth objects that were never matched
        false_negatives = len(ground_truth) - len(matched_gt_indices)

        # Metrics (guard against division by zero)
        recall = (
            true_positives / (true_positives + false_negatives)
            if (true_positives + false_negatives) > 0
            else 0.0
        )
        precision = (
            true_positives / (true_positives + false_positives)
            if (true_positives + false_positives) > 0
            else 0.0
        )

        false_positives = len(detections.objects) - true_positives
        false_negatives = len(ground_truth) - len(matched_gt_indices)
        return _make_result(true_positives, false_positives, false_negatives)


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