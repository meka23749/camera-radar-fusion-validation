"""Tests for the synthetic scenario generator and sensor models.

These tests check the TEST TOOLS, not the system under test.
They are deliberately NOT tagged with requirement IDs.
"""

from src.test_harness.scenario import ScenarioGenerator


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