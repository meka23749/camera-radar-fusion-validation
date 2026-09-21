"""Radar Processing: turns raw radar points into detected objects.

For now this is a STUB: each radar point becomes one DetectedObject, using
the point's real position and velocity, with class "unknown" (radar cannot
classify objects on its own). Real clustering/filtering will come later,
without changing this block's interface.
"""

from src.interfaces import RadarPoints, DetectedObject

class RadarProcessing:
    """Extracts detected objects from raw radar points.

    Input:  a RadarPoints frame (raw echoes).
    Output: a list of DetectedObject (may be empty).
    """

    def process(self, radar: RadarPoints) -> list[DetectedObject]:
        """Convert radar points into detected objects.

        Position and velocity come from the real radar points. The class is
        set to "unknown" because radar alone cannot classify objects; the
        detections keep the timestamp of the input frame (synchronization).

        Args:
            radar: the radar frame to process.

        Returns:
            A list of DetectedObject. Empty if there are no points.
        """
        detections = []
        for point in radar.points:
            obj = DetectedObject(
                object_class="unknown",
                x=point.x,
                y=point.y,
                velocity=point.velocity,
                confidence=0.5,
                timestamp=radar.timestamp,
            )
            detections.append(obj)
        return detections