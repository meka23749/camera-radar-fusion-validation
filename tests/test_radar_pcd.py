"""Tests for the nuScenes radar .pcd reader (src/perception/radar_pcd.py).

The test files are generated here with the same layout as real nuScenes radar
files, so these tests run in CI without the (licensed) dataset.
"""

import numpy as np
import pytest

from src.perception.radar_pcd import read_radar_pcd

# Layout of a nuScenes radar point, copied from a real file header
FIELDS = ("x y z dyn_prop id rcs vx vy vx_comp vy_comp is_quality_valid "
          "ambig_state x_rms y_rms invalid_state pdh0 vx_rms vy_rms").split()
SIZES = "4 4 4 1 2 4 4 4 4 4 1 1 1 1 1 1 1 1".split()
TYPES = "F F F I I F F F F F I I I I I I I I".split()
NUMPY = {("F", "4"): "<f4", ("I", "1"): "i1", ("I", "2"): "<i2"}
DTYPE = np.dtype([(n, NUMPY[(t, s)]) for n, t, s in zip(FIELDS, TYPES, SIZES)])


def _write_pcd(path, points, data_kind="binary", declared_points=None):
    """Write a PCD file with the nuScenes radar layout."""
    n = len(points) if declared_points is None else declared_points
    header = "\n".join([
        "# .PCD v0.7 - Point Cloud Data file format",
        "VERSION 0.7",
        "FIELDS " + " ".join(FIELDS),
        "SIZE " + " ".join(SIZES),
        "TYPE " + " ".join(TYPES),
        "COUNT " + " ".join(["1"] * len(FIELDS)),
        f"WIDTH {n}",
        "HEIGHT 1",
        "VIEWPOINT 0 0 0 1 0 0 0",
        f"POINTS {n}",
        f"DATA {data_kind}",
    ]) + "\n"
    path.write_bytes(header.encode("ascii") + points.tobytes())
    return path


def _two_points():
    points = np.zeros(2, dtype=DTYPE)
    points["x"] = [12.5, 80.0]
    points["y"] = [-1.25, 4.0]
    points["vx_comp"] = [-3.0, 0.5]
    points["invalid_state"] = [0, 1]
    return points


def test_one_point_is_43_bytes():
    """Same layout as the real files: 18 fields packed without padding."""
    assert DTYPE.itemsize == 43


def test_reads_all_points_and_fields(tmp_path):
    path = _write_pcd(tmp_path / "radar.pcd", _two_points())
    points = read_radar_pcd(path)
    assert len(points) == 2
    assert points.dtype.names == tuple(FIELDS)
    assert points["x"].tolist() == [12.5, 80.0]
    assert points["y"].tolist() == [-1.25, 4.0]
    assert points["vx_comp"].tolist() == [-3.0, 0.5]
    assert points["invalid_state"].tolist() == [0, 1]


def test_empty_file_gives_zero_points(tmp_path):
    path = _write_pcd(tmp_path / "radar.pcd", np.zeros(0, dtype=DTYPE))
    assert len(read_radar_pcd(path)) == 0


def test_ascii_data_is_rejected(tmp_path):
    path = _write_pcd(tmp_path / "radar.pcd", _two_points(), data_kind="ascii")
    with pytest.raises(ValueError, match="binary"):
        read_radar_pcd(path)


def test_truncated_file_is_rejected(tmp_path):
    """Header announces 5 points but the file only contains 2: corrupted file."""
    path = _write_pcd(tmp_path / "radar.pcd", _two_points(), declared_points=5)
    with pytest.raises(ValueError, match="truncated"):
        read_radar_pcd(path)