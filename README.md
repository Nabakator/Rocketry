# GU Rocketry

GU Rocketry is the umbrella repository for rocketry software and analysis tools, organized by engineering domain first and then by tool.

## Repository Structure

- `recovery-systems/`
  - recovery-system tools and analyses
  - active tool: `recovery-systems/drift/`
- `propulsion/`
  - reserved for future propulsion tools

## Active Tool

- `recovery-systems/drift/`
  - `DRIFT` (`Deployment and Recovery Integrated Flight Tool`)
  - desktop PySide6 application for recovery-system design, analysis, comparison, visuals, and Markdown export

## Notes

- The repository root provides umbrella metadata such as `LICENSE` and `.gitignore`.
- Individual tools should remain self-contained inside their domain folders.
- Local virtual environments such as `.venv/` are ignored and are not part of the tracked source tree.
