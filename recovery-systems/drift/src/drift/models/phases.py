"""Recovery phase and analysis result models for DRIFT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class PhaseSummary:
    """Represents one recovery phase in canonical SI units."""

    phase_name: str
    start_altitude_m: float
    end_altitude_m: float
    parachute_id: str
    nominal_descent_velocity_mps: float
    estimated_duration_s: float | None = None
    estimated_drift_m: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase_name": self.phase_name,
            "start_altitude_m": self.start_altitude_m,
            "end_altitude_m": self.end_altitude_m,
            "parachute_id": self.parachute_id,
            "nominal_descent_velocity_mps": self.nominal_descent_velocity_mps,
            "estimated_duration_s": self.estimated_duration_s,
            "estimated_drift_m": self.estimated_drift_m,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhaseSummary":
        return cls(
            phase_name=data["phase_name"],
            start_altitude_m=data["start_altitude_m"],
            end_altitude_m=data["end_altitude_m"],
            parachute_id=data["parachute_id"],
            nominal_descent_velocity_mps=data["nominal_descent_velocity_mps"],
            estimated_duration_s=data.get("estimated_duration_s"),
            estimated_drift_m=data.get("estimated_drift_m"),
        )


@dataclass(slots=True)
class AnalysisResult:
    """Represents top-level analysis outputs for a configuration."""

    recovery_basis_label: str
    phase_summaries: list[PhaseSummary] = field(default_factory=list)
    total_descent_time_s: float | None = None
    total_estimated_drift_m: float | None = None
    display_metrics: dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "recovery_basis_label": self.recovery_basis_label,
            "phase_summaries": [phase.to_dict() for phase in self.phase_summaries],
            "total_descent_time_s": self.total_descent_time_s,
            "total_estimated_drift_m": self.total_estimated_drift_m,
            "display_metrics": dict(self.display_metrics),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AnalysisResult":
        return cls(
            recovery_basis_label=data["recovery_basis_label"],
            phase_summaries=[
                PhaseSummary.from_dict(item)
                for item in data.get("phase_summaries", [])
            ],
            total_descent_time_s=data.get("total_descent_time_s"),
            total_estimated_drift_m=data.get("total_estimated_drift_m"),
            display_metrics=dict(data.get("display_metrics", {})),
        )
