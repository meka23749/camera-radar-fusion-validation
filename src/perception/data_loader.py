"""Data Loader: provides synchronized camera and radar frames.

For now it produces SYNTHETIC data (random image, fake radar points) so the
rest of the pipeline can be built and tested without nuScenes. The real
nuScenes reading will replace the internals later, without changing this
block's interface (encapsulation).
"""

import numpy as np
from src.interfaces import CameraImage, RadarPoint, RadarPoints

class DataLoader:
    """Provides camera + radar frames, synchronized by timestamp.

    Frames are accessed by index (frame 0, 1, 2, ...). This makes each
    frame reproducible, which is important for testing.
    """

    def __init__(self, num_frames: int = 10):
        """Create a loader with a fixed number of (synthetic) frames.

        Args:
            num_frames: how many frames this loader can provide.
        """
        self._num_frames = num_frames

    def num_frames(self) -> int:
        """Return the total number of available frames."""
        return self._num_frames

    
    def get_frame(self, index: int) -> tuple[CameraImage, RadarPoints]:
        """Return the synchronized camera image and radar points for frame `index`.

        Both outputs share the same timestamp, so they describe the same
        scene at the same moment (REQ-12).

        Args:
            index: frame number, from 0 to num_frames() - 1.

        Returns:
            A tuple (camera_image, radar_points) for that frame.

        Raises:
            IndexError: if index is out of range.
        """
        if index < 0 or index >= self._num_frames:
            raise IndexError(f"Frame index {index} out of range (0..{self._num_frames - 1})")

        # Same timestamp for both sensors → synchronization (REQ-12)
        timestamp = float(index)

        # --- Synthetic camera image (random pixels for now) ---
        pixels = np.random.randint(0, 256, size=(900, 1600, 3), dtype=np.uint8)
        camera_image = CameraImage(pixels=pixels, timestamp=timestamp, camera_id="front")

        # --- Synthetic radar points (a few fake echoes for now) ---
        points = [
            RadarPoint(x=10.0, y=1.0, velocity=-5.0),
            RadarPoint(x=25.0, y=-2.0, velocity=-12.0),
            RadarPoint(x=40.0, y=0.0, velocity=0.0),
        ]
        radar_points = RadarPoints(points=points, timestamp=timestamp)

        return camera_image, radar_points