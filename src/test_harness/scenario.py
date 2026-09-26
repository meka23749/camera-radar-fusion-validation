"""Synthetic scenarios with ground truth + object-level sensor models.

Purpose: make the validation loop run END TO END with real numbers today,
before the nuScenes loader exists. The ground truth is known exactly, and the
sensor models reproduce the typical weaknesses of each sensor.

This is an industry-standard technique (phenomenological / object-level sensor
models) for validating FUSION logic. It does NOT validate the camera detector or
the radar itself: REQ-03 / REQ-04 still need real data (nuScenes).

Everything is driven by a seeded RNG -> fully reproducible (REQ-16).
"""

import math
from dataclasses import dataclass, field
import numpy as np

from src.interfaces import DetectedObject, GroundTruthObject, RadarPoint, RadarPoints

VEHICLES = {"car", "truck"}
CLASSES = ["car", "car", "car", "truck", "pedestrian", "cyclist"]   # sampling weights


@dataclass
class _Actor:
    object_class: str
    x: float
    y: float
    vx: float


class ScenarioGenerator:
    """Moving actors in front of the ego vehicle, frame by frame (dt = 0.1 s)."""

    def __init__(self, seed: int = 0, num_frames: int = 200, num_actors: int = 25, dt: float = 0.1):
        self._rng = np.random.default_rng(seed)
        self._dt = dt
        self._frames: list[list[GroundTruthObject]] = []
        actors = [self._spawn() for _ in range(num_actors)]
        for k in range(num_frames):
            t = round(k * dt, 6)
            self._frames.append([
                GroundTruthObject(a.object_class, a.x, a.y, a.vx, t) for a in actors
            ])
            for a in actors:
                a.x += a.vx * dt
            # an actor that leaves the zone is replaced by a new one
            actors = [a if 1.0 < a.x < 200.0 else self._spawn() for a in actors]

    def _spawn(self) -> _Actor:
        cls = str(self._rng.choice(CLASSES))
        vulnerable = cls in ("pedestrian", "cyclist")
        return _Actor(
            object_class=cls,
            x=float(self._rng.uniform(3.0, 60.0 if vulnerable else 195.0)),
            y=float(self._rng.uniform(-12.0, 12.0)),
            vx=float(self._rng.uniform(-2.0, 1.0) if vulnerable else self._rng.uniform(-15.0, 5.0)),
        )

    def num_frames(self) -> int:
        return len(self._frames)

    def timestamp(self, k: int) -> float:
        return self._frames[k][0].timestamp if self._frames[k] else round(k * self._dt, 6)

    def ground_truth(self, k: int) -> list[GroundTruthObject]:
        return self._frames[k]