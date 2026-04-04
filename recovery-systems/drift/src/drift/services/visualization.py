"""Presentation models for DRIFT recovery schematic and timeline rendering."""

from __future__ import annotations

from dataclasses import dataclass

from drift.models import Configuration, PhaseSummary


@dataclass(slots=True, frozen=True)
class SchematicMarker:
    """One labeled schematic marker."""

    altitude_m: float
    label: str
    kind: str


@dataclass(slots=True, frozen=True)
class SchematicSegment:
    """One schematic segment between two altitudes."""

    start_altitude_m: float
    end_altitude_m: float
    label: str
    kind: str


@dataclass(slots=True, frozen=True)
class TimelineEvent:
    """One event in the recovery timeline."""

    label: str
    altitude_m: float
    time_s: float | None
    notes: str | None = None


@dataclass(slots=True, frozen=True)
class RecoveryVisualModel:
    """Complete presentation model for the right-panel recovery visuals."""

    basis_label: str
    max_altitude_m: float
    markers: tuple[SchematicMarker, ...]
    segments: tuple[SchematicSegment, ...]
    timeline_events: tuple[TimelineEvent, ...]


def build_recovery_visual_model(configuration: Configuration) -> RecoveryVisualModel:
    """Build a schematic/timeline model from one analyzed configuration."""

    if configuration.analysis_results is None:
        raise ValueError("Recovery visuals require analyzed configuration results.")

    markers: list[SchematicMarker] = [SchematicMarker(0.0, "Ground", "ground")]
    segments: list[SchematicSegment] = []
    timeline_events: list[TimelineEvent] = []
    analysis = configuration.analysis_results
    altitude_inputs = configuration.altitude_inputs

    if configuration.recovery_mode == "single":
        phase = analysis.phase_summaries[0]
        if altitude_inputs.apogee_altitude_m is not None:
            markers.append(SchematicMarker(altitude_inputs.apogee_altitude_m, "Apogee", "apogee"))
            segments.append(
                SchematicSegment(
                    0.0,
                    altitude_inputs.apogee_altitude_m,
                    "Ascent (schematic only)",
                    "ascent",
                )
            )
            timeline_events.append(
                TimelineEvent(
                    label="Recovery basis starts at apogee",
                    altitude_m=altitude_inputs.apogee_altitude_m,
                    time_s=0.0,
                    notes="Basis label: from_apogee",
                )
            )
        deployment_altitude_m = altitude_inputs.deployment_altitude_m or phase.start_altitude_m
        markers.append(
            SchematicMarker(
                deployment_altitude_m,
                "Single deployment",
                "deployment",
            )
        )
        if altitude_inputs.apogee_altitude_m is not None and deployment_altitude_m != phase.start_altitude_m:
            timeline_events.append(
                TimelineEvent(
                    label="Single deployment input altitude",
                    altitude_m=deployment_altitude_m,
                    time_s=None,
                    notes="Deployment timing is not modeled separately in the MVP basis.",
                )
            )
        timeline_events.append(
            TimelineEvent(
                label="Single deployment / descent begins",
                altitude_m=phase.start_altitude_m,
                time_s=0.0,
                notes=f"Basis label: {analysis.recovery_basis_label}",
            )
        )
        segments.append(_segment_from_phase(phase, "single"))
        timeline_events.append(
            TimelineEvent(
                label="Landing",
                altitude_m=0.0,
                time_s=analysis.total_descent_time_s,
                notes="End of single descent phase.",
            )
        )
    else:
        drogue_phase = analysis.phase_summaries[0]
        main_phase = analysis.phase_summaries[1]
        if altitude_inputs.apogee_altitude_m is not None:
            markers.append(SchematicMarker(altitude_inputs.apogee_altitude_m, "Apogee", "apogee"))
            segments.append(
                SchematicSegment(
                    0.0,
                    altitude_inputs.apogee_altitude_m,
                    "Ascent (schematic only)",
                    "ascent",
                )
            )
            timeline_events.append(
                TimelineEvent(
                    label="Recovery basis starts at apogee",
                    altitude_m=altitude_inputs.apogee_altitude_m,
                    time_s=0.0,
                    notes="Basis label: from_apogee",
                )
            )
        drogue_deployment_altitude_m = (
            altitude_inputs.drogue_deployment_altitude_m or drogue_phase.start_altitude_m
        )
        main_deployment_altitude_m = (
            altitude_inputs.main_deployment_altitude_m or main_phase.start_altitude_m
        )
        markers.append(
            SchematicMarker(
                drogue_deployment_altitude_m,
                "Drogue deployment",
                "deployment",
            )
        )
        markers.append(
            SchematicMarker(
                main_deployment_altitude_m,
                "Main deployment",
                "deployment",
            )
        )
        if (
            altitude_inputs.apogee_altitude_m is not None
            and drogue_deployment_altitude_m != drogue_phase.start_altitude_m
        ):
            timeline_events.append(
                TimelineEvent(
                    label="Drogue deployment input altitude",
                    altitude_m=drogue_deployment_altitude_m,
                    time_s=None,
                    notes="Deployment timing is not modeled separately in the MVP basis.",
                )
            )
        timeline_events.append(
            TimelineEvent(
                label="Drogue deployment / drogue descent begins",
                altitude_m=drogue_phase.start_altitude_m,
                time_s=0.0,
                notes=f"Basis label: {analysis.recovery_basis_label}",
            )
        )
        segments.append(_segment_from_phase(drogue_phase, "drogue"))
        segments.append(_segment_from_phase(main_phase, "main"))
        timeline_events.append(
            TimelineEvent(
                label="Main deployment / main descent begins",
                altitude_m=main_phase.start_altitude_m,
                time_s=drogue_phase.estimated_duration_s,
                notes="Transition from drogue phase to main phase.",
            )
        )
        timeline_events.append(
            TimelineEvent(
                label="Landing",
                altitude_m=0.0,
                time_s=analysis.total_descent_time_s,
                notes="End of main descent phase.",
            )
        )

    max_altitude_m = max(
        [marker.altitude_m for marker in markers]
        + [segment.start_altitude_m for segment in segments]
        + [segment.end_altitude_m for segment in segments]
    )
    return RecoveryVisualModel(
        basis_label=analysis.recovery_basis_label,
        max_altitude_m=max_altitude_m,
        markers=tuple(
            sorted(markers, key=lambda marker: (-marker.altitude_m, marker.label))
        ),
        segments=tuple(segments),
        timeline_events=tuple(timeline_events),
    )


def _segment_from_phase(phase: PhaseSummary, kind: str) -> SchematicSegment:
    return SchematicSegment(
        start_altitude_m=phase.start_altitude_m,
        end_altitude_m=phase.end_altitude_m,
        label=f"{phase.phase_name.capitalize()} descent",
        kind=kind,
    )


__all__ = [
    "RecoveryVisualModel",
    "SchematicMarker",
    "SchematicSegment",
    "TimelineEvent",
    "build_recovery_visual_model",
]
