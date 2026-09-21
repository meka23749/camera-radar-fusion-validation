"""Shared geometry helpers used across perception blocks."""

import math
from src.interfaces import DetectedObject


def distance(a: DetectedObject, b: DetectedObject) -> float:
    """Euclidean distance between two detections in the (x, y) plane."""
    return math.hypot(a.x - b.x, a.y - b.y)