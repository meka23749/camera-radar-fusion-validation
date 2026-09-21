# Camera-Radar Fusion for Obstacle Detection - SiL Validation on nuScenes

A camera–radar perception system that detects, classifies and localizes obstacles
in front of the ego vehicle, validated as **Software-in-the-Loop (SiL)** against the
annotated real-world **nuScenes** dataset.

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
- **Sensor & perception:** camera-based detection, radar point processing, camera–radar fusion
- **Validation:** automated measurement of recall, precision and latency against ground truth
- **CI/CD:** automated build and test execution on every commit
- **Reproducibility:** containerized, deterministic runs on recorded data

---

## Approach

The system is validated on recorded, human-annotated data from nuScenes:

1. Raw sensor data (camera images + radar points) is replayed from nuScenes
2. The perception pipeline produces a list of detected obstacles
3. Detections are compared against the human **ground-truth annotations**
4. Metrics (recall, precision, latency) are computed and reported automatically

This mirrors the **SiL (Software-in-the-Loop)** replay approach used in industry.

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
├── docs/
│   └── 01_Requirements.md      # Requirements specification
├── src/                        # Perception & fusion source code
├── tests/                      # Automated, requirement-based tests
├── .github/workflows/          # CI/CD pipeline
└── README.md
```

---

## Documentation

- [Requirements Specification](docs/01_Requirements.md)
- [System Architecture (Capella / MBSE)](docs/02_Architecture.md)
- [Detailed Design](docs/03_Design.md)
- [Fusion – Detailed Design](docs/04_Fusion_Design.md)
- [Git Workflow](docs/05_Git_Workflow.md)

---

## Status

🚧 Work in progress — see [documentation](docs/) for the current state.

---

## Author

**Steve Meka** — B.Eng. Technische Informatik
[stevkmef.com](https://stevkmef.com)
