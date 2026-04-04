"""Presentation models for DRIFT recovery schematic and timeline rendering."""

from __future__ import annotations

from dataclasses import dataclass

from drift.models import Configuration, PhaseSummary

ASCENT_START_X = 0.10
ASCENT_APOGEE_X = 0.30
DESCENT_START_X = 0.42
DESCENT_END_X = 0.90
SLOPE_ORDER_MARGIN = 1.10
MIN_VISIBLE_SPAN = 0.02
PREFERRED_TRANSITION_SPAN = 0.04


@dataclass(slots=True, frozen=True)
class SchematicMarker:
    """One labeled schematic marker."""

    altitude_m: float
    x_fraction: float
    label: str
    kind: str


@dataclass(slots=True, frozen=True)
class SchematicSegment:
    """One schematic segment between two altitudes."""

    start_altitude_m: float
    end_altitude_m: float
    start_x_fraction: float
    end_x_fraction: float
    label: str
    kind: str
    show_label: bool = True


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


def _humanise(value: str) -> str:
    return value.replace("_", " ").strip().capitalize()


def build_recovery_visual_model(configuration: Configuration) -> RecoveryVisualModel:
    """Build a schematic/timeline model from one analysed configuration."""

    if configuration.analysis_results is None:
        raise ValueError("Recovery visuals require analysed configuration results.")

    markers: list[SchematicMarker] = []
    segments: list[SchematicSegment] = []
    timeline_events: list[TimelineEvent] = []
    analysis = configuration.analysis_results
    altitude_inputs = configuration.altitude_inputs
    phase_summaries = analysis.phase_summaries
    total_drift_m = analysis.total_estimated_drift_m or 0.0

    def drift_to_x_fraction(drift_m: float) -> float:
        if total_drift_m <= 0.0:
            return DESCENT_START_X
        ratio = max(0.0, min(1.0, drift_m / total_drift_m))
        return DESCENT_START_X + ratio * (DESCENT_END_X - DESCENT_START_X)

    if configuration.recovery_mode == "single":
        phase = phase_summaries[0]
        deployment_altitude_m = altitude_inputs.deployment_altitude_m or phase.start_altitude_m
        landing_x = drift_to_x_fraction(phase.estimated_drift_m or 0.0)
        descent_start_x = DESCENT_START_X

        if altitude_inputs.apogee_altitude_m is not None:
            if deployment_altitude_m < altitude_inputs.apogee_altitude_m:
                descent_start_x = _transition_end_x(
                    start_x=ASCENT_APOGEE_X,
                    end_x=landing_x,
                    transition_drop_m=altitude_inputs.apogee_altitude_m - deployment_altitude_m,
                    next_phase_drop_m=max(deployment_altitude_m - phase.end_altitude_m, 0.0),
                )
            markers.append(
                SchematicMarker(
                    altitude_inputs.apogee_altitude_m,
                    ASCENT_APOGEE_X,
                    "Apogee",
                    "apogee",
                )
            )
            segments.append(
                SchematicSegment(
                    0.0,
                    altitude_inputs.apogee_altitude_m,
                    ASCENT_START_X,
                    ASCENT_APOGEE_X,
                    "Ascent",
                    "ascent",
                )
            )
            if deployment_altitude_m < altitude_inputs.apogee_altitude_m:
                segments.append(
                    SchematicSegment(
                        altitude_inputs.apogee_altitude_m,
                        deployment_altitude_m,
                        ASCENT_APOGEE_X,
                        descent_start_x,
                        "Pre-deployment descent",
                        "transition",
                        show_label=False,
                    )
                )
            timeline_events.append(
                TimelineEvent(
                    label="Recovery basis starts at apogee",
                    altitude_m=altitude_inputs.apogee_altitude_m,
                    time_s=0.0,
                    notes="Basis: From apogee",
                )
            )
        deployment_altitude_m = altitude_inputs.deployment_altitude_m or phase.start_altitude_m
        markers.append(
            SchematicMarker(
                deployment_altitude_m,
                descent_start_x,
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
                    notes="Deployment timing is not modelled separately in the MVP basis.",
                )
            )
        timeline_events.append(
            TimelineEvent(
                label="Single deployment / descent begins",
                altitude_m=phase.start_altitude_m,
                time_s=0.0,
                notes=f"Basis: {_humanise(analysis.recovery_basis_label)}",
            )
        )
        segments.append(
            _segment_from_phase(
                phase,
                "single",
                start_altitude_m=deployment_altitude_m,
                start_x_fraction=descent_start_x,
                end_x_fraction=landing_x,
            )
        )
        markers.append(SchematicMarker(0.0, landing_x, "Ground", "ground"))
        timeline_events.append(
            TimelineEvent(
                label="Landing",
                altitude_m=0.0,
                time_s=analysis.total_descent_time_s,
                notes="End of single descent phase.",
            )
        )
    else:
        drogue_phase = phase_summaries[0]
        main_phase = phase_summaries[1]
        drogue_deployment_altitude_m = (
            altitude_inputs.drogue_deployment_altitude_m or drogue_phase.start_altitude_m
        )
        main_deployment_altitude_m = (
            altitude_inputs.main_deployment_altitude_m or main_phase.start_altitude_m
        )
        main_end_x = drift_to_x_fraction(
            (drogue_phase.estimated_drift_m or 0.0) + (main_phase.estimated_drift_m or 0.0)
        )
        drogue_start_x = DESCENT_START_X
        drogue_end_x = _phase_boundary_x(
            start_x=drogue_start_x,
            end_x=main_end_x,
            first_phase_drop_m=max(drogue_deployment_altitude_m - drogue_phase.end_altitude_m, 0.0),
            second_phase_drop_m=max(main_deployment_altitude_m - main_phase.end_altitude_m, 0.0),
            preferred_first_ratio=_drift_ratio(
                drogue_phase.estimated_drift_m,
                (drogue_phase.estimated_drift_m or 0.0) + (main_phase.estimated_drift_m or 0.0),
            ),
        )
        main_start_x = drogue_end_x

        if altitude_inputs.apogee_altitude_m is not None:
            if drogue_deployment_altitude_m < altitude_inputs.apogee_altitude_m:
                drogue_start_x = _transition_end_x(
                    start_x=ASCENT_APOGEE_X,
                    end_x=drogue_end_x,
                    transition_drop_m=(
                        altitude_inputs.apogee_altitude_m - drogue_deployment_altitude_m
                    ),
                    next_phase_drop_m=max(
                        drogue_deployment_altitude_m - drogue_phase.end_altitude_m,
                        0.0,
                    ),
                )
                drogue_end_x = _phase_boundary_x(
                    start_x=drogue_start_x,
                    end_x=main_end_x,
                    first_phase_drop_m=max(
                        drogue_deployment_altitude_m - drogue_phase.end_altitude_m,
                        0.0,
                    ),
                    second_phase_drop_m=max(
                        main_deployment_altitude_m - main_phase.end_altitude_m,
                        0.0,
                    ),
                    preferred_first_ratio=_drift_ratio(
                        drogue_phase.estimated_drift_m,
                        (drogue_phase.estimated_drift_m or 0.0)
                        + (main_phase.estimated_drift_m or 0.0),
                    ),
                )
                main_start_x = drogue_end_x
            markers.append(
                SchematicMarker(
                    altitude_inputs.apogee_altitude_m,
                    ASCENT_APOGEE_X,
                    "Apogee",
                    "apogee",
                )
            )
            segments.append(
                SchematicSegment(
                    0.0,
                    altitude_inputs.apogee_altitude_m,
                    ASCENT_START_X,
                    ASCENT_APOGEE_X,
                    "Ascent",
                    "ascent",
                )
            )
            if drogue_deployment_altitude_m < altitude_inputs.apogee_altitude_m:
                segments.append(
                    SchematicSegment(
                        altitude_inputs.apogee_altitude_m,
                        drogue_deployment_altitude_m,
                        ASCENT_APOGEE_X,
                        drogue_start_x,
                        "Pre-deployment descent",
                        "transition",
                        show_label=False,
                    )
                )
            timeline_events.append(
                TimelineEvent(
                    label="Recovery basis starts at apogee",
                    altitude_m=altitude_inputs.apogee_altitude_m,
                    time_s=0.0,
                    notes="Basis: From apogee",
                )
            )
        markers.append(
            SchematicMarker(
                drogue_deployment_altitude_m,
                drogue_start_x,
                "Drogue deployment",
                "deployment",
            )
        )
        markers.append(
            SchematicMarker(
                main_deployment_altitude_m,
                main_start_x,
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
                    notes="Deployment timing is not modelled separately in the MVP basis.",
                )
            )
        timeline_events.append(
            TimelineEvent(
                label="Drogue deployment / drogue descent begins",
                altitude_m=drogue_phase.start_altitude_m,
                time_s=0.0,
                notes=f"Basis: {_humanise(analysis.recovery_basis_label)}",
            )
        )
        segments.append(
            _segment_from_phase(
                drogue_phase,
                "drogue",
                start_altitude_m=drogue_deployment_altitude_m,
                start_x_fraction=drogue_start_x,
                end_x_fraction=drogue_end_x,
            )
        )
        segments.append(
            _segment_from_phase(
                main_phase,
                "main",
                start_altitude_m=main_deployment_altitude_m,
                start_x_fraction=main_start_x,
                end_x_fraction=main_end_x,
            )
        )
        markers.append(SchematicMarker(0.0, main_end_x, "Ground", "ground"))
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


def _segment_from_phase(
    phase: PhaseSummary,
    kind: str,
    *,
    start_altitude_m: float,
    start_x_fraction: float,
    end_x_fraction: float,
) -> SchematicSegment:
    return SchematicSegment(
        start_altitude_m=start_altitude_m,
        end_altitude_m=phase.end_altitude_m,
        start_x_fraction=start_x_fraction,
        end_x_fraction=end_x_fraction,
        label=f"{phase.phase_name.capitalize()} descent",
        kind=kind,
    )


def _drift_ratio(part_drift_m: float | None, total_drift_m: float | None) -> float:
    if not part_drift_m or not total_drift_m or total_drift_m <= 0.0:
        return 0.5
    return max(0.0, min(1.0, part_drift_m / total_drift_m))


def _transition_end_x(
    *,
    start_x: float,
    end_x: float,
    transition_drop_m: float,
    next_phase_drop_m: float,
) -> float:
    available_span = max(end_x - start_x, MIN_VISIBLE_SPAN * 2.0)
    if transition_drop_m <= 0.0 or next_phase_drop_m <= 0.0:
        transition_span = min(PREFERRED_TRANSITION_SPAN, available_span - MIN_VISIBLE_SPAN)
        return start_x + max(MIN_VISIBLE_SPAN, transition_span)

    max_transition_span = available_span * transition_drop_m / (
        transition_drop_m + SLOPE_ORDER_MARGIN * next_phase_drop_m
    )
    transition_span = min(PREFERRED_TRANSITION_SPAN, max_transition_span * 0.95)
    transition_span = max(MIN_VISIBLE_SPAN, transition_span)
    transition_span = min(transition_span, available_span - MIN_VISIBLE_SPAN)
    return start_x + transition_span


def _phase_boundary_x(
    *,
    start_x: float,
    end_x: float,
    first_phase_drop_m: float,
    second_phase_drop_m: float,
    preferred_first_ratio: float,
) -> float:
    available_span = max(end_x - start_x, MIN_VISIBLE_SPAN * 2.0)
    preferred_first_span = available_span * preferred_first_ratio
    minimum_first_span = min(MIN_VISIBLE_SPAN, available_span / 2.0)
    maximum_first_span = available_span - minimum_first_span

    if first_phase_drop_m > 0.0 and second_phase_drop_m > 0.0:
        slope_bound = available_span * first_phase_drop_m / (
            first_phase_drop_m + SLOPE_ORDER_MARGIN * second_phase_drop_m
        )
        maximum_first_span = min(maximum_first_span, slope_bound * 0.98)

    first_span = min(preferred_first_span, maximum_first_span)
    first_span = max(minimum_first_span, first_span)
    first_span = min(first_span, available_span - minimum_first_span)
    return start_x + first_span


__all__ = [
    "RecoveryVisualModel",
    "SchematicMarker",
    "SchematicSegment",
    "TimelineEvent",
    "build_recovery_visual_model",
]
