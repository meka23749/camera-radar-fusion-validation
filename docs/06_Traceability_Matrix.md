# Requirement ↔ Test Traceability Matrix

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
| REQ-04 | Radar detection range (≥ 180 m) | yes | - | - | ❌ Not covered (no range limit in radar processing) |
| REQ-05 | System range / camera-radar fusion | yes | `test_fusion::test_close_camera_and_radar_merge_into_one` | L1 | ⚠️ Fusion logic only (range not measured) |
| REQ-06 | Output class of each obstacle | yes | - | - | ❌ Not covered (classification not validated) |
| REQ-07 | Proximity warning | optional | - | - | Not implemented |
| REQ-08 | Recall ≥ 0.90 (vehicles < 30 m) | yes | `test_validation::test_missed_object_lowers_recall` | L1 | ⚠️ Metric only (system not measured yet) |
| REQ-09 | Precision ≥ 0.80 | yes | `test_validation::test_invented_object_lowers_precision`, `test_output::test_low_confidence_objects_are_removed` | L1 | ⚠️ Metric + filter only (system not measured yet) |
| REQ-10 | Latency ≤ 100 ms per frame | yes | - | - | ❌ Not covered (no measurement) |
| REQ-11 | Read nuScenes data | | - | - | ❌ Not implemented (synthetic loader) |
| REQ-12 | Camera/radar synchronization | | `test_data_loader::test_camera_and_radar_are_synchronized`, `test_camera_perception::test_detections_carry_image_timestamp`, `test_radar_processing::test_detections_carry_frame_timestamp` | L1 | ✅ Logic verified |
| REQ-13 | Structured, machine-readable output | | - | - | ❌ Not covered (no export format) |
| REQ-14 | Every mandatory requirement has a test | | this matrix | Process | ❌ Not met (REQ-03, 04, 06, 10 uncovered) |
| REQ-15 | Tests run in CI/CD | | `.github/workflows/tests.yml` | Process | ✅ Verified |
| REQ-16 | Reproducible, documented results | | `test_data_loader::test_same_frame_is_reproducible` | L1 | ⚠️ Partial (inputs reproducible, no results report yet) |

---

## Coverage summary

- **Logic verified (L1):** REQ-01, REQ-02, REQ-12
- **Partially covered (L1 only):** REQ-05, REQ-08, REQ-09, REQ-16
- **Not covered (mandatory):** REQ-03, REQ-04, REQ-06, REQ-10
- **No requirement is verified at system level (L2/L3) yet.** This is the next milestone.

---

## How the traceability is maintained

1. Each requirement has a unique ID in [01_Requirements.md](01_Requirements.md).
2. Each verifying test is tagged with `@pytest.mark.requirement("REQ-XX")`.
3. `pytest -m "requirement" -v` reports all requirement-linked tests.
4. This matrix is updated whenever a requirement or its verification changes.

