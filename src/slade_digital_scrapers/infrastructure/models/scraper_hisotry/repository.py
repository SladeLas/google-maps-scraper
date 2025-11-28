"""Persistence helpers for the `scrape_history` table."""

from __future__ import annotations
from typing import Any, Iterable, Mapping
from psycopg2.extras import execute_values
from slade_digital_scrapers.infrastructure.database.connection import db_connection

SCRAPE_HISTORY_COLUMNS = ("source", "search_key", "location_key", "results_scraped")

UPSERT_SQL = f"""
INSERT INTO scrape_history ({", ".join(SCRAPE_HISTORY_COLUMNS)})
VALUES %s
ON CONFLICT (source) DO UPDATE
SET
    search_key = EXCLUDED.search_key,
    location_key = EXCLUDED.location_key,
    results_scraped = EXCLUDED.results_scraped
"""


def upsert_scrape_history(records: Iterable[Mapping[str, Any]], page_size: int = 100) -> int:
    """
    Bulk upsert scrape history records into the `scrape_history` table.

    Args:
        records: Iterable of dict-like objects with `source`, `search_key`, `location_key`, and `results_scraped`.
        page_size: Optional batch size for `execute_values`.

    Returns:
        Number of rows that were attempted (inserted + updated).

    Notes:
        - Requires a unique constraint on `scrape_history.source` (already defined in schema).
        - Uses a single INSERT ... ON CONFLICT statement per batch for efficiency.
        - Deduplicates records by `source` (keeps the last occurrence) to avoid PostgreSQL errors.
    """
    # Deduplicate by source (keep last occurrence) to avoid ON CONFLICT errors
    seen = {}
    for record in records:
        if record:
            source = str(record.get("source", ""))
            if source:
                seen[source] = record

    if not seen:
        return 0

    rows = [_to_row(record) for record in seen.values()]

    with db_connection() as conn:
        with conn.cursor() as cursor:
            execute_values(
                cursor,
                UPSERT_SQL,
                rows,
                template="(" + ", ".join(["%s"] * len(SCRAPE_HISTORY_COLUMNS)) + ")",
                page_size=page_size,
            )
        conn.commit()

    return len(rows)


def get_scrape_history(source: str | None = None) -> list[dict[str, Any]]:
    """
    Fetch scrape history records from the database.

    Args:
        source: Optional filter by source identifier. If None, returns all records.

    Returns:
        List of dictionaries with scrape history data.
    """
    with db_connection() as conn:
        with conn.cursor() as cursor:
            if source:
                cursor.execute(
                    """
                    SELECT id, source, search_key, location_key, results_scraped, created_at
                    FROM scrape_history
                    WHERE source = %s
                    ORDER BY created_at DESC
                    """,
                    (source,),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, source, search_key, location_key, results_scraped, created_at
                    FROM scrape_history
                    ORDER BY created_at DESC
                    """
                )

            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _to_row(record: Mapping[str, Any]) -> tuple[str, str | None, str | None, int | None]:
    """Transform the record into the DB column order."""
    results_scraped = record.get("results_scraped")
    if results_scraped is not None:
        try:
            results_scraped = int(results_scraped)
        except (TypeError, ValueError):
            results_scraped = None
    
    return (
        str(record.get("source", "")),
        record.get("search_key"),
        record.get("location_key"),
        results_scraped,
    )

