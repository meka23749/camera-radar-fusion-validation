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



@dataclass
class CameraModel:
    """Object-level camera: good class, poor depth, blind beyond max_range."""
    max_range: float = 80.0
    p_detect_near: float = 0.97
    depth_error: float = 0.05          # sigma = 5 % of range
    lateral_error: float = 0.3         # m
    p_confusion: float = 0.05
    fp_per_frame: float = 0.3
    seed: int = 1
    _rng: np.random.Generator = field(init=False, repr=False)

    def __post_init__(self):
        self._rng = np.random.default_rng(self.seed)

    def _p_detect(self, r: float) -> float:
        if r > self.max_range:
            return 0.0
        return self.p_detect_near * (1.0 - 0.4 * (r / self.max_range) ** 2)

    def observe(self, gt: list[GroundTruthObject], t: float) -> list[DetectedObject]:
        out = []
        for o in gt:
            r = math.hypot(o.x, o.y)
            if self._rng.random() > self._p_detect(r):
                continue
            cls = o.object_class
            if self._rng.random() < self.p_confusion:
                cls = str(self._rng.choice([c for c in set(CLASSES) if c != cls]))
            out.append(DetectedObject(
                object_class=cls,
                x=o.x + self._rng.normal(0, self.depth_error * r),
                y=o.y + self._rng.normal(0, self.lateral_error),
                velocity=0.0,                          # camera: no direct velocity
                confidence=float(np.clip(self._rng.normal(0.85 - 0.3 * r / self.max_range, 0.1), 0.05, 0.99)),
                timestamp=t,
            ))
        for _ in range(self._rng.poisson(self.fp_per_frame)):
            out.append(DetectedObject(str(self._rng.choice(CLASSES)),
                                      float(self._rng.uniform(5, 70)), float(self._rng.uniform(-10, 10)),
                                      0.0, float(self._rng.uniform(0.1, 0.5)), t))
        return out


@dataclass
class RadarModel:
    """Point-level radar: accurate range, several echoes per vehicle, clutter."""
    max_range: float = 180.0
    p_detect: float = 0.93
    range_error: float = 0.25          # m
    azimuth_error_deg: float = 0.5     # lateral error = r * azimuth error
    clutter_per_frame: float = 3.0
    seed: int = 2
    _rng: np.random.Generator = field(init=False, repr=False)

    def __post_init__(self):
        self._rng = np.random.default_rng(self.seed)

    def observe(self, gt: list[GroundTruthObject], t: float) -> RadarPoints:
        pts = []
        az = math.radians(self.azimuth_error_deg)
        for o in gt:
            r = math.hypot(o.x, o.y)
            weak = o.object_class in ("pedestrian", "cyclist")
            p = self.p_detect * (0.8 if weak else 1.0) * (1.0 if r < 0.8 * self.max_range else 0.7)
            if r > self.max_range or self._rng.random() > p:
                continue
            n_echoes = 1 if weak else int(self._rng.integers(1, 5))
            for _ in range(n_echoes):
                pts.append(RadarPoint(
                    x=o.x + self._rng.normal(0, self.range_error),
                    y=o.y + self._rng.normal(0, max(0.2, r * az)) + self._rng.uniform(-0.8, 0.8) * (not weak),
                    velocity=o.velocity + self._rng.normal(0, 0.1),
                ))
        for _ in range(self._rng.poisson(self.clutter_per_frame)):
            pts.append(RadarPoint(float(self._rng.uniform(2, 150)), float(self._rng.uniform(-15, 15)),
                                  float(self._rng.normal(0, 3))))
        return RadarPoints(points=pts, timestamp=t)