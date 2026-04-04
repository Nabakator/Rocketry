# DRIFT

`DRIFT` stands for `Deployment and Recovery Integrated Flight Tool`.

This folder is the self-contained home of the active recovery-systems application inside the Rocketry umbrella repository.

## Overview

DRIFT is a desktop application for amateur rocketry recovery-system design and first-order recovery analysis.

It exists because recovery work is usually treated as a sub-feature of a broader simulator, while recovery design often needs a faster and more focused workflow. DRIFT is intended to cover recovery-specific sizing, checks, comparison, and reporting without trying to replace a full flight simulator.

Within Rocketry, the repository is organized by engineering domain first. DRIFT is the active tool inside the `recovery-systems` domain and is intended to remain self-contained so future recovery tools can live alongside it cleanly.

## Current MVP capabilities

The current implementation supports:

- a PySide6 desktop shell for project, configuration, analysis, comparison, and export workflows
- project save and load using versioned JSON project files
- single and dual deployment workflows
- parachute sizing with safety margin and local catalogue matching
- standard atmosphere density plus manual density override
- constant-wind and two-layer wind models
- first-order descent-time and drift estimation
- deterministic validation before analysis
- deterministic engineering warnings based on analysed results
- side-by-side comparison of two saved configurations within a project
- trajectory-style recovery schematic and event timeline views driven by analysed model state
- Markdown export of configuration assumptions and analysis results

## Non-goals and current limits

DRIFT currently does not try to be:

- a full powered-flight simulator
- a propulsion or aerodynamic-stability simulator
- a high-fidelity opening-load or transient recovery dynamics tool
- a live supplier, stock, or lead-time integration tool
- a PDF reporting tool

The current visuals are engineering schematics, not high-fidelity trajectory plots.
They intentionally prioritise readable phase ordering and recovery sequence over physical scale.

## Quickstart

From the repository root:

Requirements:

- Python `3.11` or newer
- a local virtual environment is recommended
- `PySide6` is installed through the DRIFT package dependencies

```bash
cd recovery-systems/drift
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -e .
drift
```

This installs DRIFT in editable mode and launches the desktop shell.

You can also launch it with the module entry point:

```bash
python3 -m drift
```

The desktop title bar uses the current project, file name where available, and the installed DRIFT version tag.

To run the full test suite:

```bash
PYTHONPATH=src python3 -m unittest
```

## Testing

From the DRIFT tool root:

- full test suite: `PYTHONPATH=src python3 -m unittest`
- acceptance suite only: `PYTHONPATH=src python3 -m unittest tests.acceptance.test_acceptance_suite`
- UI smoke tests: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src python3 -m unittest tests.unit.test_ui_smoke`

Notes:

- the UI smoke tests require `PySide6` to be installed
- `QT_QPA_PLATFORM=offscreen` is useful in headless environments and CI-like local runs

## Tool structure

Core files and folders:

- `pyproject.toml`
  - Python project configuration for DRIFT
- `src/drift/`
  - active application package
  - `core/`: SI-only engineering calculations
  - `models/`: persistence-facing domain models
  - `services/`: validation, analysis, comparison, export, and visualisation orchestration
  - `ui/`: PySide6 desktop shell, panels, and schematic widgets
- `data/`
  - local curated parachute catalogue used by DRIFT
- `tests/`
  - unit and acceptance coverage for the engineering core, services, and UI smoke checks
- `docs/`
  - MVP and schema notes

## Development workflow

For contributors:

- keep engineering formulas in `src/drift/core/`
- keep orchestration and model-to-model workflows in `src/drift/services/`
- keep persistence-facing structures in `src/drift/models/`
- keep PySide6 widget and presentation code in `src/drift/ui/`
- keep recovery-schematic geometry rules in the visualisation layer, not in the analysis engine
- do not move engineering formulas into widgets
- changes are not considered complete until the test suite passes

The UI should bind to models and call services. It should not duplicate validation, analysis, or warning logic.

## Data and catalogue

`data/parachute_catalogue.json` stores the local curated parachute catalogue used by the MVP.

The catalogue is used for nominal-size matching after sizing calculations. It is local and deterministic by design, and does not depend on any live supplier integration.

## Documentation

The `docs/` folder holds project notes that define the current MVP contract:

- `docs/design-spec.md`
  - desktop UI design direction and component-level presentation guidance
- `docs/mvp-spec.md`
  - high-level MVP scope and implementation direction
- `docs/json-schema.md`
  - project-file and catalogue schema notes

## Repository Context

- DRIFT is the active implementation for the `recovery-systems` domain.
- It is intended to remain self-contained so future sibling tools can live alongside it under the same domain.
- The Rocketry repository is an umbrella repo and may contain other domains such as propulsion in the future.

## Status

DRIFT is the active recovery-systems tool in Rocketry and is currently at MVP / early-stage status.

The architecture, validation, engineering core, warnings, persistence, comparison, visuals, and Markdown export are implemented. Future work should build on this structure rather than reintroducing tool logic at the repository root.

The current desktop UI includes the shared theme system, custom top bar and state badge, redesigned left/centre/right panels, and a trajectory-style recovery schematic.

The current recovery schematic is a non-scale engineering sketch that shows ascent separately from recovery descent, includes visible horizontal drift, and distinguishes drogue and main descent segments where applicable.
