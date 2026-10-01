"""Reader for nuScenes radar files (.pcd, binary Point Cloud Data format).

A .pcd file has a short text header followed by binary data, e.g.:

    FIELDS x y z dyn_prop id rcs vx vy vx_comp vy_comp ...
    SIZE   4 4 4 1        2  4   4  4  4       4       ...
    TYPE   F F F I        I  F   F  F  F       F       ...
    COUNT  1 1 1 1        1  1   1  1  1       1       ...
    POINTS 125
    DATA binary

The header describes the binary layout of ONE point; the data is POINTS points
packed one after the other (no padding). We turn the header into a NumPy
structured dtype and read the data with it.

Coordinates (x, y, z) are in the RADAR SENSOR frame, not in the vehicle frame.
"""

from pathlib import Path

import numpy as np

# PCD (TYPE, SIZE) -> NumPy type code, little-endian
_NUMPY_TYPES = {
    ("F", 4): "<f4", ("F", 8): "<f8",
    ("I", 1): "i1", ("I", 2): "<i2", ("I", 4): "<i4",
    ("U", 1): "u1", ("U", 2): "<u2", ("U", 4): "<u4",
}


def read_radar_pcd(path: str | Path) -> np.ndarray:
    """Read a binary .pcd radar file into a NumPy structured array.

    Args:
        path: path to the .pcd file.

    Returns:
        One record per radar point; fields named as in the header
        (e.g. points["x"], points["vx_comp"]).

    Raises:
        ValueError: if the file is not a valid binary PCD file.
    """
    header: dict[str, list[str]] = {}
    with open(path, "rb") as f:
        while True:
            line = f.readline()
            if not line:
                raise ValueError(f"{path}: no DATA line in header")
            text = line.decode("ascii").strip()
            if not text or text.startswith("#"):
                continue
            key, *values = text.split()
            header[key] = values
            if key == "DATA":
                break
        data = f.read()

    if header["DATA"] != ["binary"]:
        raise ValueError(f"{path}: only 'DATA binary' is supported, got {header['DATA']}")
    if any(c != "1" for c in header["COUNT"]):
        raise ValueError(f"{path}: fields with COUNT > 1 are not supported")

    dtype = np.dtype([
        (name, _NUMPY_TYPES[(typ, int(size))])
        for name, typ, size in zip(header["FIELDS"], header["TYPE"], header["SIZE"])
    ])
    n_points = int(header["POINTS"][0])

    expected = n_points * dtype.itemsize
    if len(data) < expected:
        raise ValueError(f"{path}: truncated data ({len(data)} bytes, expected {expected})")

    return np.frombuffer(data, dtype=dtype, count=n_points)