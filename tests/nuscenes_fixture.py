"""A tiny, hand-made dataset in nuScenes format, for tests (no licensed data).

One scene, two samples. Every number is chosen so that the expected result can
be computed by hand.
"""

import json

import numpy as np

IDENTITY = [1.0, 0.0, 0.0, 0.0]
YAW_180 = [0.0, 0.0, 0.0, 1.0]            # rotation of 180 deg around z
CAMERA_LOOKING_FORWARD = [0.5, -0.5, 0.5, -0.5]   # camera z axis (optical axis) -> vehicle x axis

# Annotations of sample 1, given in the VEHICLE frame at camera time
# (the vehicle is at global x = 100 m, so global x = vehicle x + 100).
# (token, category, x, y, lidar points, radar points, expected result)
ANNOTATIONS_S1 = [
    ("a_car",       "vehicle.car",               30.0,   2.0, 50, 3, "car"),
    ("a_moto",      "vehicle.motorcycle",        15.0,   1.0, 20, 1, "cyclist"),
    ("a_bus",       "vehicle.bus.rigid",         40.0,  -4.0, 80, 2, "truck"),
    ("a_child",     "human.pedestrian.child",    12.0,  -2.0, 15, 0, "pedestrian"),
    ("a_behind",    "vehicle.car",              -10.0,   0.0, 40, 2, "ignored"),   # behind the vehicle
    ("a_side",      "vehicle.car",               10.0,  20.0, 30, 1, "ignored"),   # outside the FOV
    ("a_cone",      "movable_object.trafficcone", 20.0,  0.0, 10, 0, "ignored"),   # out-of-scope class
    ("a_invisible", "vehicle.car",               60.0,  -3.0,  0, 0, "ignored"),   # no sensor point
    ("a_far",       "vehicle.car",              190.0,   0.0,  2, 1, "ignored"),   # beyond 180 m
]

RADAR_FIELDS = ("x y z dyn_prop id rcs vx vy vx_comp vy_comp is_quality_valid "
                "ambig_state x_rms y_rms invalid_state pdh0 vx_rms vy_rms").split()
RADAR_SIZES = "4 4 4 1 2 4 4 4 4 4 1 1 1 1 1 1 1 1".split()
RADAR_TYPES = "F F F I I F F F F F I I I I I I I I".split()
_NUMPY = {("F", "4"): "<f4", ("I", "1"): "i1", ("I", "2"): "<i2"}
RADAR_DTYPE = np.dtype([(n, _NUMPY[(t, s)]) for n, t, s in
                        zip(RADAR_FIELDS, RADAR_TYPES, RADAR_SIZES)])


def write_radar_pcd(path, points):
    header = "\n".join([
        "VERSION 0.7",
        "FIELDS " + " ".join(RADAR_FIELDS),
        "SIZE " + " ".join(RADAR_SIZES),
        "TYPE " + " ".join(RADAR_TYPES),
        "COUNT " + " ".join(["1"] * len(RADAR_FIELDS)),
        f"WIDTH {len(points)}", "HEIGHT 1", "VIEWPOINT 0 0 0 1 0 0 0",
        f"POINTS {len(points)}", "DATA binary",
    ]) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(header.encode("ascii") + points.tobytes())


def make_dataset(root, ego_shift=1.0, radar_rotation=IDENTITY, radar_offset_us=20_000):
    """Write the mini dataset under root and return root.

    Sample 1: camera at t = 0.98 s, radar at t = 0.98 s + radar_offset_us.
    The ego vehicle is at x = 100 m at camera time and x = 100 + ego_shift at
    radar time (driving straight along the global x axis).
    The radar is mounted 3.5 m ahead of the ego origin, 0.5 m high.
    The radar sees one point 20 m in front of the sensor, vx_comp = 5 m/s.
    """
    meta = root / "v1.0-mini"
    meta.mkdir(parents=True)
    t_cam = 980_000
    t_rad = t_cam + radar_offset_us

    tables = {
        "scene": [{"token": "scene1", "name": "scene-0001", "first_sample_token": "s1"}],
        "sample": [
            {"token": "s1", "timestamp": 1_000_000, "prev": "", "next": "s2", "scene_token": "scene1"},
            {"token": "s2", "timestamp": 1_500_000, "prev": "s1", "next": "", "scene_token": "scene1"},
        ],
        "sensor": [
            {"token": "sensor_cam", "channel": "CAM_FRONT", "modality": "camera"},
            {"token": "sensor_rad", "channel": "RADAR_FRONT", "modality": "radar"},
        ],
        "calibrated_sensor": [
            {"token": "cs_cam", "sensor_token": "sensor_cam", "translation": [1.7, 0.0, 1.5],
             "rotation": CAMERA_LOOKING_FORWARD,
             "camera_intrinsic": [[1266.0, 0.0, 800.0], [0.0, 1266.0, 450.0], [0.0, 0.0, 1.0]]},
            {"token": "cs_rad", "sensor_token": "sensor_rad", "translation": [3.5, 0.0, 0.5],
             "rotation": radar_rotation},
        ],
        "ego_pose": [
            {"token": "ep_cam1", "timestamp": t_cam, "translation": [100.0, 0.0, 0.0], "rotation": IDENTITY},
            {"token": "ep_rad1", "timestamp": t_rad, "translation": [100.0 + ego_shift, 0.0, 0.0],
             "rotation": IDENTITY},
            {"token": "ep_cam2", "timestamp": 1_480_000, "translation": [105.0, 0.0, 0.0], "rotation": IDENTITY},
            {"token": "ep_rad2", "timestamp": 1_500_000, "translation": [105.0, 0.0, 0.0], "rotation": IDENTITY},
            {"token": "ep_sweep", "timestamp": 1_050_000, "translation": [101.5, 0.0, 0.0], "rotation": IDENTITY},
        ],
        "sample_data": [
            {"token": "cam1", "sample_token": "s1", "calibrated_sensor_token": "cs_cam",
             "ego_pose_token": "ep_cam1", "timestamp": t_cam, "is_key_frame": True,
             "filename": "samples/CAM_FRONT/cam1.jpg", "width": 1600, "height": 900},
            {"token": "rad1", "sample_token": "s1", "calibrated_sensor_token": "cs_rad",
             "ego_pose_token": "ep_rad1", "timestamp": t_rad, "is_key_frame": True,
             "filename": "samples/RADAR_FRONT/rad1.pcd"},
            {"token": "sweep", "sample_token": "s1", "calibrated_sensor_token": "cs_rad",
             "ego_pose_token": "ep_sweep", "timestamp": 1_050_000, "is_key_frame": False,
             "filename": "sweeps/RADAR_FRONT/sweep.pcd"},
            {"token": "cam2", "sample_token": "s2", "calibrated_sensor_token": "cs_cam",
             "ego_pose_token": "ep_cam2", "timestamp": 1_480_000, "is_key_frame": True,
             "filename": "samples/CAM_FRONT/cam2.jpg", "width": 1600, "height": 900},
            {"token": "rad2", "sample_token": "s2", "calibrated_sensor_token": "cs_rad",
             "ego_pose_token": "ep_rad2", "timestamp": 1_500_000, "is_key_frame": True,
             "filename": "samples/RADAR_FRONT/rad2.pcd"},
        ],
    }
    # annotations: sample 1 as listed above, sample 2 has one car 50 m ahead
    # (the vehicle is at global x = 105 m at the camera time of sample 2)
    categories = sorted({a[1] for a in ANNOTATIONS_S1})
    tables["category"] = [{"token": f"cat_{c}", "name": c} for c in categories]
    tables["instance"], tables["sample_annotation"] = [], []
    rows = [("s1", *a[:6], 100.0) for a in ANNOTATIONS_S1] + \
           [("s2", "a_s2_car", "vehicle.car", 50.0, 0.0, 30, 2, 105.0)]
    for sample, token, cat, x, y, lidar, radar, ego_x in rows:
        tables["instance"].append({"token": f"inst_{token}", "category_token": f"cat_{cat}"})
        tables["sample_annotation"].append({
            "token": token, "sample_token": sample, "instance_token": f"inst_{token}",
            "translation": [x + ego_x, y, 1.0], "size": [1.8, 4.5, 1.5], "rotation": IDENTITY,
            "num_lidar_pts": lidar, "num_radar_pts": radar, "visibility_token": "4",
        })

    # samples listed in the file in REVERSE order: the loader must follow the "next" links
    tables["sample"].reverse()
    for name, records in tables.items():
        (meta / f"{name}.json").write_text(json.dumps(records), encoding="utf-8")

    point = np.zeros(1, dtype=RADAR_DTYPE)
    point["x"], point["vx_comp"] = 20.0, 5.0
    write_radar_pcd(root / "samples/RADAR_FRONT/rad1.pcd", point)
    write_radar_pcd(root / "samples/RADAR_FRONT/rad2.pcd", np.zeros(0, dtype=RADAR_DTYPE))
    return root