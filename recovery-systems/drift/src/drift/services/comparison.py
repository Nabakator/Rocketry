"""Comparison helpers for side-by-side DRIFT configuration review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from drift.formatting import format_length, format_time, format_velocity
from drift.models import CatalogueItem, Configuration, ParachuteSpec

ROLE_ORDER = {"single": 0, "drogue": 1, "main": 2}


@dataclass(slots=True, frozen=True)
class ComparisonRow:
    """One deterministic side-by-side comparison row."""

    metric: str
    value_a: str
    value_b: str


def build_comparison_rows(
    configuration_a: Configuration,
    configuration_b: Configuration,
    catalogue_items: Sequence[CatalogueItem],
    *,
    unit_system: str,
) -> list[ComparisonRow]:
    """Build deterministic comparison rows for two configurations."""

    catalogue_by_id = {item.item_id: item for item in catalogue_items}
    return [
        ComparisonRow("Recovery mode", configuration_a.recovery_mode, configuration_b.recovery_mode),
        ComparisonRow(
            "Parachute family",
            _format_parachutes(configuration_a, lambda parachute: parachute.family),
            _format_parachutes(configuration_b, lambda parachute: parachute.family),
        ),
        ComparisonRow(
            "Theoretical diameter",
            _format_parachutes(
                configuration_a,
                lambda parachute: format_length(parachute.theoretical_diameter_m, unit_system),
                require_analysis=True,
            ),
            _format_parachutes(
                configuration_b,
                lambda parachute: format_length(parachute.theoretical_diameter_m, unit_system),
                require_analysis=True,
            ),
        ),
        ComparisonRow(
            "Recommended diameter",
            _format_parachutes(
                configuration_a,
                lambda parachute: format_length(parachute.recommended_diameter_m, unit_system),
                require_analysis=True,
            ),
            _format_parachutes(
                configuration_b,
                lambda parachute: format_length(parachute.recommended_diameter_m, unit_system),
                require_analysis=True,
            ),
        ),
        ComparisonRow(
            "Selected catalogue item",
            _format_parachutes(
                configuration_a,
                lambda parachute: _catalogue_name(parachute, catalogue_by_id),
                require_analysis=True,
            ),
            _format_parachutes(
                configuration_b,
                lambda parachute: _catalogue_name(parachute, catalogue_by_id),
                require_analysis=True,
            ),
        ),
        ComparisonRow(
            "Selected nominal diameter",
            _format_parachutes(
                configuration_a,
                lambda parachute: format_length(parachute.selected_nominal_diameter_m, unit_system),
                require_analysis=True,
            ),
            _format_parachutes(
                configuration_b,
                lambda parachute: format_length(parachute.selected_nominal_diameter_m, unit_system),
                require_analysis=True,
            ),
        ),
        ComparisonRow(
            "Resulting descent velocity",
            _format_parachutes(
                configuration_a,
                lambda parachute: format_velocity(
                    parachute.resulting_descent_velocity_mps,
                    unit_system,
                ),
                require_analysis=True,
            ),
            _format_parachutes(
                configuration_b,
                lambda parachute: format_velocity(
                    parachute.resulting_descent_velocity_mps,
                    unit_system,
                ),
                require_analysis=True,
            ),
        ),
        ComparisonRow(
            "Total descent time",
            _format_total_time(configuration_a),
            _format_total_time(configuration_b),
        ),
        ComparisonRow(
            "Total estimated drift",
            _format_total_drift(configuration_a, unit_system),
            _format_total_drift(configuration_b, unit_system),
        ),
        ComparisonRow(
            "Warnings",
            ", ".join(warning.code for warning in configuration_a.warnings) or "None",
            ", ".join(warning.code for warning in configuration_b.warnings) or "None",
        ),
    ]


def _format_parachutes(
    configuration: Configuration,
    formatter,
    *,
    require_analysis: bool = False,
) -> str:
    if require_analysis and configuration.analysis_results is None:
        return "Draft / not analysed"

    parachutes = sorted(
        configuration.parachutes,
        key=lambda parachute: (ROLE_ORDER.get(parachute.role, 99), parachute.role),
    )
    if not parachutes:
        return "N/A"
    return "; ".join(
        f"{parachute.role}: {formatter(parachute)}"
        for parachute in parachutes
    )


def _catalogue_name(
    parachute: ParachuteSpec,
    catalogue_by_id: dict[str, CatalogueItem],
) -> str:
    if parachute.selected_catalogue_item_id is None:
        return "N/A"
    item = catalogue_by_id.get(parachute.selected_catalogue_item_id)
    if item is None:
        return parachute.selected_catalogue_item_id
    return item.product_name


def _format_total_time(configuration: Configuration) -> str:
    if configuration.analysis_results is None:
        return "Draft / not analysed"
    return format_time(configuration.analysis_results.total_descent_time_s)


def _format_total_drift(configuration: Configuration, unit_system: str) -> str:
    if configuration.analysis_results is None:
        return "Draft / not analysed"
    return format_length(configuration.analysis_results.total_estimated_drift_m, unit_system)


__all__ = ["ComparisonRow", "build_comparison_rows"]
