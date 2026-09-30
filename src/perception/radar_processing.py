"""Radar Processing: turns raw radar points into detected objects.

One real object usually produces SEVERAL radar echoes (a car reflects from its
bumper, wheels, mirrors...). Turning every echo into its own object would create
duplicates, i.e. false positives (REQ-09). This block therefore groups nearby
echoes into clusters and outputs ONE DetectedObject per cluster.

The class stays "unknown" because radar alone cannot classify objects.
Confidence grows with the number of echoes supporting the cluster: a single
isolated echo is more likely clutter than a 4-echo cluster.
"""

import math
from src.interfaces import RadarPoints, DetectedObject


class RadarProcessing:
    """Extracts detected objects from raw radar points.

    Input:  a RadarPoints frame (raw echoes).
    Output: a list of DetectedObject, one per cluster of echoes (may be empty).
    """

    def __init__(
        self,
        cluster_eps: float = 2.0,
        single_point_confidence: float = 0.4,
        confidence_per_point: float = 0.15,
    ):
        """Create the radar processing block.

        Args:
            cluster_eps: max distance (m) between two echoes of the same cluster.
            single_point_confidence: confidence of a cluster with one echo.
            confidence_per_point: confidence added per additional echo (capped at 0.95).
        """
        self._eps = cluster_eps
        self._c0 = single_point_confidence
        self._dc = confidence_per_point

    def _clusters(self, points):
        """Group echoes: two echoes closer than cluster_eps end up in the same group.

        Chains are allowed (A near B, B near C -> A, B, C together).
        Implemented with union-find. O(n^2), fine for < ~200 echoes per frame.
        """
        parent = list(range(len(points)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                if math.hypot(points[i].x - points[j].x, points[i].y - points[j].y) <= self._eps:
                    parent[find(i)] = find(j)

        groups: dict[int, list] = {}
        for i, p in enumerate(points):
            groups.setdefault(find(i), []).append(p)
        return list(groups.values())

    def process(self, radar: RadarPoints) -> list[DetectedObject]:
        """Convert radar points into one detected object per cluster.

        Args:
            radar: the radar frame to process.

        Returns:
            A list of DetectedObject (empty if there are no points), each
            carrying the timestamp of the radar frame (REQ-12).
        """
        detections = []
        for cluster in self._clusters(radar.points):
            n = len(cluster)
            detections.append(
                DetectedObject(
                    object_class="unknown",
                    x=sum(p.x for p in cluster) / n,
                    y=sum(p.y for p in cluster) / n,
                    velocity=sum(p.velocity for p in cluster) / n,
                    confidence=min(0.95, self._c0 + self._dc * (n - 1)),
                    timestamp=radar.timestamp,
                )
            )
        # Deterministic order (closest first) -> reproducible outputs (REQ-16)
        detections.sort(key=lambda d: (d.x, d.y))
        return detections