"""nuScenes loader: turns one nuScenes sample into one frame for the system (REQ-11).

For every annotated sample (keyframe, 2 Hz) it provides:
- the CAM_FRONT image path and timestamp (the frame's reference time),
- the RADAR_FRONT points in the VEHICLE frame AT THE CAMERA TIMESTAMP.

Camera and radar never measure at the same instant (12 Hz vs 13 Hz, up to
~72 ms apart in v1.0-mini). REQ-12 therefore requires that both measurements
are at most 100 ms apart and that the radar data is motion-compensated to the
camera timestamp. The compensation goes through the global frame:

    radar sensor -> ego (radar time) -> global -> ego (camera time)

It corrects the motion of OUR vehicle; the motion of other objects during the
offset is not corrected here.

The loader does NOT filter radar points: all points are returned, whatever
their quality flags. Filtering is a processing decision, measured separately.
Image pixels are not loaded (the camera detector is still a stub).

Usage:
    loader = NuScenesLoader(os.environ["NUSCENES_ROOT"])
    frame = loader.get_frame(0)
"""

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.interfaces import RadarPoint, RadarPoints
from src.perception.fusion import SynchronizationError
from src.perception.radar_pcd import read_radar_pcd
from src.perception.transforms import (
    make_transform, invert_transform, transform_points, rotate_vectors,
)


@dataclass
class NuScenesFrame:
    """One nuScenes sample, ready for the system under test."""
    sample_token: str
    timestamp: float                 # camera timestamp, seconds
    camera_path: Path                # CAM_FRONT image file
    radar: RadarPoints               # in the ego frame at camera time
    sync_offset: float               # radar time - camera time, seconds (before compensation)
    ego_to_global: np.ndarray        # 4x4 vehicle pose at camera time (for ground truth)


class NuScenesLoader:
    """Reads nuScenes metadata once, then builds frames on demand."""

    def __init__(
        self,
        root: str | Path,
        version: str = "v1.0-mini",
        camera: str = "CAM_FRONT",
        radar: str = "RADAR_FRONT",
        max_sync_offset: float = 0.100,
    ):
        """
        Args:
            root: dataset folder (contains samples/, sweeps/, v1.0-mini/).
            version: metadata folder name.
            camera, radar: sensor channels to use.
            max_sync_offset: max |radar time - camera time| in seconds (REQ-12).
        """
        self._root = Path(root)
        self._max_sync_offset = max_sync_offset
        meta = self._root / version

        def load(name):
            return json.loads((meta / f"{name}.json").read_text(encoding="utf-8"))

        channel_of_sensor = {s["token"]: s["channel"] for s in load("sensor")}
        self._calib = {c["token"]: c for c in load("calibrated_sensor")}
        self._ego_pose = {e["token"]: e for e in load("ego_pose")}

        # keyframe sample_data of our two sensors, per sample
        self._data: dict[str, dict[str, dict]] = {}
        for d in load("sample_data"):
            channel = channel_of_sensor[self._calib[d["calibrated_sensor_token"]]["sensor_token"]]
            if d["is_key_frame"] and channel in (camera, radar):
                self._data.setdefault(d["sample_token"], {})["camera" if channel == camera else "radar"] = d

        # samples in chronological order, scene by scene (follow the "next" links)
        samples = {s["token"]: s for s in load("sample")}
        self._order: list[str] = []
        for scene in load("scene"):
            token = scene["first_sample_token"]
            while token:
                self._order.append(token)
                token = samples[token]["next"]

    def num_frames(self) -> int:
        return len(self._order)

    def _pose(self, token: str) -> np.ndarray:
        pose = self._ego_pose[token]
        return make_transform(pose["translation"], pose["rotation"])

    def get_frame(self, index: int) -> NuScenesFrame:
        """Build the frame of the index-th sample (chronological order)."""
        sample_token = self._order[index]
        cam, rad = self._data[sample_token]["camera"], self._data[sample_token]["radar"]

        t_cam = cam["timestamp"] / 1e6           # nuScenes timestamps are microseconds
        t_rad = rad["timestamp"] / 1e6
        offset = t_rad - t_cam
        if abs(offset) > self._max_sync_offset:
            raise SynchronizationError(
                f"sample {sample_token}: radar and camera are {offset * 1000:.1f} ms apart "
                f"(max {self._max_sync_offset * 1000:.0f} ms, REQ-12)"
            )

        calib = self._calib[rad["calibrated_sensor_token"]]
        radar_to_ego = make_transform(calib["translation"], calib["rotation"])
        ego_cam = self._pose(cam["ego_pose_token"])
        chain = invert_transform(ego_cam) @ self._pose(rad["ego_pose_token"]) @ radar_to_ego

        raw = read_radar_pcd(self._root / rad["filename"])
        xyz = transform_points(chain, np.column_stack([raw["x"], raw["y"], raw["z"]]))
        vel = rotate_vectors(chain, np.column_stack([raw["vx_comp"], raw["vy_comp"],
                                                     np.zeros(len(raw))]))
        points = [RadarPoint(x=float(p[0]), y=float(p[1]), velocity=float(v[0]))
                  for p, v in zip(xyz, vel)]

        return NuScenesFrame(
            sample_token=sample_token,
            timestamp=t_cam,
            camera_path=self._root / cam["filename"],
            radar=RadarPoints(points=points, timestamp=t_cam),   # compensated to camera time
            sync_offset=offset,
            ego_to_global=ego_cam,
        )