"""Project model definitions for DRIFT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .configuration import Configuration

PROJECT_SCHEMA_VERSION = "1.0.0"


@dataclass(slots=True)
class Project:
    """Represents one saved DRIFT recovery study."""

    project_id: str
    project_name: str
    description: str | None
    created_at: str
    updated_at: str
    default_unit_system: str
    configurations: list[Configuration] = field(default_factory=list)
    active_configuration_id: str | None = None
    schema_version: str = PROJECT_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "default_unit_system": self.default_unit_system,
            "active_configuration_id": self.active_configuration_id,
            "configurations": [
                configuration.to_dict() for configuration in self.configurations
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        return cls(
            schema_version=data["schema_version"],
            project_id=data["project_id"],
            project_name=data["project_name"],
            description=data.get("description"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            default_unit_system=data["default_unit_system"],
            active_configuration_id=data.get("active_configuration_id"),
            configurations=[
                Configuration.from_dict(item) for item in data.get("configurations", [])
            ],
        )
