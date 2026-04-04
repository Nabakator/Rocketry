# GU Rocketry

This repository now treats DRIFT as the active recovery-systems application.

`DRIFT` stands for `Deployment and Recovery Integrated Flight Tool`. The canonical implementation lives under `src/drift/`.

## Active Implementation

- `src/drift/`
  - active DRIFT application package
  - canonical implementation for recovery-system modeling, analysis, warnings, comparison, visuals, and Markdown export
- `data/`
  - local curated parachute catalogue used by DRIFT
- `tests/`
  - unit and acceptance coverage for DRIFT
- `docs/`
  - DRIFT MVP and schema notes

## Prototype Archive

- `recovery-systems/parachute-area/`
  - archived prototype/reference-only parachute sizing tool
  - not the active implementation path
  - retained for historical reference only

## Verification Status

Current DRIFT verification baseline:

- command: `PYTHONPATH=src python3 -m unittest`
- result: `39` tests passed
- note: `2` Qt smoke checks are skipped when `PySide6` is not installed in the local environment

## Repository Notes

- The top-level `README.md`, `LICENSE`, and `.gitignore` are the authoritative repository metadata.
- DRIFT under `src/drift/` is the default target for new development.
- Local virtual environments such as `.venv/` are ignored and are not part of the tracked source tree.
