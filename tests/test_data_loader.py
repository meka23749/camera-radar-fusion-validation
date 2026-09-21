"""Tests for the Data Loader (src/perception/data_loader.py)."""

import pytest
from src.perception.data_loader import DataLoader
from src.interfaces import CameraImage, RadarPoints


def test_num_frames_matches_configuration():
    """The loader reports the number of frames it was created with."""
    loader = DataLoader(num_frames=10)
    assert loader.num_frames() == 10


def test_get_frame_returns_camera_and_radar():
    """get_frame returns a CameraImage and a RadarPoints."""
    loader = DataLoader(num_frames=5)
    camera, radar = loader.get_frame(0)
    assert isinstance(camera, CameraImage)
    assert isinstance(radar, RadarPoints)


def test_camera_and_radar_are_synchronized():
    """Camera and radar of the same frame share the same timestamp (REQ-12)."""
    loader = DataLoader(num_frames=5)
    camera, radar = loader.get_frame(3)
    assert camera.timestamp == radar.timestamp


def test_out_of_range_index_raises():
    """Requesting a frame outside the valid range raises IndexError."""
    loader = DataLoader(num_frames=5)
    with pytest.raises(IndexError):
        loader.get_frame(99)