"""Tests for the synthetic scenario generator and sensor models.

These tests check the TEST TOOLS, not the system under test.
They are deliberately NOT tagged with requirement IDs.
"""

from src.test_harness.scenario import ScenarioGenerator, CameraModel, RadarModel
from src.interfaces import GroundTruthObject


def test_same_seed_gives_same_scenario():
    a = ScenarioGenerator(seed=3, num_frames=20)
    b = ScenarioGenerator(seed=3, num_frames=20)
    assert a.ground_truth(19) == b.ground_truth(19)


def test_different_seeds_give_different_scenarios():
    a = ScenarioGenerator(seed=3, num_frames=5)
    b = ScenarioGenerator(seed=4, num_frames=5)
    assert a.ground_truth(0) != b.ground_truth(0)


def test_objects_move_with_their_velocity():
    s = ScenarioGenerator(seed=0, num_frames=2, dt=0.1)
    first, second = s.ground_truth(0)[0], s.ground_truth(1)[0]
    if first.object_class == second.object_class:          # not respawned
        assert abs(second.x - (first.x + first.velocity * 0.1)) < 1e-9


def test_ground_truth_carries_frame_timestamp():
    s = ScenarioGenerator(seed=0, num_frames=5, dt=0.1)
    assert all(o.timestamp == s.timestamp(3) for o in s.ground_truth(3))

def test_camera_model_sees_nothing_beyond_its_range():
    far = [GroundTruthObject("car", 100.0, 0.0, 0.0, 1.0),
           GroundTruthObject("car", 150.0, 2.0, 0.0, 1.0)]
    camera = CameraModel(fp_per_frame=0.0)
    assert all(camera.observe(far, 1.0) == [] for _ in range(50))


def test_radar_model_sees_nothing_beyond_its_range():
    far = [GroundTruthObject("car", 190.0, 0.0, 0.0, 1.0)]
    radar = RadarModel(clutter_per_frame=0.0)
    assert all(radar.observe(far, 1.0).points == [] for _ in range(50))


def test_radar_model_gives_several_echoes_per_vehicle():
    car = [GroundTruthObject("car", 50.0, 0.0, -5.0, 1.0)]
    radar = RadarModel(p_detect=1.0, clutter_per_frame=0.0)
    counts = [len(radar.observe(car, 1.0).points) for _ in range(50)]
    assert max(counts) >= 2