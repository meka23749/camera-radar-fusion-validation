"""Demo: run the full perception pipeline on synthetic frames."""

from src.perception.data_loader import DataLoader
from src.perception.camera_perception import CameraPerception
from src.perception.radar_processing import RadarProcessing
from src.perception.fusion import Fusion
from src.perception.output import Output
from src.perception.pipeline import PerceptionPipeline


def main():
    # Create all blocks (dependency injection)
    pipeline = PerceptionPipeline(
        data_loader=DataLoader(num_frames=3),
        camera_perception=CameraPerception(),
        radar_processing=RadarProcessing(),
        fusion=Fusion(distance_threshold=3.0),
        output=Output(confidence_threshold=0.3),
    )

    # Process each frame and print the detected obstacles
    for i in range(3):
        result = pipeline.process_frame(i)
        print(f"\n=== Frame {i} (timestamp {result.timestamp}) ===")
        print(f"  {len(result.objects)} obstacle(s) detected:")
        for obj in result.objects:
            print(
                f"   - {obj.object_class:12s} "
                f"at x={obj.x:5.1f} m, y={obj.y:5.1f} m, "
                f"v={obj.velocity:6.1f}, conf={obj.confidence:.2f}"
            )


if __name__ == "__main__":
    main()