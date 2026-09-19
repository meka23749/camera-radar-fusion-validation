"""Data interfaces exchanged between the perception and validation blocks.

This module defines the data contracts of the system (see docs/03_Design.md).
It contains no processing logic - only the structures passed between blocks.
"""

from dataclasses import dataclass, field
import numpy as np

@dataclass
class CameraImage:
    """Raw camera output for one frame (input of Camera Perception)."""
    pixels: np.ndarray          # the raw image, shape (H, W, 3)
    timestamp: float            # acquisition time of the frame
    camera_id: str              # which camera (e.g. "front")

@dataclass
class RadarPoint:
    """A single radar echo."""
    x: float                    # longitudinal position (distance ahead)
    y: float                    # lateral position (left/right)
    velocity: float             # relative velocity (Doppler)

@dataclass
class RadarPoints:
    """Raw radar output for one frame (input of Radar Processing)."""
    points: list[RadarPoint] = field(default_factory=list)
    timestamp: float = 0.0

@dataclass
class DetectedObject:
    """An obstacle produced by perception (output of the perception blocks)."""
    object_class: str           # class of the object: "car", "pedestrian", ...
    x: float                    # longitudinal position (distance ahead)
    y: float                    # lateral position (left/right)
    velocity: float             # relative velocity
    confidence: float           # detection confidence, 0.0 to 1.0
    timestamp: float            # which frame this object belongs to

@dataclass
class ObstacleList:
    """The system output for one frame: all detected obstacles."""
    objects: list[DetectedObject] = field(default_factory=list)
    timestamp: float = 0.0

@dataclass
class GroundTruthObject:
    """A reference object from human annotation (nuScenes ground truth).

    Same as DetectedObject but WITHOUT a confidence score: annotations are
    asserted as true, not predicted.
    """
    object_class: str           # annotated class
    x: float                    # longitudinal position
    y: float                    # lateral position
    velocity: float             # annotated velocity
    timestamp: float            # which frame this object belongs to

