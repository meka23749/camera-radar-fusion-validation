"""Tests for Camera Perception (src/perception/camera_perception.py)."""

import numpy as np
from src.perception.camera_perception import CameraPerception
from src.interfaces import CameraImage, DetectedObject


def _make_test_image(timestamp: float = 3.0) -> CameraImage:
    """Helper: build a controlled CameraImage for testing."""
    pixels = np.zeros((900, 1600, 3), dtype=np.uint8)
    return CameraImage(pixels=pixels, timestamp=timestamp, camera_id="front")


def test_detect_returns_a_list():
    """detect() returns a list of DetectedObject."""
    perception = CameraPerception()
    image = _make_test_image()
    result = perception.detect(image)
    assert isinstance(result, list)
    assert all(isinstance(obj, DetectedObject) for obj in result)


def test_detections_carry_image_timestamp():
    """Detected objects keep the timestamp of the input image (synchronization)."""
    perception = CameraPerception()
    image = _make_test_image(timestamp=7.0)
    result = perception.detect(image)
    assert all(obj.timestamp == 7.0 for obj in result)


def test_confidence_is_between_zero_and_one():
    """Every detection has a confidence score in the valid range [0, 1]."""
    perception = CameraPerception()
    image = _make_test_image()
    result = perception.detect(image)
    assert all(0.0 <= obj.confidence <= 1.0 for obj in result)