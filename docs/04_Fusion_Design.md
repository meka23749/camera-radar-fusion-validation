# Fusion - Detailed Design
---

## 1. Why this component has a dedicated design document

Most blocks in this system are simple input→output transformations and are
documented by their code docstrings. The **Fusion** block is different: it
contains real decision logic (data association, matching threshold, merge rules).
Such logic deserves an explicit, visible design - not only code.

---

## 2. Problem

The camera and the radar can detect the **same real object**. If their detections
are simply concatenated, one real car would appear **twice** in the output (once
from the camera, once from the radar), which is wrong and unsafe.

The Fusion block must therefore:
1. **Associate** detections that describe the same real object, and
2. **Merge** them into a single obstacle, keeping the best of each sensor.

---

## 3. Association rule (which detections are the same object)

Two detections are considered the **same object** when:

- they belong to the **same frame** (same timestamp), and
- they are **close in space** — the Euclidean distance between them in the (x, y)
  plane is below a fixed **distance threshold** (default: **3.0 m**).

The timestamp groups detections by instant; the spatial proximity identifies the
object within that instant. This is a simple form of **data association**.

> **Why a threshold?** Camera and radar never report exactly the same position for
> the same object (e.g. 14 m vs 15 m). A tolerance is needed. 3.0 m is small enough
> to avoid merging two distinct objects, large enough to absorb normal sensor
> disagreement. It is a tunable parameter, not a hard-coded constant.

---

## 4. Merge rule (how to combine two matched detections)

When a camera detection is matched to a radar detection, the merged object takes:

| Field | Source | Reason |
|---|---|---|
| object_class | **Camera** | radar cannot classify objects |
| x, y (position) | **Radar** | radar gives accurate distance |
| velocity | **Radar** | radar measures velocity directly (Doppler) |
| confidence | max(camera, radar) | keep the more optimistic score |
| timestamp | frame timestamp | keep synchronization |

This reflects each sensor's strength: the **camera knows *what*** it is, the
**radar knows *where* and *how fast*** it is.

---

## 5. Unmatched detections

- A **camera** detection with no nearby radar → kept as-is (the camera saw
  something the radar missed).
- A **radar** detection with no nearby camera → kept as-is, class stays
  `"unknown"` (radar detected something, but cannot classify it).

Nothing is dropped: fusion improves the result, it does not discard information.

---

## 6. Algorithm (flowchart)



---

## 7. Design decisions & trade-offs

- **Greedy nearest-match association.** For each camera detection, the closest
  unused radar detection within the threshold is chosen. Simple and fast; good
  enough for a first version. A more advanced approach (global optimal assignment,
  e.g. Hungarian algorithm) could replace it later without changing the block's
  interface.
- **Fixed threshold.** Kept constant for simplicity; exposed as a parameter so it
  can be tuned or made adaptive later.
- **Radar drives position, camera drives class.** Deliberate: plays to each
  sensor's strength.
- **No information dropped.** Unmatched detections from both sensors are preserved.

---

## 8. Requirement traceability

| Requirement | How Fusion addresses it |
|---|---|
| REQ-05 (system range) | combines camera and radar coverage into one list |
| REQ-02 (position output) | outputs position for every obstacle |
| REQ-06 (classification) | class taken from the camera when available |
| REQ-12 (synchronization) | only detections of the same timestamp are fused |
