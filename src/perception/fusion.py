"""Fusion: combines camera and radar detections into one obstacle list.

Camera and radar may detect the SAME real object. This block associates
detections that are close in space (same object) and merges them, taking the
class from the camera and the position/velocity from the radar. Unmatched
detections from either sensor are kept as-is.

Association is GLOBALLY optimal (Hungarian algorithm): among all possible
camera-radar pairings, it picks the one with the most matches and the smallest
total distance. Unlike greedy matching, the result does not depend on the
order of the input lists.

The association gate grows with range: the camera estimates depth from a
single image, so its distance error grows with distance (~5 % of range).
A fixed gate would fail to merge far camera and radar detections of the
same object, creating one duplicate (false positive) per missed merge.
"""

import math

import numpy as np
from scipy.optimize import linear_sum_assignment

from src.interfaces import DetectedObject, ObstacleList
from src.geometry import distance

NO_MATCH = 1e9   # cost of a forbidden pairing (farther apart than the gate)


class SynchronizationError(ValueError):
    """Raised when detections from different frames are passed to fusion (REQ-12)."""

class Fusion:
    """Combines camera and radar detections into a single obstacle list."""

    def __init__(
        self,
        distance_threshold: float = 3.0,
        gate_per_meter: float = 0.08,
        max_time_offset: float = 0.05,
        radar_only_min_speed: float | None = None,
        lateral_gate: float | None = None,
    ):
        """Create the fusion block.

        Args:
            distance_threshold: base association gate (meters).
            gate_per_meter: extra gate per meter of range
                (0.08 -> gate of 3 + 0.08 * 50 = 7 m at 50 m). 0.0 = fixed gate.
            max_time_offset: max allowed |detection timestamp - frame timestamp| (s).
            radar_only_min_speed: if set, a radar detection that NO camera detection
                confirms is kept only if it moves at least this fast (m/s, over ground).
                Real radar clutter (guard rails, poles, walls) is static.
            lateral_gate: if set, the gate becomes an ELLIPSE around the camera detection:
                along the line of sight its half-length is the range gate above (camera
                depth is uncertain), across it is lateral_gate metres (camera bearing is
                precise). None = circular gate.
        """
        self._distance_threshold = distance_threshold
        self._gate_per_meter = gate_per_meter
        self._max_time_offset = max_time_offset
        self._radar_only_min_speed = radar_only_min_speed
        self._lateral_gate = lateral_gate

    def _check_sync(self, detections, timestamp: float) -> None:
        """Refuse detections that do not belong to this frame (REQ-12)."""
        for d in detections:
            if abs(d.timestamp - timestamp) > self._max_time_offset:
                raise SynchronizationError(
                    f"Detection at t={d.timestamp} passed to frame t={timestamp} "
                    f"(max offset {self._max_time_offset} s)"
                )

    def _gate(self, cam: DetectedObject) -> float:
        """Association gate for this camera detection: grows with its range."""
        return self._distance_threshold + self._gate_per_meter * math.hypot(cam.x, cam.y)

    def _gate_cost(self, cam: DetectedObject, rad: DetectedObject) -> float | None:
        """Cost of pairing cam with rad, or None if rad is outside the gate.

        Circular gate: cost = distance in metres.
        Elliptical gate: the offset is split into a component ALONG the camera's
        line of sight (depth, poorly known) and one ACROSS it (bearing, well
        known); cost = normalized distance, 1.0 on the edge of the ellipse.
        """
        depth_gate = self._gate(cam)
        if self._lateral_gate is None:
            d = distance(cam, rad)
            return d if d < depth_gate else None

        r = math.hypot(cam.x, cam.y)
        ux, uy = (cam.x / r, cam.y / r) if r > 1e-6 else (1.0, 0.0)   # line of sight
        dx, dy = rad.x - cam.x, rad.y - cam.y
        along = dx * ux + dy * uy
        across = -dx * uy + dy * ux
        cost = math.hypot(along / depth_gate, across / self._lateral_gate)
        return cost if cost < 1.0 else None

    def _associate(self, camera_detections, radar_detections) -> dict[int, int]:
        """Return {camera index: radar index} for the optimal set of pairs."""
        if not camera_detections or not radar_detections:
            return {}

        # cost[i, j] = gate cost of camera i with radar j, or NO_MATCH if outside the gate
        cost = np.full((len(camera_detections), len(radar_detections)), NO_MATCH)
        for i, cam in enumerate(camera_detections):
            for j, rad in enumerate(radar_detections):
                c = self._gate_cost(cam, rad)
                if c is not None:
                    cost[i, j] = c

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
        self._check_sync(camera_detections, timestamp)
        self._check_sync(radar_detections, timestamp)
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
            if j in used_radar_indices:
                continue
            if self._radar_only_min_speed is not None and abs(rad.velocity) < self._radar_only_min_speed:
                continue                     # unconfirmed AND static: most likely clutter
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