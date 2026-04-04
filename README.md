# GU Rocketry

GU Rocketry is the umbrella repository for rocketry software and analysis tools, organized by engineering domain first and then by tool.

## Overview

This repository is intended to hold multiple engineering tools that support different parts of amateur rocketry work.

The organizing rule is:

- first by domain
- then by tool within that domain

That keeps each tool self-contained and avoids mixing tool-specific `src/`, `tests/`, `docs/`, and data folders at the repository root.

## Current repository structure

- `recovery-systems/`
  - recovery-system tools and analyses
  - active tool: `recovery-systems/drift/`
- `propulsion/`
  - reserved for future propulsion tools

## Active tool

- `recovery-systems/drift/`
  - `DRIFT` (`Deployment and Recovery Integrated Flight Tool`)
  - desktop PySide6 application for recovery-system design, analysis, comparison, visuals, and Markdown export

## What lives here today

At the moment, the active implemented tool in this repository is DRIFT under `recovery-systems/drift/`.

DRIFT covers recovery-system work such as:

- project save and load
- single and dual deployment workflows
- parachute sizing
- drift and descent-time estimation
- validation and deterministic warnings
- comparison, visuals, and Markdown export

Tool-specific setup, testing, and usage instructions should live in the tool’s own README rather than being duplicated in detail at the repository root.

## Repository conventions

- keep the repository root limited to umbrella metadata and navigation
- keep each tool self-contained inside its domain folder
- keep tool-specific dependencies, tests, docs, and data with that tool
- avoid reintroducing tool-specific app code directly at the repository root

## Working in this repository

If you are working on the active recovery tool:

```bash
cd recovery-systems/drift
```

From there, use the DRIFT-specific README for setup, running, and testing.

If future domains are added, they should follow the same pattern:

- `domain-name/tool-name/`
- self-contained project layout inside the tool root

## Notes

- The repository root provides umbrella metadata such as `LICENSE` and `.gitignore`.
- Individual tools should remain self-contained inside their domain folders.
- Local virtual environments such as `.venv/` are ignored and are not part of the tracked source tree.

## Status

GU Rocketry is currently structured as a multi-domain umbrella repository with DRIFT as the active implemented tool under `recovery-systems/`.
