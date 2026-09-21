"""Camera Perception: detects objects in a camera image.

For now this is a STUB that returns fake detections, so the full pipeline
can run end to end. The real detector (e.g. YOLO) will replace the internals
later, without changing this block's interface (encapsulation).
"""

from src.interfaces import CameraImage, DetectedObject

class CameraPerception:
    """Detects and classifies objects in a camera image.

    Input:  a CameraImage (raw pixels).
    Output: a list of DetectedObject (may be empty if nothing is detected).
    """

    def detect(self, image: CameraImage) -> list[DetectedObject]:
        """Detect objects in the given camera image.

        The returned objects carry the same timestamp as the input image,
        so they stay synchronized with the rest of the pipeline.

        Args:
            image: the camera frame to analyze.

        Returns:
            A list of DetectedObject. Empty if no object is detected.
        """
        # --- STUB: fake detections for now (real detector comes later) ---
        detections = [
            DetectedObject(
                object_class="car",
                x=15.0,
                y=1.5,
                velocity=-8.0,
                confidence=0.90,
                timestamp=image.timestamp,
            ),
            DetectedObject(
                object_class="pedestrian",
                x=8.0,
                y=-2.0,
                velocity=0.0,
                confidence=0.75,
                timestamp=image.timestamp,
            ),
        ]
        return detections