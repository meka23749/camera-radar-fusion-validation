# System Architecture

**Project:** Camera–Radar Fusion for Obstacle Detection - SiL Validation on nuScenes
**Author:** Steve Meka
**Version:** 0.1 (Draft)


---

## 1. Overview

The architecture is split into two clearly separated parts:

- **System Under Test (SUT):** the perception system itself : it turns raw sensor
  data into a structured obstacle list.
- **Test Harness:** the validation environment : it compares the SUT output against
  ground truth and computes metrics. It is **not** part of the embedded system; it
  is a development/validation tool.

This separation mirrors real ADAS development: the perception software runs in the
vehicle, while validation runs offline against annotated data.

---

## 2. Block diagram

```
                    SYSTEM UNDER TEST (perception)
   ┌───────────────────────────────────────────────────────────────┐
   │                                                                 │
   │                 ┌─────────────────────┐                         │
   │            ┌───▶│  Camera Perception  │────┐                    │
   │            │    └─────────────────────┘    │                    │
   │  ┌─────────────┐                       ┌────▼──────┐   ┌───────┐ │
   │  │ Data Loader │                       │  Fusion   │──▶│ Output│─┼──┐
   │  └─────────────┘                       └────▲──────┘   └───────┘ │  │
   │            │    ┌─────────────────────┐    │                    │  │
   │            └───▶│   Radar Processing  │────┘                    │  │
   │                 └─────────────────────┘                         │  │
   └───────────────────────────────────────────────────────────────┘  │
                                                                        │
   ┌───────────────────────────────────────────────────────────────┐  │
   │                      TEST HARNESS (validation)                  │  │
   │   ┌──────────────────┐        ┌──────────────────────────┐     │  │
   │   │  Ground Truth     │        │       Validation         │◀────┼──┘
   │   │  (nuScenes annot.)│───────▶│  (recall/precision/lat.) │     │
   │   └──────────────────┘        └────────────┬─────────────┘     │
   │                                             ▼                   │
   │                                   ┌──────────────────┐          │
   │                                   │  Metrics Report  │          │
   │                                   └──────────────────┘          │
   └───────────────────────────────────────────────────────────────┘
```

---

## 3. Components

### System Under Test

| Block | Responsibility | Input | Output |
|---|---|---|---|
| **Data Loader** | Read nuScenes data and provide time-synchronized frames | nuScenes files | Camera image + radar points (same timestamp) |
| **Camera Perception** | Detect and classify objects in the image | Camera image | Image-based detections (class, image position) |
| **Radar Processing** | Extract targets from radar points | Radar points | Radar targets (distance, velocity) |
| **Fusion** | Combine camera and radar into one reliable obstacle list | Camera detections + radar targets | Unified obstacle list |
| **Output** | Produce the structured result and optional proximity flag | Unified obstacle list | Obstacle list (class, position, velocity); warning flag |

### Test Harness (separate)

| Block | Responsibility | Input | Output |
|---|---|---|---|
| **Ground Truth** | Provide human-annotated reference objects | nuScenes annotations | Reference obstacle list |
| **Validation** | Compare SUT output vs ground truth, measure performance | SUT output + ground truth | Recall, precision, latency |
| **Metrics Report** | Present results reproducibly | Metrics | Report (files/logs) |

---

## 4. Data flow (per frame)

1. **Data Loader** reads one synchronized frame (image + radar points) from nuScenes.
2. **Camera Perception** and **Radar Processing** run on their respective inputs.
3. **Fusion** merges both into a single obstacle list.
4. **Output** formats the result (and sets the proximity flag if applicable).
5. **Validation** (test harness) compares the Output against the **Ground Truth**
   for that frame and updates the metrics.
6. **Metrics Report** aggregates results over all frames.

---

## 5. Time synchronization (rationale)

The **Data Loader** must deliver camera and radar data from the *same timestamp*.
Fusion is only meaningful if both sensors describe the same scene at the same
moment; otherwise the ego vehicle and other objects have moved between the two
readings. This directly supports **REQ-12**.

---

## 6. Requirement ↔ block traceability

| Requirement | Covered by block(s) |
|---|---|
| REQ-01 Detection | Camera Perception, Radar Processing, Fusion |
| REQ-02 Position output | Fusion, Output |
| REQ-03 Camera range (80 m) | Camera Perception |
| REQ-04 Radar range (180 m) | Radar Processing |
| REQ-05 System range | Fusion |
| REQ-06 Classification | Camera Perception, Output |
| REQ-07 Proximity warning (optional) | Output |
| REQ-08 Recall | Validation |
| REQ-09 Precision | Validation |
| REQ-10 Latency | Validation |
| REQ-11 Read nuScenes | Data Loader |
| REQ-12 Synchronization | Data Loader |
| REQ-13 Structured output | Output |
| REQ-14 Requirement ↔ test traceability | Validation (+ test suite) |
| REQ-15 CI/CD execution | Test Harness (CI pipeline) |
| REQ-16 Reproducible results | Metrics Report |

---

## 7. Notes

- The perception blocks (Camera, Radar, Fusion) are the **system under test**; they
  could be replaced by any other perception implementation without changing the
  test harness.
- The test harness is the **primary engineering contribution** of this project:
  a reproducible, requirement-based validation pipeline.
