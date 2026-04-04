"""JSON persistence helpers for DRIFT project and catalogue data."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from drift.models import CatalogueItem, Project

CATALOGUE_SCHEMA_VERSION = "1.0.0"


def project_to_dict(project: Project) -> dict[str, object]:
    """Return a JSON-ready project mapping."""

    return project.to_dict()


def project_from_dict(data: dict[str, object]) -> Project:
    """Build a project model from a JSON-ready mapping."""

    return Project.from_dict(data)


def dumps_project(project: Project) -> str:
    """Serialize a project to deterministic JSON text."""

    return json.dumps(
        project_to_dict(project),
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"


def loads_project(payload: str) -> Project:
    """Deserialize a project from JSON text."""

    return project_from_dict(json.loads(payload))


def save_project(project: Project, path: str | Path) -> Path:
    """Save a project JSON file to disk."""

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(dumps_project(project), encoding="utf-8")
    return file_path


def load_project(path: str | Path) -> Project:
    """Load a project JSON file from disk."""

    return loads_project(Path(path).read_text(encoding="utf-8"))


def catalogue_to_dict(items: Sequence[CatalogueItem]) -> dict[str, object]:
    """Return a JSON-ready catalogue mapping."""

    return {
        "schema_version": CATALOGUE_SCHEMA_VERSION,
        "items": [item.to_dict() for item in items],
    }


def catalogue_from_dict(data: dict[str, object]) -> list[CatalogueItem]:
    """Build catalogue items from a JSON-ready mapping."""

    return [CatalogueItem.from_dict(item) for item in data.get("items", [])]


def dumps_catalogue(items: Sequence[CatalogueItem]) -> str:
    """Serialize catalogue items to deterministic JSON text."""

    return json.dumps(
        catalogue_to_dict(items),
        indent=2,
        ensure_ascii=True,
        allow_nan=False,
    ) + "\n"


def loads_catalogue(payload: str) -> list[CatalogueItem]:
    """Deserialize catalogue items from JSON text."""

    return catalogue_from_dict(json.loads(payload))


def save_catalogue(items: Sequence[CatalogueItem], path: str | Path) -> Path:
    """Save a catalogue JSON file to disk."""

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(dumps_catalogue(items), encoding="utf-8")
    return file_path


def load_catalogue(path: str | Path) -> list[CatalogueItem]:
    """Load catalogue items from disk."""

    return loads_catalogue(Path(path).read_text(encoding="utf-8"))
