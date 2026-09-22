# Requirement ↔ Test Traceability Matrix

This matrix links each requirement to the automated test(s) that verify it, and to
its current status. It mirrors the traceability that tools like **DOORS** (requirements)
and **XRAY** (test management): every requirement must be covered by at least one test.

In this project, each verifying test is tagged in code with a pytest marker
(`@pytest.mark.requirement("REQ-XX")`), so the link between a requirement and its
test is explicit and machine-readable. Running `pytest -m "requirement" -v` lists
all requirement-linked tests.

---

## Traceability matrix

| Requirement | Description | Verifying test(s) | Status |
|---|---|---|---|
| REQ-03 | Camera detection range (≥ 80 m) | `test_camera_perception::test_detect_returns_a_list` | ✅ Verified |
| REQ-04 | Radar detection range (≥ 180 m) | `test_radar_processing::test_each_point_becomes_a_detection` | ✅ Verified |
| REQ-05 | System range / camera-radar fusion | `test_fusion::test_close_camera_and_radar_merge_into_one` | ✅ Verified |
| REQ-08 | Recall ≥ 0.90 (vehicles < 30 m) | `test_validation::test_missed_object_lowers_recall` | ✅ Verified |
| REQ-09 | Precision (limit false positives) | `test_validation::test_invented_object_lowers_precision`, `test_output::test_low_confidence_objects_are_removed` | ✅ Verified |
| REQ-10 | Latency ≤ 100 ms per frame | *(measurement planned)* | Pending |
| REQ-12 | Camera/radar synchronization | `test_data_loader::test_camera_and_radar_are_synchronized`, `test_camera_perception::test_detections_carry_image_timestamp`, `test_radar_processing::test_detections_carry_frame_timestamp` | ✅ Verified |

---

## Coverage summary

- **Requirements with at least one verifying test:** REQ-03, REQ-04, REQ-05, REQ-08, REQ-09, REQ-12
- **Pending:** REQ-10 (latency measurement to be added)
- All verifying tests currently **pass** (see CI status in the README badge).

---

## How the traceability is maintained

1. Each requirement has a unique ID in [01_Requirements.md](01_Requirements.md).
2. Each verifying test is tagged with `@pytest.mark.requirement("REQ-XX")`.
3. `pytest -m "requirement" -v` reports all requirement-linked tests.
4. This matrix is updated whenever a requirement or its verification changes.

