# Test Scripts

This directory contains test scripts for validating database insertion functionality.

## Prerequisites

1. Ensure your database is configured and accessible (check `.env` file)
2. Make sure the database tables are created (run `schema.py` if needed)
3. Ensure the `response_1764064679215.json` file exists in the project root

## Test Scripts

### `test_entities_insertion.py`
Tests inserting entity records from the `response_1764064679215.json` file into the `entities` table.

**Usage:**
```bash
python tests/test_entities_insertion.py
```

**What it does:**
- Tests database connection
- Loads entities from the response JSON file
- Inserts/updates entities in the database
- Displays results and sample entity structure

### `test_scraper_history_insertion.py`
Tests inserting scraper history records into the `scrape_history` table.

**Usage:**
```bash
python tests/test_scraper_history_insertion.py
```

**What it does:**
- Tests database connection
- Creates test scraper history records
- Inserts/updates records in the database
- Fetches and displays the inserted records

### `test_all_insertions.py`
Runs both test scripts sequentially and provides a summary.

**Usage:**
```bash
python tests/test_all_insertions.py
```

## Running from Project Root

Make sure you're in the project root directory when running these tests:

```bash
cd /path/to/google-maps-scraper
python tests/test_entities_insertion.py
python tests/test_scraper_history_insertion.py
python tests/test_all_insertions.py
```

## Notes

- These tests will insert/update real data in your database
- The entity test uses the actual response JSON file from your scraper
- The scraper history test creates sample records with test prefixes
- Duplicate records (same `place_id` for entities, same `source` for history) will update existing records

