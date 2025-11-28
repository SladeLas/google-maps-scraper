"""Typed contracts for Google Maps entity payloads."""

from __future__ import annotations
from typing import Any, Iterable
from pydantic import BaseModel, Field, HttpUrl, field_validator


class Coordinates(BaseModel):
    """Lat/long pair provided by the scraper."""

    latitude: float = Field(..., description="Decimal latitude from Google Maps.")
    longitude: float = Field(..., description="Decimal longitude from Google Maps.")


class EntityContract(BaseModel):
    """Canonical representation of an entity scraped from Google Maps."""

    name: str = Field(..., description="Business name as displayed on Maps.")
    place_id: str = Field(..., description="Stable Google Maps place identifier.")
    coordinates: Coordinates = Field(..., description="Lat/long pair for the entity.")
    address: str | None = Field(None, description="Formatted street address.")
    rating: float | None = Field(
        None, ge=0, le=5, description="Aggregate rating (0-5 scale)."
    )
    reviews_count: int | None = Field(
        None, ge=0, description="Number of public reviews when scraped."
    )
    categories: list[str] = Field(
        default_factory=list,
        description="All Google tags/categories associated with the entity.",
    )
    website: HttpUrl | None = Field(
        None, description="External website URL if available."
    )
    phone: str | None = Field(None, description="Dial-able phone number string.")
    link: HttpUrl | None = Field(
        None,
        description="Direct Google Maps deep-link for the entity.",
    )

    @field_validator("categories", mode="before")
    @classmethod
    def _normalize_categories(cls, value: Iterable[str] | None) -> list[str]:
        if not value:
            return []
        return [str(item).strip() for item in value if item]

    def to_repository_dict(self) -> dict[str, Any]:
        """Flatten into the shape expected by `upsert_entities`."""
        payload = self.dict()
        payload["entity_categories"] = payload.pop("categories")
        return payload

