"""Ground truth from nuScenes annotations, in the vehicle frame at camera time.

nuScenes annotates every object around the vehicle (360 deg), in the global map
frame, with 23 categories. This block turns the annotations of one sample into
what OUR system can be judged on. Each annotation ends up in one of two lists:

- evaluated: the system must detect it (missing it = false negative),
- ignored:   a real object the system is NOT judged on; missing it is not a
             false negative, and a detection on it is not a false positive.

Rules (see docs/07_Ground_Truth_Rules.md for the measurements behind them):
1. Field of view: inside the horizontal field of view of the front camera,
   computed from its calibration (64.6 deg in v1.0-mini), and within max_range.
2. Classes: mapped to the REQ-06 classes (vehicle / pedestrian / two-wheeler);
   other categories (cones, barriers, ...) are ignored.
3. Visibility: an annotation with no lidar AND no radar point is ignored
   (same rule as the official nuScenes detection evaluation).

Known approximations:
- Annotations are taken at the lidar timestamp, the frame at the camera
  timestamp (up to ~50 ms earlier); moving objects can be off by ~0.5 m.
- Annotation velocities are not computed (0.0): the validation does not use them.
"""

import json
import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from src.interfaces import GroundTruthObject
from src.perception.nuscenes_loader import NuScenesFrame
from src.perception.transforms import invert_transform, transform_points, quaternion_to_matrix

# nuScenes category prefix -> class of the system (REQ-06: Fahrzeug / Fussgaenger / Zweirad)
CLASS_MAP = {
    "vehicle.car": "car",
    "vehicle.truck": "truck",
    "vehicle.bus": "truck",            # bus.rigid, bus.bendy
    "vehicle.construction": "truck",
    "vehicle.trailer": "truck",
    "vehicle.motorcycle": "cyclist",   # "cyclist" = two-wheeler (Zweirad)
    "vehicle.bicycle": "cyclist",
    "human.pedestrian": "pedestrian",  # adult, child, construction_worker, ...
}


def map_category(name: str) -> str | None:
    """System class of a nuScenes category, or None if out of scope."""
    for prefix, cls in CLASS_MAP.items():
        if name == prefix or name.startswith(prefix + "."):
            return cls
    return None


@dataclass
class FrameGroundTruth:
    evaluated: list[GroundTruthObject] = field(default_factory=list)
    ignored: list[GroundTruthObject] = field(default_factory=list)


@dataclass
class _Camera:
    x: float
    y: float
    yaw: float            # direction of the optical axis in the vehicle frame (rad)
    half_fov: float       # half of the horizontal field of view (rad)


class NuScenesGroundTruth:
    """Annotations of a nuScenes sample, split into evaluated and ignored objects."""

    def __init__(self, root: str | Path, version: str = "v1.0-mini",
                 camera: str = "CAM_FRONT", max_range: float = 180.0):
        meta = Path(root) / version

        def load(name):
            return json.loads((meta / f"{name}.json").read_text(encoding="utf-8"))

        self._max_range = max_range
        category = {c["token"]: c["name"] for c in load("category")}
        self._category_of_instance = {i["token"]: category[i["category_token"]]
                                      for i in load("instance")}
        self._annotations = defaultdict(list)
        for a in load("sample_annotation"):
            self._annotations[a["sample_token"]].append(a)

        # camera geometry per sample (calibration can differ between scenes / vehicles)
        channel = {s["token"]: s["channel"] for s in load("sensor")}
        calib = {c["token"]: c for c in load("calibrated_sensor")}
        self._camera: dict[str, _Camera] = {}
        for d in load("sample_data"):
            c = calib[d["calibrated_sensor_token"]]
            if d["is_key_frame"] and channel[c["sensor_token"]] == camera:
                axis = quaternion_to_matrix(c["rotation"]) @ [0.0, 0.0, 1.0]   # optical axis
                fx = c["camera_intrinsic"][0][0]
                self._camera[d["sample_token"]] = _Camera(
                    x=c["translation"][0], y=c["translation"][1],
                    yaw=math.atan2(axis[1], axis[0]),
                    half_fov=math.atan(d["width"] / 2 / fx),
                )

    def in_field_of_view(self, sample_token: str, x: float, y: float) -> bool:
        """Is the point (vehicle frame) inside the camera's field of view and range?"""
        cam = self._camera[sample_token]
        angle = math.atan2(y - cam.y, x - cam.x) - cam.yaw
        angle = (angle + math.pi) % (2 * math.pi) - math.pi          # wrap to [-pi, pi]
        return abs(angle) < cam.half_fov and math.hypot(x, y) <= self._max_range

    def get(self, frame: NuScenesFrame) -> FrameGroundTruth:
        """Ground truth of one frame, in the vehicle frame at the camera timestamp."""
        to_ego = invert_transform(frame.ego_to_global)
        result = FrameGroundTruth()
        for a in self._annotations[frame.sample_token]:
            x, y, _ = transform_points(to_ego, a["translation"])[0]
            cls = map_category(self._category_of_instance[a["instance_token"]])
            obj = GroundTruthObject(object_class=cls or "out_of_scope", x=float(x), y=float(y),
                                    velocity=0.0, timestamp=frame.timestamp)
            visible = a["num_lidar_pts"] + a["num_radar_pts"] > 0
            if cls is not None and visible and self.in_field_of_view(frame.sample_token, x, y):
                result.evaluated.append(obj)
            else:
                result.ignored.append(obj)
        return result