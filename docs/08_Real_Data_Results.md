# Real-Data Results (nuScenes v1.0-mini)

## Setup

| Item | Value |
|---|---|
| Data | nuScenes v1.0-mini: 10 scenes, 404 samples (Boston, Singapore; urban, ≤ 55 km/h) |
| Radar | REAL (`RADAR_FRONT`), motion-compensated to the camera timestamp |
| Ground truth | REAL annotations, rules in [07_Ground_Truth_Rules.md](07_Ground_Truth_Rules.md) |
| Camera | **MODELED** (object-level model, no detector yet): nothing here validates the real camera |
| System | Default configuration (fusion version 3, see [04_Fusion_Design.md](04_Fusion_Design.md)) |
| Runner | `python -m src.test_harness.nuscenes_runner --split validate` |

## Method

- **Tune / validate split:** scenes sorted by name and alternated. Parameters were tuned on
  the 5 "tune" scenes only; the 5 "validate" scenes were used once, for the final check.
- **One match threshold (2 m) for every range.** With real clutter, a 5 m threshold let
  unrelated detections "find" a vehicle by chance (60-68 % below 80 m).
- **Chance level:** every range-band recall is also computed against the ground truth of an
  unrelated frame. It is reported next to the recall.
- **Confidence intervals (Wilson, 95 %) and a three-way verdict:** PASS only if the whole
  interval is above the target, FAIL if it is entirely below, INCONCLUSIVE otherwise.
  Observations repeat across frames (not independent): intervals are optimistic.

## Results (validate scenes, default configuration)

| Requirement | Target | Measured [95 % CI] (n) | Verdict |
|---|---|---|---|
| REQ-04 | radar alone, 120-180 m: recall > 0.5 | 0.667 [0.21-0.94] (n = 3) | INCONCLUSIVE |
| REQ-05 | system, 80-180 m: recall > 0.5 | 0.207 [0.13-0.31] (n = 82) | **FAIL** |
| REQ-08 | recall, vehicles < 30 m ≥ 0.90 | 0.783 [0.73-0.82] (n = 318) | **FAIL** |
| REQ-09 | precision ≥ 0.80 | 0.466 [0.44-0.49] | **FAIL** |
| REQ-10 | latency p95 ≤ 100 ms | 2.1 ms (fusion stage only) | PASS |

## What changed during tuning (validate scenes)

| Configuration | F1 | Precision | Recall < 30 m | Recall 80-180 m |
|---|---|---|---|---|
| Before (circle 3 m + 0.08 × range, every radar cluster kept) | 0.124 | 0.069 | 0.682 | 0.622 |
| **Default now** (ellipse 0.75 × 3 m, unconfirmed radar must move ≥ 5 m/s) | **0.520** | **0.466** | **0.783** | 0.207 |
| Camera alone (modeled, reference) | 0.623 | 0.701 | 0.811 | 0.000 |

On the tune scenes the default configuration reached F1 0.638 and precision 0.601: part of
the tuning fitted those scenes. The near-range recall generalised (0.786 → 0.783).

## Findings

1. **Synthetic results did not transfer.** Precision was 0.81 on the synthetic bench and
   0.075 with the real radar (all scenes, no tuning). The synthetic radar produced 3 clutter
   echoes per frame; the real one sends about 125 points per frame, 84 % of them static.
   Parameters tuned on the synthetic bench (range-dependent gate) degrade the real system.
2. **Radar quality filters are not the lever.** The strictest filter (nuScenes devkit
   default) raised precision only from 0.075 to 0.105 and cost 17 points of recall at 30-80 m.
3. **Unconfirmed radar clusters caused the false alarms:** 1.6 per frame with the camera
   alone, 34.5 with the fusion.
4. **Clutter beside a car captured its camera detection** and moved it. An elliptical gate
   (narrow across the line of sight) recovered 7.5 points of near-range recall.
5. **The radar sees far, the system discards it.** Radar alone detects 62 % of the vehicles
   at 80-120 m (chance level 1 %), but most are slow or stopped and the minimum-speed rule
   drops them with the clutter: 21 % after fusion.
6. **A generic score is not a requirement.** Ranking configurations by F1 would have
   removed every detection beyond 80 m (only 37 vehicles in the tune scenes).

## Decision

No configuration met REQ-05, REQ-08 and REQ-09 at the same time, even with a modeled
camera. The default configuration keeps long range (the radar's own capability) at the cost
of precision. The alternative (never keep unconfirmed radar objects) reached precision 0.76
on the tune scenes but detects nothing beyond 80 m, by design.

**Conclusion:** with the real radar, a single-frame architecture (radar clusters, no memory
between frames) cannot meet the requirements. This is an architecture finding, not a tuning
problem.

## Limitations

- Camera MODELED: its numbers are probably optimistic.
- Small sample at long range: 15 vehicles at 120-180 m in all of v1.0-mini (3 in validate).
- Operational design domain: urban only, ≤ 55 km/h, 6 children in the camera's field of view.
- Annotations at lidar time, frame at camera time: moving objects can be off by ~0.5 m.

## Next steps

1. **Tracking over time:** keep a static object if it reappears at the same place frame after
   frame (targets REQ-05 and REQ-09).
2. **Range-bearing fusion:** depth from the radar, direction from the camera.
3. **Real camera detector** (makes REQ-03 and REQ-06 testable, replaces the camera model).
4. **Calibrate the synthetic sensor models** against these measurements, so the synthetic
   bench becomes useful evidence again.
5. **nuScenes trainval** (about 85 times more data) for statistically meaningful long-range results.