# DRIFT

`DRIFT` stands for `Deployment and Recovery Integrated Flight Tool`.

This folder is the self-contained home of the active recovery-systems application inside the GU Rocketry umbrella repository.

## Tool Structure

- `pyproject.toml`
  - Python project configuration for DRIFT
- `src/drift/`
  - active application package
- `data/`
  - local curated parachute catalogue used by DRIFT
- `tests/`
  - unit and acceptance coverage
- `docs/`
  - MVP and schema notes

## Run And Test

- run tests: `PYTHONPATH=src python3 -m unittest`
- run UI smoke tests offscreen with local PySide6: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 -m unittest tests.unit.test_ui_smoke`

## Repository Context

- DRIFT is the active implementation for the `recovery-systems` domain.
- It is intended to remain self-contained so future sibling tools can live alongside it under the same domain.
