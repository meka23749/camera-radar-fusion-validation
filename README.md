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
- **Validation:** automated measurement of recall, precision and latency against ground truth
- **CI/CD:** automated build and test execution on every commit
- **Reproducibility:** seeded, deterministic runs and generated validation report (containerization planned)

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
- **Perception:** camera object detection, radar point processing, sensor fusion
- **Data:** nuScenes (mini split for development)
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
- [Traceability Matrix](docs/06_Traceability_Matrix.md)

---

## Quick start

```bash
pip install -r requirements.txt
pytest                                                   # unit + SiL tests
python -m src.test_harness.runner --seed 42 --frames 300 # validation report -> reports/
```

## Status

First system-level results (synthetic SiL, seed 42, 300 frames):

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

---

## Author

**Steve Meka** — B.Eng. Technische Informatik
[stevkmef.com](https://stevkmef.com)
