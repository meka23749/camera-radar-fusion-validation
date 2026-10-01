"""Coordinate transforms between sensor, vehicle (ego) and global frames.

nuScenes stores every position in its own frame:
- radar points        -> RADAR SENSOR frame  (calibrated_sensor: sensor -> ego)
- the vehicle itself  -> GLOBAL map frame    (ego_pose: ego -> global, one per timestamp)
- annotations         -> GLOBAL map frame

A pose (translation + rotation) is stored as a 4x4 homogeneous matrix T so that
a point p is transformed with  T @ [x, y, z, 1].  Chaining frames is then a
matrix product, read from RIGHT to LEFT:

    p_ego_cam = inv(ego_cam) @ ego_radar @ radar_to_ego @ p_radar
                \_________/   \_______/   \__________/
                global->ego   ego->global  sensor->ego
                (camera time) (radar time)

Going through the global frame compensates the vehicle's motion between the
radar and the camera timestamps.

Rotations are quaternions in nuScenes order [w, x, y, z].
"""

import numpy as np


def quaternion_to_matrix(q) -> np.ndarray:
    """Convert a quaternion [w, x, y, z] to a 3x3 rotation matrix.

    The quaternion is normalized first, so a slightly non-unit quaternion
    (rounding in the JSON files) still gives a valid rotation.
    """
    w, x, y, z = np.asarray(q, dtype=float) / np.linalg.norm(q)
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - w * z),     2 * (x * z + w * y)],
        [2 * (x * y + w * z),     1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
        [2 * (x * z - w * y),     2 * (y * z + w * x),     1 - 2 * (x * x + y * y)],
    ])


def make_transform(translation, rotation) -> np.ndarray:
    """4x4 matrix from a nuScenes pose: translation [x, y, z], rotation [w, x, y, z]."""
    T = np.eye(4)
    T[:3, :3] = quaternion_to_matrix(rotation)
    T[:3, 3] = translation
    return T


def invert_transform(T: np.ndarray) -> np.ndarray:
    """Inverse of a rigid transform (cheaper and more exact than np.linalg.inv)."""
    R, t = T[:3, :3], T[:3, 3]
    inv = np.eye(4)
    inv[:3, :3] = R.T
    inv[:3, 3] = -R.T @ t
    return inv


def transform_points(T: np.ndarray, points: np.ndarray) -> np.ndarray:
    """Apply T to positions. points: (N, 3) -> (N, 3). Uses rotation AND translation."""
    points = np.asarray(points, dtype=float).reshape(-1, 3)
    return points @ T[:3, :3].T + T[:3, 3]


def rotate_vectors(T: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    """Apply only the rotation of T to directions such as velocities. (N, 3) -> (N, 3).

    A velocity does not depend on where the frame's origin is, so the
    translation must NOT be applied to it.
    """
    vectors = np.asarray(vectors, dtype=float).reshape(-1, 3)
    return vectors @ T[:3, :3].T