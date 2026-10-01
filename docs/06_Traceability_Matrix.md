# Requirement ↔ Test Traceability Matrix

> The test lists in this table are checked automatically by `tests/test_traceability.py`:
> any test tagged with `@pytest.mark.requirement` must appear here, and vice versa.
> Levels and statuses are maintained by hand.

This matrix links each requirement to the automated test(s) that verify it, and to
its current status. It mirrors the traceability that tools like **DOORS** (requirements)
and **XRAY** (test management): every requirement must be covered by at least one test.

In this project, each verifying test is tagged in code with a pytest marker
(`@pytest.mark.requirement("REQ-XX")`), so the link between a requirement and its
test is explicit and machine-readable. Running `pytest -m "requirement" -v` lists
all requirement-linked tests.

---

## Verification levels

| Level | Meaning |
|---|---|
| **L1 - Logic** | A unit test proves that the mechanism behind the requirement works (e.g. the recall formula, the fusion merge rule). |
| **L2 - Synthetic SiL** | The system's behaviour is measured on synthetic scenarios with known ground truth. |
| **L3 - Real-data SiL** | The system's behaviour is measured on annotated nuScenes data. |

A requirement is only fully verified at L2 or L3. L1 proves the building blocks, not the system.

## Traceability matrix

| Requirement | Description | Mandatory | Verifying test(s) | Level | Status |
|---|---|---|---|---|---|
| REQ-01 | Detect obstacles from camera + radar | yes | `test_pipeline::test_every_obstacle_has_a_finite_position` | L1 | ✅ Logic verified |
| REQ-02 | Output position of each obstacle | yes | `test_pipeline::test_every_obstacle_has_a_finite_position` | L1 | ✅ Logic verified |
| REQ-03 | Camera detection range (≥ 80 m) | yes | - | - | ❌ Not covered (camera is a stub) |
| REQ-04 | Radar detection range (≥ 180 m) | yes | `test_l3_requirements::test_radar_range` (xfail) | L3 | ⚠️ Inconclusive (only 3 vehicles at 120-180 m in v1.0-mini validate) |
| REQ-05 | System range / camera-radar fusion | yes | `test_fusion::test_close_camera_and_radar_merge_into_one`, `test_l3_requirements::test_system_range` (xfail) | L3 | ❌ Fails on real data (0.21 at 80-180 m, n = 82) |
| REQ-06 | Output class of each obstacle | yes | `test_validation::test_class_aware_matching_rejects_wrong_class` | L1 | ⚠️ Class-aware metric only (classification not measured yet) |
| REQ-07 | Proximity warning | optional | - | - | Not implemented |
| REQ-08 | Recall ≥ 0.90 (vehicles < 30 m) | yes | `test_validation::test_missed_object_lowers_recall`, `test_validation::test_req08_scope_only_counts_vehicles_closer_than_30m`, `test_l3_requirements::test_recall_near_vehicles` (xfail) | L3 | ❌ Fails on real data (0.78, n = 318) |
| REQ-09 | Precision ≥ 0.80 | yes | `test_validation::test_invented_object_lowers_precision`, `test_output::test_low_confidence_objects_are_removed`, `test_l3_requirements::test_precision` (xfail) | L3 | ❌ Fails on real data (0.47) |
| REQ-10 | Latency ≤ 100 ms per frame | yes | `test_l3_requirements::test_latency` | L3 | ⚠️ Fusion stage only: 2.1 ms (no real detector yet) |
| REQ-11 | Read nuScenes data | | `test_nuscenes_loader::test_frames_follow_the_scene_order`, `test_nuscenes_loader::test_real_dataset_loads` | L3 | ✅ Verified (all 404 samples of v1.0-mini) |
| REQ-12 | Camera/radar synchronization (≤ 100 ms apart, radar motion-compensated to camera time) | | `test_data_loader::test_camera_and_radar_are_synchronized`, `test_camera_perception::test_detections_carry_image_timestamp`, `test_radar_processing::test_detections_carry_frame_timestamp`, `test_fusion::test_detections_from_another_frame_are_rejected`, `test_nuscenes_loader::test_measurements_too_far_apart_are_rejected` | L1 | ✅ Logic verified (offsets on real data: max 72 ms) |
| REQ-13 | Structured, machine-readable output | | - | - | ❌ Not covered (no export format) |
| REQ-14 | Every mandatory requirement has a test | | `test_traceability::test_matrix_lists_exactly_the_tagged_tests`, `test_traceability::test_every_mandatory_requirement_has_a_test` | Process | ⚠️ Checked automatically; known gap: REQ-03 |
| REQ-15 | Tests run in CI/CD | | `.github/workflows/tests.yml` | Process | ✅ Verified |
| REQ-16 | Reproducible, documented results | | `test_data_loader::test_same_frame_is_reproducible`, `test_sil_validation::test_runner_is_reproducible`, `test_sil_validation::test_runner_is_reproducible_across_processes`, `test_sil_validation::test_report_contains_all_verdicts` | L2 | ✅ Verified (seeded runs, identical across processes, generated report) |

---

## Coverage summary

- **Verified on real data (L3):** REQ-11, REQ-10 (fusion stage only)
- **Failing on real data (L3):** REQ-05, REQ-08, REQ-09 - see `docs/08_Real_Data_Results.md`
- **Inconclusive (L3):** REQ-04 - too few far vehicles in v1.0-mini
- **Logic verified (L1):** REQ-01, REQ-02, REQ-12, REQ-16
- **Partially covered:** REQ-06 (metric only)
- **Not covered (mandatory):** REQ-03 (needs a real camera detector)

> L3 results: nuScenes v1.0-mini, validate scenes (never used for tuning), real radar,
> real ground truth, modeled camera. The synthetic bench (`test_sil_validation.py`) is a
> regression test of the fusion logic only: its sensor models are not calibrated against
> real sensors, so its verdicts are not requirement evidence.

---

## How the traceability is maintained

1. Each requirement has a unique ID in [01_Requirements.md](01_Requirements.md).
2. Each verifying test is tagged with `@pytest.mark.requirement("REQ-XX")`.
3. `pytest -m "requirement" -v` reports all requirement-linked tests.
4. `tests/test_traceability.py` checks on every run that the test lists in this matrix match
   the tags in the code, and that every mandatory requirement has a test (known gap: REQ-03).
5. Verification levels and statuses need engineering judgment and are updated by hand.

