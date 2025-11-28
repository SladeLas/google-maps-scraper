"""Persistence helpers for the `entities` table."""

from __future__ import annotations
from typing import Any, Iterable, Mapping, Sequence
from psycopg2.extras import execute_values
from slade_digital_scrapers.infrastructure.database.connection import db_connection

ENTITY_COLUMNS: Sequence[str] = (
    "name",
    "place_id",
    "address",
    "google_rating",
    "review_count",
    "entity_categories",
    "website",
    "phone",
    "google_link",
)

UPSERT_SQL = f"""
INSERT INTO entities ({", ".join(ENTITY_COLUMNS)})
VALUES %s
ON CONFLICT (place_id) DO UPDATE
SET
    name = EXCLUDED.name,
    address = EXCLUDED.address,
    google_rating = EXCLUDED.google_rating,
    review_count = EXCLUDED.review_count,
    entity_categories = EXCLUDED.entity_categories,
    website = EXCLUDED.website,
    phone = EXCLUDED.phone,
    google_link = EXCLUDED.google_link
"""

def upsert_entities(records: Iterable[Mapping[str, Any]], page_size: int = 250) -> int:
    """
    Bulk upsert entity payloads into the `entities` table.

    Args:
        records: Iterable of dict-like objects that follow the Google Maps
            scraper contract (see response_*.json example).
        page_size: Optional batch size for `execute_values`.

    Returns:
        Number of rows that were attempted (inserted + updated).

    Notes:
        - Requires a unique constraint on `entities.place_id`. Example:
          `ALTER TABLE entities ADD CONSTRAINT entities_place_id_key UNIQUE (place_id);`
        - Uses a single INSERT ... ON CONFLICT statement per batch to keep the
          memory and round-trips minimal.
    """

    rows = [_to_row(record) for record in records if record]
    if not rows:
        return 0

    with db_connection() as conn:
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                UPSERT_SQL,
                rows,
                template="(" + ", ".join(["%s"] * len(ENTITY_COLUMNS)) + ")",
                page_size=page_size,
            )
        conn.commit()

    return len(rows)


def _to_row(record: Mapping[str, Any]) -> tuple[Any, ...]:
    """Transform the scraper payload into the DB column order."""
    categories = record.get("categories") or record.get("entity_categories")
    categories = _clean_categories(categories)

    return (
        record.get("name"),
        record.get("place_id"),
        record.get("address"),
        _coerce_int(record.get("rating")),
        _coerce_int(record.get("reviews_count")),
        categories,
        record.get("website"),
        record.get("phone"),
        record.get("link"),
    )


def _clean_categories(raw: Any) -> list[str] | None:
    if not raw:
        return None
    items = [str(item).strip() for item in raw if item]
    return items or None


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None

