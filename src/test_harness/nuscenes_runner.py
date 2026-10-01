"""Semi-real SiL validation on nuScenes: REAL radar + REAL ground truth, MODELED camera.

There is no camera detector yet (step 12), so the camera detections still come
from the object-level CameraModel, applied to the real ground truth. Everything
radar-related is real: points, clutter, mounting, timing, ego motion.

    What this run CAN tell:     radar range (REQ-04), real clutter vs precision
                                (REQ-09), radar-camera fusion on real geometry.
    What it CANNOT tell:        anything about the real camera (REQ-03, REQ-06).

Every metric is reported with n (number of ground-truth objects) and a 95 %
confidence interval. Every recall in a range band also shows its CHANCE LEVEL:
the recall the same detections reach against the ground truth of an unrelated
frame. With dense radar clutter this is far from zero. A verdict is PASS only if the whole interval is above the
target, FAIL if it is entirely below, INCONCLUSIVE otherwise. Caveat: the same
object appears in consecutive frames, so observations are not independent and
the intervals are optimistic (too narrow).

Usage (needs NUSCENES_ROOT):
    python -m src.test_harness.nuscenes_runner --radar-filter none --out reports/nuscenes
"""

import argparse
import json
import math
import os
import statistics
import sys
import time
from pathlib import Path

from src.interfaces import ObstacleList
from src.perception.fusion import Fusion
from src.perception.nuscenes_loader import NuScenesLoader, RADAR_FILTERS
from src.perception.output import Output
from src.perception.radar_processing import RadarProcessing
from src.test_harness.nuscenes_ground_truth import NuScenesGroundTruth
from src.test_harness.scenario import CameraModel, VEHICLES
from src.test_harness.validation import Validation, aggregate

RADAR_BANDS = [(0, 30), (30, 80), (80, 120), (120, 180)]
MATCH_THRESHOLD = 2.0      # m, for every range (see explore_chance measurements)


def wilson_interval(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95 % confidence interval of a proportion k/n (Wilson score interval)."""
    if n == 0:
        return 0.0, 1.0
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, centre - half), min(1.0, centre + half)


def verdict(k: int, n: int, target: float) -> str:
    low, high = wilson_interval(k, n)
    if low >= target:
        return "PASS"
    if high < target:
        return "FAIL"
    return "INCONCLUSIVE"


def _stat(k: int, n: int) -> dict:
    low, high = wilson_interval(k, n)
    return {"value": round(k / n, 3) if n else None, "k": k, "n": n,
            "ci95": [round(low, 3), round(high, 3)]}


def _in_band(objects, lo, hi, classes=VEHICLES):
    return [o for o in objects if o.object_class in classes and lo <= math.hypot(o.x, o.y) < hi]


def run_nuscenes(root, radar_filter: str = "none", seed: int = 42, max_frames: int | None = None,
                 radar_processing=None, fusion=None, output=None) -> dict:
    loader = NuScenesLoader(root, radar_filter=radar_filter)
    ground_truth = NuScenesGroundTruth(root)
    camera = CameraModel(seed=seed)                    # MODELED camera (no detector yet)
    radar_processing = radar_processing or RadarProcessing()
    fusion = fusion or Fusion()
    output = output or Output(confidence_threshold=0.3)
    # One threshold for every range: with real clutter, a 5 m threshold lets
    # unrelated detections "find" a vehicle by chance (measured: 60-68 % < 80 m).
    val = Validation(distance_threshold=MATCH_THRESHOLD, class_aware=True)

    overall, req08 = [], []
    frames = []                                        # (system, radar_only, evaluated gt) per frame
    latencies_ms = []
    n_frames = loader.num_frames() if max_frames is None else min(max_frames, loader.num_frames())

    for i in range(n_frames):
        frame = loader.get_frame(i)
        gt = ground_truth.get(frame)
        token = frame.sample_token
        cam_dets = camera.observe(gt.evaluated, frame.timestamp)

        start = time.perf_counter()                    # REQ-10: time only the system
        radar_dets = radar_processing.process(frame.radar)
        final = output.finalize(fusion.fuse(cam_dets, radar_dets, frame.timestamp))
        latencies_ms.append((time.perf_counter() - start) * 1000.0)

        # Evaluation region = the region of the ground truth (camera field of view)
        def in_region(objects):
            return ObstacleList([o for o in objects if ground_truth.in_field_of_view(token, o.x, o.y)],
                                frame.timestamp)

        system, radar_only = in_region(final.objects), in_region(radar_dets)
        overall.append(val.evaluate(system, gt.evaluated, ignored=gt.ignored))
        req08.append(val.evaluate(system, gt.evaluated, classes=VEHICLES, max_range=30.0,
                                  ignored=gt.ignored))
        frames.append((system, radar_only, gt.evaluated))

    def band_recall(band, detections_of, gt_of):
        """Recall of vehicles in a range band. gt_of(i) picks the ground truth for frame i."""
        lo, hi = band
        return aggregate(val.evaluate(detections_of(i), _in_band(gt_of(i), lo, hi))
                         for i in range(len(frames)))

    # Chance level: same detections, ground truth of an UNRELATED frame (half the
    # dataset away, i.e. another scene). Any recall measured this way is coincidence.
    def real_gt(i):
        return frames[i][2]

    def other_gt(i):
        return frames[(i + len(frames) // 2) % len(frames)][2]

    def radar_of(i):
        return frames[i][1]

    def system_of(i):
        return frames[i][0]

    def recall_counts(r):
        return r.true_positives, r.true_positives + r.false_negatives

    def precision_counts(r):
        return r.true_positives, r.true_positives + r.false_positives

    def with_chance(detections_of, band):
        stat = _stat(*recall_counts(band_recall(band, detections_of, real_gt)))
        stat["chance"] = _stat(*recall_counts(band_recall(band, detections_of, other_gt)))
        return stat

    r_all, r08 = aggregate(overall), aggregate(req08)
    r_far = band_recall((80, 180), system_of, real_gt)
    far_radar = band_recall((120, 180), radar_of, real_gt)
    p95 = sorted(latencies_ms)[int(0.95 * (len(latencies_ms) - 1))]
    return {
        "config": {
            "data": "nuScenes v1.0-mini: REAL radar + REAL ground truth, MODELED camera",
            "radar_filter": radar_filter, "seed": seed, "frames": n_frames,
            "match_threshold_m": MATCH_THRESHOLD,
        },
        "metrics": {
            "precision_overall": _stat(*precision_counts(r_all)),
            "recall_overall": _stat(*recall_counts(r_all)),
            "recall_vehicles_<30m": _stat(*recall_counts(r08)),
            "recall_vehicles_80-180m_fused": with_chance(system_of, (80, 180)),
            "radar_only_recall_vehicles": {f"{lo}-{hi} m": with_chance(radar_of, (lo, hi))
                                           for lo, hi in RADAR_BANDS},
            "latency_ms": {"mean": statistics.mean(latencies_ms), "p95": p95},
        },
        "requirements": {
            "REQ-04": {"target": "radar alone, vehicles 120-180 m: recall > 0.5",
                       "verdict": verdict(*recall_counts(far_radar), 0.5)},
            "REQ-05": {"target": "fused system, vehicles 80-180 m: recall > 0.5",
                       "verdict": verdict(*recall_counts(r_far), 0.5)},
            "REQ-08": {"target": "recall, vehicles < 30 m >= 0.90",
                       "verdict": verdict(*recall_counts(r08), 0.90)},
            "REQ-09": {"target": "precision >= 0.80",
                       "verdict": verdict(*precision_counts(r_all), 0.80)},
            "REQ-10": {"target": "p95 <= 100 ms (fusion stage)",
                       "verdict": "PASS" if p95 <= 100.0 else "FAIL"},
        },
    }


def to_markdown(report: dict) -> str:
    c, m = report["config"], report["metrics"]

    def fmt(s):
        if s["n"] == 0:
            return "n = 0"
        text = f"{s['value']:.3f} [{s['ci95'][0]:.2f}-{s['ci95'][1]:.2f}] (n = {s['n']})"
        if "chance" in s and s["chance"]["n"]:
            text += f" - chance level {s['chance']['value']:.3f}"
        return text

    lines = [
        "# Semi-real SiL report (nuScenes)", "",
        f"{c['data']}  ",
        f"radar filter `{c['radar_filter']}`, seed {c['seed']}, {c['frames']} frames, "
        f"match threshold {c['match_threshold_m']} m", "",
        "| Metric | Value [95 % CI] (n) |", "|---|---|",
        f"| Precision, all classes | {fmt(m['precision_overall'])} |",
        f"| Recall, all classes | {fmt(m['recall_overall'])} |",
        f"| Recall, vehicles < 30 m | {fmt(m['recall_vehicles_<30m'])} |",
        f"| Recall, vehicles 80-180 m (fused) | {fmt(m['recall_vehicles_80-180m_fused'])} |",
    ]
    for band, s in m["radar_only_recall_vehicles"].items():
        lines.append(f"| Radar alone, vehicles {band} | {fmt(s)} |")
    lines += [f"| Latency p95 | {m['latency_ms']['p95']:.2f} ms |", "",
              "| Requirement | Target | Verdict |", "|---|---|---|"]
    for req, r in report["requirements"].items():
        lines.append(f"| {req} | {r['target']} | {r['verdict']} |")
    lines += ["", "> Camera detections are MODELED: nothing here validates the real camera.",
              "> Observations repeat across frames (not independent): intervals are optimistic.",
              "> Chance level = recall of the same detections against an unrelated frame's ground truth."]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Semi-real SiL validation on nuScenes.")
    parser.add_argument("--root", default=os.environ.get("NUSCENES_ROOT"))
    parser.add_argument("--radar-filter", default="none", choices=sorted(RADAR_FILTERS))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-frames", type=int, default=None)
    parser.add_argument("--out", default="reports/nuscenes")
    args = parser.parse_args(argv)
    if not args.root:
        parser.error("set NUSCENES_ROOT or pass --root")

    report = run_nuscenes(args.root, args.radar_filter, args.seed, args.max_frames)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    name = f"nuscenes_{args.radar_filter}"
    (out / f"{name}.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out / f"{name}.md").write_text(to_markdown(report), encoding="utf-8")
    print(to_markdown(report))
    return 1 if any(r["verdict"] == "FAIL" for r in report["requirements"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())