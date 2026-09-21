"""Output: finalizes the system output by filtering low-confidence obstacles.

Detections below a confidence threshold are removed to limit false positives
(REQ-09), while keeping the threshold low to preserve recall (safety priority).
The threshold is a tunable parameter.
"""

from src.interfaces import ObstacleList

class Output:
    """Filters an ObstacleList, keeping only confident-enough detections."""

    def __init__(self, confidence_threshold: float = 0.3):
        """Create the output block.

        Args:
            confidence_threshold: minimum confidence to keep a detection.
                Kept low to preserve recall (safety priority).
        """
        self._confidence_threshold = confidence_threshold

    def finalize(self, obstacles: ObstacleList) -> ObstacleList:
        """Return a new ObstacleList without low-confidence detections.

        Args:
            obstacles: the fused obstacle list.

        Returns:
            A new ObstacleList keeping only objects with
            confidence >= confidence_threshold. Timestamp is preserved.
        """
        kept = [
            obj for obj in obstacles.objects
            if obj.confidence >= self._confidence_threshold
        ]
        return ObstacleList(objects=kept, timestamp=obstacles.timestamp)