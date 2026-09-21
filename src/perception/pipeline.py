"""Perception Pipeline: connects all blocks into one end-to-end chain.

For each frame: Data Loader -> Camera Perception + Radar Processing
-> Fusion -> Output -> final ObstacleList.

Blocks are injected from outside (dependency injection), so they can be
replaced (e.g. real YOLO instead of the stub) or mocked in tests without
changing this pipeline.
"""

from src.interfaces import ObstacleList

class PerceptionPipeline:
    """Runs the full perception chain for a given frame."""

    def __init__(self, data_loader, camera_perception, radar_processing, fusion, output):
        """Create the pipeline with its building blocks.

        Args:
            data_loader: provides synchronized camera + radar frames.
            camera_perception: detects objects in the camera image.
            radar_processing: extracts objects from radar points.
            fusion: merges camera and radar detections.
            output: filters and finalizes the obstacle list.
        """
        self._data_loader = data_loader
        self._camera_perception = camera_perception
        self._radar_processing = radar_processing
        self._fusion = fusion
        self._output = output

    def process_frame(self, index: int) -> ObstacleList:
        """Run the full perception chain for one frame.

        Steps:
            1. Data Loader     -> camera image + radar points (synchronized)
            2. Camera / Radar  -> detections from each sensor
            3. Fusion          -> merged obstacle list
            4. Output          -> filtered final obstacle list

        Args:
            index: the frame number to process.

        Returns:
            The final ObstacleList for that frame.
        """
        # 1. Get synchronized sensor data
        camera_image, radar_points = self._data_loader.get_frame(index)

        # 2. Run each sensor's perception
        camera_detections = self._camera_perception.detect(camera_image)
        radar_detections = self._radar_processing.process(radar_points)

        # 3. Fuse the two detection lists
        fused = self._fusion.fuse(
            camera_detections,
            radar_detections,
            timestamp=camera_image.timestamp,
        )

        # 4. Finalize (filter low-confidence obstacles)
        final = self._output.finalize(fused)

        return final