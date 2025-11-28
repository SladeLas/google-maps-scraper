"""Typed contracts for scrape history records."""

from __future__ import annotations
from pydantic import BaseModel, Field


class ScrapeHistoryContract(BaseModel):
    """Canonical representation of a scrape history record."""

    source: str = Field(..., description="Unique identifier for the scrape source (e.g., 'gmaps_insurance_nyc').")
    search_key: str | None = Field(None, description="Search query/keyword used for the scrape.")
    location_key: str | None = Field(None, description="Location identifier used for the scrape.")
    results_scraped: int | None = Field(None, ge=0, description="Number of results/entities scraped in this run.")

    def to_repository_dict(self) -> dict[str, str | int | None]:
        """Flatten into the shape expected by repository functions."""
        return {
            "source": self.source,
            "search_key": self.search_key,
            "location_key": self.location_key,
            "results_scraped": self.results_scraped,
        }

