"""Fusion: combines camera and radar detections into one obstacle list.

Camera and radar may detect the SAME real object. This block associates
detections that are close in space (same object) and merges them, taking the
class from the camera and the position/velocity from the radar. Unmatched
detections from either sensor are kept as-is.

Association is GLOBALLY optimal (Hungarian algorithm): among all possible
camera-radar pairings, it picks the one with the most matches and the smallest
total distance. Unlike greedy matching, the result does not depend on the
order of the input lists.
"""

import numpy as np
from scipy.optimize import linear_sum_assignment

from src.interfaces import DetectedObject, ObstacleList
from src.geometry import distance

NO_MATCH = 1e9   # cost of a forbidden pairing (farther apart than the gate)


class Fusion:
    """Combines camera and radar detections into a single obstacle list."""

    def __init__(self, distance_threshold: float = 3.0):
        """Create the fusion block.

        Args:
            distance_threshold: max distance (meters) below which a camera and
                a radar detection are considered the same real object.
        """
        self._distance_threshold = distance_threshold

    def _associate(self, camera_detections, radar_detections) -> dict[int, int]:
        """Return {camera index: radar index} for the optimal set of pairs."""
        if not camera_detections or not radar_detections:
            return {}

        # cost[i, j] = distance between camera i and radar j, or NO_MATCH if too far
        cost = np.full((len(camera_detections), len(radar_detections)), NO_MATCH)
        for i, cam in enumerate(camera_detections):
            for j, rad in enumerate(radar_detections):
                d = distance(cam, rad)
                if d < self._distance_threshold:
                    cost[i, j] = d

        rows, cols = linear_sum_assignment(cost)
        return {int(i): int(j) for i, j in zip(rows, cols) if cost[i, j] < NO_MATCH}

    def fuse(
        self,
        camera_detections: list[DetectedObject],
        radar_detections: list[DetectedObject],
        timestamp: float,
    ) -> ObstacleList:
        """Merge camera and radar detections into one ObstacleList.

        Args:
            camera_detections: objects detected by the camera.
            radar_detections: objects detected by the radar.
            timestamp: the frame timestamp for the output list.

        Returns:
            An ObstacleList with the fused obstacles.
        """
        matches = self._associate(camera_detections, radar_detections)
        fused: list[DetectedObject] = []

        for i, cam in enumerate(camera_detections):
            if i in matches:
                # Match found: merge camera class with radar position/velocity
                rad = radar_detections[matches[i]]
                fused.append(
                    DetectedObject(
                        object_class=cam.object_class,   # class from camera
                        x=rad.x,                          # position from radar
                        y=rad.y,
                        velocity=rad.velocity,            # velocity from radar
                        confidence=max(cam.confidence, rad.confidence),
                        timestamp=timestamp,
                    )
                )
            else:
                # No radar match: keep the camera detection as-is
                fused.append(cam)

        used_radar_indices = set(matches.values())
        for j, rad in enumerate(radar_detections):
            if j not in used_radar_indices:
                fused.append(
                    DetectedObject(
                        object_class=rad.object_class,   # stays "unknown"
                        x=rad.x,
                        y=rad.y,
                        velocity=rad.velocity,
                        confidence=rad.confidence,
                        timestamp=timestamp,
                    )
                )

        return ObstacleList(objects=fused, timestamp=timestamp)