"""Fusion: combines camera and radar detections into one obstacle list.

Camera and radar may detect the SAME real object. This block associates
detections that are close in space (same object) and merges them, taking the
class from the camera and the position/velocity from the radar. Unmatched
detections from either sensor are kept as-is.

This is a simple first version: association uses a fixed distance threshold.
"""

from src.interfaces import DetectedObject, ObstacleList
from src.geometry import distance

class Fusion:
    """Combines camera and radar detections into a single obstacle list."""

    def __init__(self, distance_threshold: float = 3.0):
        """Create the fusion block.

        Args:
            distance_threshold: max distance (meters) below which a camera and
                a radar detection are considered the same real object.
        """
        self._distance_threshold = distance_threshold

    def fuse(
        self,
        camera_detections: list[DetectedObject],
        radar_detections: list[DetectedObject],
        timestamp: float,
    ) -> ObstacleList:
        """Merge camera and radar detections into one ObstacleList.

        Camera detections are matched to nearby radar detections. Matched
        pairs are merged (class from camera, position/velocity from radar).
        Unmatched detections from both sensors are kept.

        Args:
            camera_detections: objects detected by the camera.
            radar_detections: objects detected by the radar.
            timestamp: the frame timestamp for the output list.

        Returns:
            An ObstacleList with the fused obstacles.
        """
        fused: list[DetectedObject] = []
        used_radar_indices: set[int] = set()

        # For each camera detection, find the closest radar detection within threshold
        for cam in camera_detections:
            best_index = -1
            best_distance = self._distance_threshold

            for j, rad in enumerate(radar_detections):
                if j in used_radar_indices:
                    continue
                d = distance(cam, rad)
                if d < best_distance:
                    best_distance = d
                    best_index = j

            if best_index >= 0:
                # Match found: merge camera class with radar position/velocity
                rad = radar_detections[best_index]
                used_radar_indices.add(best_index)
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