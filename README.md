# Camera-Radar Fusion for Obstacle Detection - Requirements-Based SiL Validation

![Tests](https://github.com/meka23749/camera-radar-fusion-validation/actions/workflows/tests.yml/badge.svg)

A camera–radar perception system that detects, classifies and localizes obstacles
in front of the ego vehicle, validated as **Software-in-the-Loop (SiL)**: first on
seeded synthetic scenarios with known ground truth, next on the annotated real-world
**nuScenes** dataset.

> **Focus of this project:** this is primarily a **validation engineering** project.
> The perception algorithm (camera detection + radar processing + fusion) is the
> *system under test*; the core deliverable is a reproducible validation pipeline
> with traceable requirements, automated metrics and CI/CD.

---

## Motivation

In real ADAS development, most of the engineering effort goes into **testing and
validating** perception software, not only into building it. This project reproduces
that workflow end to end on a small scale: from requirements, through system
architecture, to an automated, requirements-based validation pipeline.

**System scope:** perception only (detection, classification, localization).
Decision/actuation (braking, steering) is explicitly out of scope.

---

## What this project demonstrates

- **Systems engineering:** a formal requirements specification and requirement ↔ test traceability
- **Sensor & perception:** radar echo clustering and camera–radar fusion (camera detector: stub, real detector planned)
- **Validation:** automated measurement of recall, precision and latency against ground truth, with a PASS/FAIL verdict per requirement
- **CI/CD:** every push and pull request runs unit, SiL and traceability tests; the validation report is published in the CI job summary
- **Reproducibility:** seeded runs with identical results across processes and machines, checked by a dedicated test (containerization planned)

---

## Approach

The validation loop runs in two stages:

1. **Synthetic SiL (implemented):** a seeded scenario generator creates moving actors
   with exact ground truth. Object-level camera and radar models reproduce typical
   sensor weaknesses (depth error, limited range, multiple radar echoes, clutter).
   This validates the **fusion logic**, not the sensors themselves.
2. **Real-data SiL (next milestone):** camera images and radar points are replayed
   from nuScenes and compared against the human ground-truth annotations.

In both stages, the system output is compared against ground truth, and recall,
precision and latency are computed and checked against the requirements automatically.

---

## Tech stack

- **Language:** Python (core), C++ (performance-critical module — planned)
- **Perception:** radar echo clustering, camera–radar fusion with optimal (Hungarian) association; camera detector planned
- **Data:** seeded synthetic scenarios (current), nuScenes mini split (next)
- **Testing:** pytest, requirement-based test cases
- **CI/CD:** GitHub Actions
- **Architecture modeling:** Capella / SysML (MBSE)

---

## Repository structure

```
.
├── docs/                       # Requirements, architecture, design, traceability matrix
├── src/
│   ├── perception/             # System under test: data loading, radar processing, fusion
│   └── test_harness/           # Scenarios, sensor models, validation metrics, SiL runner
├── tests/                      # Unit tests and requirement-based SiL tests
├── .github/workflows/          # CI pipeline
└── README.md
```

---

## Documentation

- [Requirements Specification](docs/01_Requirements.md)
- [System Architecture (Capella / MBSE)](docs/02_Architecture.md)
- [Detailed Design](docs/03_Design.md)
- [Fusion – Detailed Design](docs/04_Fusion_Design.md)
- [Git Workflow](docs/05_Git_Workflow.md)
- [Ground Truth Rules (nuScenes)](docs/07_Ground_Truth_Rules.md)
- [Traceability Matrix](docs/06_Traceability_Matrix.md)

---

## Quick start

```bash
pip install -r requirements.txt
pytest                                                   # unit + SiL tests
python -m src.test_harness.runner --seed 42 --frames 300 # validation report -> reports/
```

## Status

Current results (synthetic SiL, seed 42, 300 frames - identical on Linux CI and Windows):

| Requirement | Target | Measured | Verdict |
|---|---|---|---|
| REQ-05 - far vehicles (80-180 m) detected | recall > 0.5 | 0.83 | ✅ |
| REQ-08 - recall, vehicles < 30 m | ≥ 0.90 | 0.92 | ✅ small margin, monitored |
| REQ-09 - precision | ≥ 0.80 | 0.81 | ✅ small margin, monitored |
| REQ-10 - latency (fusion stage) | ≤ 100 ms | < 1 ms | ✅ |

The validation pipeline found real defects and measured each fix:

| Version | Precision (REQ-09) | Recall < 30 m (REQ-08) |
|---|---|---|
| Initial | 0.50 ❌ | 0.97 |
| + radar echo clustering | 0.76 ❌ | 0.93 |
| + optimal association, range-dependent gate | 0.81 ✅ | 0.92 |

Not yet covered: sensor ranges (REQ-03, REQ-04) need real data; the camera detector
is a stub. See the [Traceability Matrix](docs/06_Traceability_Matrix.md) for the
verification level of each requirement.

## What the validation found

Each defect below was found by the validation pipeline itself, reproduced with a test,
then fixed in its own commit:

| Finding | How it was found | Fix |
|---|---|---|
| Traceability matrix claimed requirements were verified by tests that could not fail | Asked of every test: "would it fail if the requirement were violated?" | Honest verification levels (L1 / L2 / L3) |
| Synthetic camera frames were different on every run | Same frame requested twice | Seeded per frame index |
| Metrics ignored classes and depended on list order | Hand-built counter-examples | Class-aware, confidence-ordered matching; scoped, micro-averaged metrics |
| Precision 0.50: each radar echo became its own object | First SiL run, then a single-car experiment | Radar echo clustering |
| Fusion depended on list order; fixed 3 m gate split far objects in two (46 % at 75 m) | Order and range experiments | Hungarian association, range-dependent gate |
| Timestamps documented as checked, but never checked | Fused a detection from another frame | `SynchronizationError` (REQ-12) |
| Metrics varied slightly between runs and machines | Same seed, different `PYTHONHASHSEED` | Deterministic ordering, cross-process test |
| Hand-maintained matrix drifted from the code | Automatic comparison with test tags | Matrix checked on every test run |

## Next steps

1. **nuScenes loader (REQ-11):** replay real camera and radar data, with nearest-timestamp
   matching and ego-motion compensation (camera ~12 Hz, radar ~13 Hz).
2. **Real camera detector:** pixel boxes projected to metres using nuScenes calibration,
   which makes REQ-03 testable.
3. **Metrics per range bin and per class**, and a Docker image for fully reproducible runs.

---

---

## Author

**Steve Meka** - B.Eng. Technische Informatik
[stevkmef.com](https://stevkmef.com)
