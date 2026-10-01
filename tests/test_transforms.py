"""Tests for coordinate transforms (src/perception/transforms.py).

Every test uses a case whose answer is known without the code under test.
"""

import math

import numpy as np

from src.perception.transforms import (
    quaternion_to_matrix, make_transform, invert_transform,
    transform_points, rotate_vectors,
)

IDENTITY_Q = [1.0, 0.0, 0.0, 0.0]
YAW_90_Q = [math.cos(math.pi / 4), 0.0, 0.0, math.sin(math.pi / 4)]   # +90 deg around z


def test_identity_quaternion_gives_identity_matrix():
    assert np.allclose(quaternion_to_matrix(IDENTITY_Q), np.eye(3))


def test_yaw_90_turns_x_axis_into_y_axis():
    """Rotating 'straight ahead' by +90 deg around z gives 'to the left'."""
    R = quaternion_to_matrix(YAW_90_Q)
    assert np.allclose(R @ [1.0, 0.0, 0.0], [0.0, 1.0, 0.0])


def test_quaternion_is_normalized():
    """A scaled quaternion describes the same rotation."""
    assert np.allclose(quaternion_to_matrix(np.array(YAW_90_Q) * 2.0),
                       quaternion_to_matrix(YAW_90_Q))


def test_rotation_matrices_are_valid():
    """For any quaternion: R is orthonormal (R R^T = I) and det(R) = +1."""
    rng = np.random.default_rng(0)
    for q in rng.normal(size=(20, 4)):
        R = quaternion_to_matrix(q)
        assert np.allclose(R @ R.T, np.eye(3))
        assert math.isclose(np.linalg.det(R), 1.0)


def test_sensor_mounted_ahead_and_rotated():
    """Sensor 3.5 m in front of the ego origin, looking left (yaw +90 deg).

    A point 10 m in front of the SENSOR is 3.5 m ahead and 10 m to the left
    of the VEHICLE.
    """
    sensor_to_ego = make_transform([3.5, 0.0, 0.0], YAW_90_Q)
    assert np.allclose(transform_points(sensor_to_ego, [10.0, 0.0, 0.0]), [[3.5, 10.0, 0.0]])


def test_inverse_round_trip_returns_original_points():
    T = make_transform([12.0, -3.0, 1.5], [0.9, 0.1, -0.2, 0.3])
    points = np.array([[1.0, 2.0, 3.0], [-40.0, 7.5, 0.0]])
    back = transform_points(invert_transform(T), transform_points(T, points))
    assert np.allclose(back, points)
    assert np.allclose(invert_transform(T) @ T, np.eye(4))


def test_velocity_is_rotated_but_not_translated():
    T = make_transform([100.0, 50.0, 0.0], YAW_90_Q)
    assert np.allclose(rotate_vectors(T, [5.0, 0.0, 0.0]), [[0.0, 5.0, 0.0]])


def test_ego_motion_compensation_through_global_frame():
    """The vehicle drives 1 m forward between the radar and the camera timestamps.

    A static object 20 m ahead at radar time must appear 19 m ahead at camera time.
    """
    radar_to_ego = make_transform([0.0, 0.0, 0.0], IDENTITY_Q)
    ego_at_radar_time = make_transform([100.0, 0.0, 0.0], IDENTITY_Q)    # ego -> global
    ego_at_camera_time = make_transform([101.0, 0.0, 0.0], IDENTITY_Q)

    chain = invert_transform(ego_at_camera_time) @ ego_at_radar_time @ radar_to_ego
    assert np.allclose(transform_points(chain, [20.0, 0.0, 0.0]), [[19.0, 0.0, 0.0]])