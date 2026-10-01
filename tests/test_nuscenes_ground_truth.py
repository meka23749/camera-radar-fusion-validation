"""Tests for the nuScenes ground truth (src/test_harness/nuscenes_ground_truth.py).

The hand-made dataset (tests/nuscenes_fixture.py) contains one annotation per
rule: an object behind the vehicle, one outside the field of view, a traffic
cone, an object no sensor sees, one beyond 180 m, and objects that must be kept.
These tests check a TEST TOOL, so they are not tagged with requirement IDs.
"""

import math
import os

import pytest

from src.perception.nuscenes_loader import NuScenesLoader
from src.test_harness.nuscenes_ground_truth import NuScenesGroundTruth, map_category
from tests.nuscenes_fixture import make_dataset, ANNOTATIONS_S1


@pytest.fixture
def dataset(tmp_path):
    root = make_dataset(tmp_path, ego_shift=0.0)
    return NuScenesLoader(root), NuScenesGroundTruth(root)


@pytest.mark.parametrize("name, expected", [
    ("vehicle.car", "car"),
    ("vehicle.truck", "truck"),
    ("vehicle.bus.bendy", "truck"),
    ("vehicle.construction", "truck"),
    ("vehicle.motorcycle", "cyclist"),
    ("vehicle.bicycle", "cyclist"),
    ("human.pedestrian.adult", "pedestrian"),
    ("human.pedestrian.construction_worker", "pedestrian"),
    ("movable_object.barrier", None),
    ("static_object.bicycle_rack", None),
    ("vehicle.carriage", None),          # a prefix must match a whole name part
])
def test_category_mapping(name, expected):
    assert map_category(name) == expected


def test_each_rule_keeps_or_ignores_the_right_objects(dataset):
    loader, ground_truth = dataset
    gt = ground_truth.get(loader.get_frame(0))
    kept = {(o.object_class, round(o.x, 6), round(o.y, 6)) for o in gt.evaluated}
    expected = {(cls, x, y) for _, _, x, y, _, _, cls in ANNOTATIONS_S1 if cls != "ignored"}
    assert kept == expected
    assert len(gt.ignored) == sum(a[-1] == "ignored" for a in ANNOTATIONS_S1)


def test_positions_are_in_the_vehicle_frame(dataset):
    """The car at global x = 130 m is 30 m ahead of the vehicle (at global x = 100 m)."""
    loader, ground_truth = dataset
    car = next(o for o in ground_truth.get(loader.get_frame(0)).evaluated if o.object_class == "car")
    assert (car.x, car.y) == pytest.approx((30.0, 2.0))


def test_annotations_belong_to_their_own_sample(dataset):
    loader, ground_truth = dataset
    frame = loader.get_frame(1)
    gt = ground_truth.get(frame)
    assert [(o.object_class, o.x) for o in gt.evaluated] == [("car", pytest.approx(50.0))]
    assert all(o.timestamp == frame.timestamp for o in gt.evaluated)


def test_field_of_view_comes_from_the_calibration(dataset):
    """fx = 1266 px, width = 1600 px -> half FOV = atan(800 / 1266) = 32.3 deg."""
    loader, ground_truth = dataset
    token = loader.get_frame(0).sample_token

    def point_at(angle_deg, dist=50.0):
        a = math.radians(angle_deg)
        return 1.7 + dist * math.cos(a), dist * math.sin(a)      # seen from the camera

    assert ground_truth.in_field_of_view(token, *point_at(31.0))
    assert ground_truth.in_field_of_view(token, *point_at(-31.0))
    assert not ground_truth.in_field_of_view(token, *point_at(34.0))


@pytest.mark.skipif("NUSCENES_ROOT" not in os.environ, reason="nuScenes data not available")
def test_real_ground_truth_is_consistent():
    """Every annotation ends up in exactly one list; evaluated objects are in front."""
    loader = NuScenesLoader(os.environ["NUSCENES_ROOT"])
    ground_truth = NuScenesGroundTruth(os.environ["NUSCENES_ROOT"])
    total = evaluated = 0
    for i in range(loader.num_frames()):
        gt = ground_truth.get(loader.get_frame(i))
        total += len(gt.evaluated) + len(gt.ignored)
        evaluated += len(gt.evaluated)
        assert all(o.x > 0 for o in gt.evaluated)
        assert {o.object_class for o in gt.evaluated} <= {"car", "truck", "cyclist", "pedestrian"}
    assert total == 18538
    assert evaluated > 0