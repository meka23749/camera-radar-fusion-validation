# Ground Truth Rules (nuScenes)

nuScenes annotates every object around the vehicle (360°), in the global map frame,
with 23 categories. The system only looks ahead and only knows the REQ-06 classes.
This document defines which annotations the system is judged on, and why.
Implementation: `src/test_harness/nuscenes_ground_truth.py`.

Each annotation is either **evaluated** (missing it is a false negative) or
**ignored** (missing it is not a false negative, and a detection on it is not a
false positive).

## Rules

| Rule | Value | Source |
|---|---|---|
| Field of view | Inside the horizontal FOV of `CAM_FRONT` (64.6° in v1.0-mini), seen from the camera position | Computed from `calibrated_sensor` (fx = 1266 px, width = 1600 px); optical axis checked: [1.000, 0.006, -0.006] |
| Range | ≤ 180 m | System range (REQ-05) |
| Classes | See mapping below; other categories are ignored | REQ-06 (Fahrzeug / Fußgänger / Zweirad) |
| Visibility | Ignored if the annotation has no lidar AND no radar point | Same rule as the official nuScenes detection evaluation (`filter_eval_boxes` in `nuscenes/eval/common/loaders.py`) |

## Class mapping

| System class | REQ-06 | nuScenes categories | In FOV (v1.0-mini) |
|---|---|---|---|
| `car` | Fahrzeug | `vehicle.car` | 2140 |
| `truck` | Fahrzeug | `vehicle.truck`, `vehicle.bus.*`, `vehicle.construction`, `vehicle.trailer` | 430 |
| `cyclist` | Zweirad | `vehicle.motorcycle`, `vehicle.bicycle` | 223 |
| `pedestrian` | Fußgänger | `human.pedestrian.*` | 1095 |
| ignored | – | `movable_object.*`, `static_object.*` | 1133 |

`cyclist` means "two-wheeler" (motorcycles included).

## Measurements behind the rules (v1.0-mini, 404 samples)

- 18,538 annotations, 5,021 (27 %) inside the front camera FOV.
- Vehicles in the FOV without any lidar or radar point: 3 % (0-30 m), 16 % (30-50 m),
  35 % (50-80 m), 53 % (80-120 m), 63 % (120-180 m). These objects are annotated from
  the whole sequence, but no sensor measures them at that instant.
- Vehicles in the FOV without any radar point: 29 % already at 0-30 m (probably outside
  the narrower radar beam; to be checked).

## Known limitations

- **Timing:** annotations are given at the lidar timestamp, the frame at the camera
  timestamp (about 35 ms earlier, up to ~50 ms). Moving objects can be off by ~0.5 m.
- **Velocity:** annotation velocities are not computed (0.0); the validation does not use them.
- **Bike racks:** the official evaluation also ignores bicycles and motorcycles parked in
  a bike rack. This rule is not implemented (27 bike racks in the FOV).
- **Sample size:** only 40 vehicles between 120 and 180 m (about 15 with a sensor point),
  none beyond 180 m. Results for REQ-04 / REQ-05 at long range are not statistically
  meaningful on v1.0-mini; every result must be reported with its number of objects.
- **Coverage:** only 6 children in the FOV; urban scenes only, vehicle speed ≤ 55 km/h.