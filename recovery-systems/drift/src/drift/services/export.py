"""Markdown export service for DRIFT engineering summaries."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from drift.formatting import (
    format_density,
    format_length,
    format_mass,
    format_time,
    format_velocity,
)
from drift.models import CatalogueItem, Configuration


def render_configuration_markdown(
    *,
    project_name: str,
    configuration: Configuration,
    catalogue_items: Sequence[CatalogueItem],
) -> str:
    """Render one configuration as deterministic Markdown."""

    catalogue_by_id = {item.item_id: item for item in catalogue_items}
    unit_system = configuration.display_unit_system
    analysis = configuration.analysis_results
    atmosphere = configuration.atmosphere_settings
    wind = configuration.wind_settings

    lines = [
        f"# {project_name}",
        "",
        "## Configuration",
        f"- Name: {configuration.configuration_name}",
        f"- Recovery mode: {configuration.recovery_mode}",
        f"- Display units: {configuration.display_unit_system}",
        f"- Rocket mass: {format_mass(configuration.rocket_mass_kg, unit_system)}",
        f"- Safety margin: {configuration.safety_margin_fraction:.3f}",
        f"- Analysis status: {'analysed' if analysis is not None else 'draft / not analysed'}",
        "",
        "## Assumptions",
        f"- Basis label: {analysis.recovery_basis_label if analysis is not None else 'N/A'}",
        f"- Atmosphere mode: {atmosphere.mode}",
        (
            f"- Manual density override: {format_density(atmosphere.manual_density_kg_per_m3, unit_system)}"
            if atmosphere.manual_density_kg_per_m3 is not None
            else "- Manual density override: inactive"
        ),
        f"- Wind mode: {wind.mode}",
    ]

    if wind.mode == "constant":
        lines.append(
            f"- Constant wind: {format_velocity(wind.constant_wind_mps, unit_system)}"
        )
    else:
        lines.append(f"- Aloft wind: {format_velocity(wind.aloft_wind_mps, unit_system)}")
        lines.append(f"- Ground wind: {format_velocity(wind.ground_wind_mps, unit_system)}")

    lines.extend(
        [
            "",
            "## Parachutes",
            "| Role | Family | Cd | Cd Source | Theoretical Diameter | Recommended Diameter | Catalogue Item | Selected Diameter | Resulting Descent Velocity |",
            "| --- | --- | ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for parachute in configuration.parachutes:
        selected_item = catalogue_by_id.get(parachute.selected_catalogue_item_id or "")
        lines.append(
            "| "
            + " | ".join(
                [
                    parachute.role,
                    parachute.family,
                    f"{parachute.cd:.3f}",
                    parachute.cd_source,
                    format_length(parachute.theoretical_diameter_m, unit_system),
                    format_length(parachute.recommended_diameter_m, unit_system),
                    selected_item.product_name if selected_item is not None else "N/A",
                    format_length(parachute.selected_nominal_diameter_m, unit_system),
                    format_velocity(parachute.resulting_descent_velocity_mps, unit_system),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Phase Summaries",
        ]
    )
    if analysis is None:
        lines.append("- Not analysed.")
    else:
        lines.extend(
            [
                "| Phase | Start Altitude | End Altitude | Velocity | Duration | Drift |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for phase in analysis.phase_summaries:
            lines.append(
                "| "
                + " | ".join(
                    [
                        phase.phase_name,
                        format_length(phase.start_altitude_m, unit_system),
                        format_length(phase.end_altitude_m, unit_system),
                        format_velocity(phase.nominal_descent_velocity_mps, unit_system),
                        format_time(phase.estimated_duration_s),
                        format_length(phase.estimated_drift_m, unit_system),
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Totals",
            f"- Total descent time: {format_time(analysis.total_descent_time_s if analysis is not None else None)}",
            f"- Total estimated drift: {format_length(analysis.total_estimated_drift_m if analysis is not None else None, unit_system)}",
            "",
            "## Warnings",
        ]
    )
    if not configuration.warnings:
        lines.append("- None.")
    else:
        lines.extend(
            [
                "| Code | Severity | Message | Source |",
                "| --- | --- | --- | --- |",
            ]
        )
        for warning in configuration.warnings:
            lines.append(
                "| "
                + " | ".join(
                    [
                        warning.code,
                        warning.severity,
                        warning.message.replace("\n", " "),
                        warning.source_field or "N/A",
                    ]
                )
                + " |"
            )

    return "\n".join(lines) + "\n"


def save_configuration_markdown(
    *,
    project_name: str,
    configuration: Configuration,
    catalogue_items: Sequence[CatalogueItem],
    path: str | Path,
) -> Path:
    """Save one configuration export as Markdown."""

    file_path = Path(path)
    if file_path.suffix.lower() != ".md":
        file_path = file_path.with_suffix(".md")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        render_configuration_markdown(
            project_name=project_name,
            configuration=configuration,
            catalogue_items=catalogue_items,
        ),
        encoding="utf-8",
    )
    return file_path


__all__ = ["render_configuration_markdown", "save_configuration_markdown"]
