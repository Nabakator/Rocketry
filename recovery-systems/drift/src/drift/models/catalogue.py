"""Catalogue models for DRIFT."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class CatalogueItem:
    """Represents one local parachute catalogue entry."""

    item_id: str
    vendor: str
    product_name: str
    family: str
    nominal_diameter_m: float
    nominal_diameter_display: str
    notes: str | None = None
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_id": self.item_id,
            "vendor": self.vendor,
            "product_name": self.product_name,
            "family": self.family,
            "nominal_diameter_m": self.nominal_diameter_m,
            "nominal_diameter_display": self.nominal_diameter_display,
            "notes": self.notes,
            "url": self.url,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CatalogueItem":
        return cls(
            item_id=data["item_id"],
            vendor=data["vendor"],
            product_name=data["product_name"],
            family=data["family"],
            nominal_diameter_m=data["nominal_diameter_m"],
            nominal_diameter_display=data["nominal_diameter_display"],
            notes=data.get("notes"),
            url=data.get("url"),
        )
