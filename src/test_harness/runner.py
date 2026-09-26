"""SiL validation runner: scenario -> system under test -> metrics -> verdicts -> report.

Usage:
    python -m src.test_harness.runner --seed 42 --frames 300 --out reports

Writes reports/validation_report.json and reports/validation_report.md and
exits with code 1 if a requirement fails (usable as a CI quality gate).
"""

import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path

from src.perception.radar_processing import RadarProcessing
from src.perception.fusion import Fusion
from src.perception.output import Output
from src.test_harness.scenario import ScenarioGenerator, CameraModel, RadarModel, VEHICLES
from src.test_harness.validation import Validation, aggregate

TARGETS = {"REQ-08": 0.90, "REQ-09": 0.80, "REQ-10": 100.0}


def run(seed: int = 42, frames: int = 300, fusion=None, radar_processing=None, output=None) -> dict:
    """Run the system under test on a synthetic scenario and evaluate it."""
    # --- Scenario + sensor models (the "world" and the "sensors") ---
    scenario = ScenarioGenerator(seed=seed, num_frames=frames)
    camera = CameraModel(seed=seed + 1)
    radar = RadarModel(seed=seed + 2)

    # --- System under test (can be replaced to compare versions) ---
    radar_processing = radar_processing or RadarProcessing()
    fusion = fusion or Fusion(distance_threshold=3.0)
    output = output or Output(confidence_threshold=0.3)

    # --- Validation ---
    val = Validation(distance_threshold=2.0, class_aware=True)
    val_far = Validation(distance_threshold=5.0, class_aware=True)   # looser at long range

    overall, req08, far = [], [], []
    latencies_ms = []

    for k in range(scenario.num_frames()):
        t = scenario.timestamp(k)
        gt = scenario.ground_truth(k)
        cam_dets = camera.observe(gt, t)
        radar_pts = radar.observe(gt, t)

        start = time.perf_counter()                     # REQ-10: time only the SUT
        radar_dets = radar_processing.process(radar_pts)
        final = output.finalize(fusion.fuse(cam_dets, radar_dets, t))
        latencies_ms.append((time.perf_counter() - start) * 1000.0)

        overall.append(val.evaluate(final, gt, max_range=80.0))
        req08.append(val.evaluate(final, gt, classes=VEHICLES, max_range=30.0))
        far_gt = [g for g in gt if g.object_class in VEHICLES and 80.0 <= math.hypot(g.x, g.y) < 180.0]
        far.append(val_far.evaluate(final, far_gt))

    r_all, r08, r_far = aggregate(overall), aggregate(req08), aggregate(far)
    p95 = sorted(latencies_ms)[int(0.95 * (len(latencies_ms) - 1))]

    def verdict(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    return {
        "config": {"seed": seed, "frames": frames,
                   "data": "synthetic scenario (object-level sensor models)"},
        "metrics": {
            "overall_<80m": vars(r_all),
            "vehicles_<30m": vars(r08),
            "vehicles_80-180m_recall": r_far.recall,
            "latency_ms": {"mean": statistics.mean(latencies_ms), "p95": p95, "max": max(latencies_ms)},
        },
        "requirements": {
            "REQ-05": {"target": "vehicles 80-180 m detected (recall > 0.5)",
                       "measured": round(r_far.recall, 3), "verdict": verdict(r_far.recall > 0.5)},
            "REQ-08": {"target": f">= {TARGETS['REQ-08']}",
                       "measured": round(r08.recall, 3), "verdict": verdict(r08.recall >= TARGETS["REQ-08"])},
            "REQ-09": {"target": f">= {TARGETS['REQ-09']}",
                       "measured": round(r_all.precision, 3), "verdict": verdict(r_all.precision >= TARGETS["REQ-09"])},
            "REQ-10": {"target": f"p95 <= {TARGETS['REQ-10']} ms (fusion stage, dev CPU)",
                       "measured": round(p95, 3), "verdict": verdict(p95 <= TARGETS["REQ-10"])},
        },
    }


def to_markdown(report: dict) -> str:
    """Format a report as a Markdown table (for humans and the CI summary)."""
    c = report["config"]
    lines = [
        "# SiL Validation Report", "",
        f"Data: {c['data']} - seed `{c['seed']}` - {c['frames']} frames", "",
        "| Requirement | Target | Measured | Verdict |",
        "|---|---|---|---|",
    ]
    for req, r in report["requirements"].items():
        icon = "✅" if r["verdict"] == "PASS" else "❌"
        lines.append(f"| {req} | {r['target']} | {r['measured']} | {icon} {r['verdict']} |")
    o = report["metrics"]["overall_<80m"]
    lat = report["metrics"]["latency_ms"]
    lines += [
        "", "## Details", "",
        f"- Overall (< 80 m): TP={o['true_positives']} FP={o['false_positives']} "
        f"FN={o['false_negatives']}, recall={o['recall']:.3f}, precision={o['precision']:.3f}",
        f"- Latency: mean={lat['mean']:.3f} ms, p95={lat['p95']:.3f} ms, max={lat['max']:.3f} ms",
        "",
        "> Synthetic sensor models validate the fusion logic only. "
        "REQ-03 / REQ-04 (sensor ranges) require real nuScenes data.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run the SiL validation on a synthetic scenario.")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--frames", type=int, default=300)
    parser.add_argument("--out", default="reports")
    args = parser.parse_args(argv)

    report = run(seed=args.seed, frames=args.frames)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "validation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (out / "validation_report.md").write_text(to_markdown(report), encoding="utf-8")
    print(to_markdown(report))

    all_pass = all(r["verdict"] == "PASS" for r in report["requirements"].values())
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())