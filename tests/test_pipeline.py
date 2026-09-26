"""Integration tests for the full perception pipeline."""

from src.perception.data_loader import DataLoader
from src.perception.camera_perception import CameraPerception
from src.perception.radar_processing import RadarProcessing
from src.perception.fusion import Fusion
from src.perception.output import Output
from src.perception.pipeline import PerceptionPipeline
from src.interfaces import ObstacleList
import math
import pytest


def _make_pipeline():
    """Helper: build a pipeline with all real blocks."""
    return PerceptionPipeline(
        data_loader=DataLoader(num_frames=3),
        camera_perception=CameraPerception(),
        radar_processing=RadarProcessing(),
        fusion=Fusion(distance_threshold=3.0),
        output=Output(confidence_threshold=0.3),
    )


def test_pipeline_returns_obstacle_list():
    """Processing a frame returns an ObstacleList."""
    pipeline = _make_pipeline()
    result = pipeline.process_frame(0)
    assert isinstance(result, ObstacleList)


def test_pipeline_output_has_correct_timestamp():
    """The final obstacle list carries the frame timestamp."""
    pipeline = _make_pipeline()
    result = pipeline.process_frame(2)
    assert result.timestamp == 2.0


def test_pipeline_produces_detections():
    """The pipeline detects at least one obstacle on a synthetic frame."""
    pipeline = _make_pipeline()
    result = pipeline.process_frame(0)
    assert len(result.objects) > 0


def test_all_output_objects_pass_confidence_threshold():
    """Every obstacle in the output respects the Output confidence threshold."""
    pipeline = _make_pipeline()
    result = pipeline.process_frame(0)
    assert all(obj.confidence >= 0.3 for obj in result.objects)


@pytest.mark.requirement("REQ-01")
@pytest.mark.requirement("REQ-02")
def test_every_obstacle_has_a_finite_position():
    """REQ-01: the pipeline outputs obstacles from camera + radar.
    REQ-02: every obstacle has a valid position."""
    result = _make_pipeline().process_frame(1)
    assert result.objects
    assert all(math.isfinite(o.x) and math.isfinite(o.y) for o in result.objects)