"""Test script for inserting scraper history records into the database."""

import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from slade_digital_scrapers.infrastructure.models.scraper_hisotry.repository import (
    upsert_scrape_history,
    get_scrape_history,
)
from slade_digital_scrapers.infrastructure.models.scraper_hisotry.schema import ScrapeHistoryContract
from slade_digital_scrapers.infrastructure.database.schema import test_connection


def test_scraper_history_insertion():
    """Test inserting scraper history records."""
    print("=" * 60)
    print("Testing Scraper History Insertion")
    print("=" * 60)
    
    # Test database connection first
    print("\n1. Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed. Please check your configuration.")
        return False
    print("✅ Database connection successful!")
    
    # Create test records
    print("\n2. Creating test scraper history records...")
    test_records = [
        ScrapeHistoryContract(
            source="gmaps_insurance_nyc_test",
            search_key="insurance agencies in New York",
            location_key="New York, NY",
            results_scraped=20,
        ),
        ScrapeHistoryContract(
            source="gmaps_restaurants_la_test",
            search_key="restaurants in Los Angeles",
            location_key="Los Angeles, CA",
            results_scraped=50,
        ),
        ScrapeHistoryContract(
            source="gmaps_insurance_nyc_test",  # Duplicate source to test upsert
            search_key="insurance agencies in New York",
            location_key="New York, NY",
            results_scraped=25,  # Updated count
        ),
    ]
    
    print(f"   Created {len(test_records)} test records:")
    for record in test_records:
        print(f"   - Source: {record.source}")
        print(f"     Search: {record.search_key}")
        print(f"     Location: {record.location_key}")
        print(f"     Results: {record.results_scraped}")
    
    # Insert records
    print(f"\n3. Inserting scraper history records into database...")
    try:
        records_dict = [record.to_repository_dict() for record in test_records]
        rows_inserted = upsert_scrape_history(records_dict)
        print(f"✅ Successfully processed {rows_inserted} records")
        print(f"   (Note: Duplicate sources in the same batch are deduplicated automatically)")
    except Exception as e:
        print(f"❌ Failed to insert scraper history: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Fetch and display records
    print(f"\n4. Fetching scraper history records from database...")
    try:
        all_records = get_scrape_history()
        print(f"✅ Retrieved {len(all_records)} total records from database")
        
        # Show the test records we just inserted
        test_sources = {record.source for record in test_records}
        matching_records = [r for r in all_records if r.get("source") in test_sources]
        
        if matching_records:
            print(f"\n   Found {len(matching_records)} matching test records:")
            for record in matching_records:
                print(f"   - ID: {record.get('id')}")
                print(f"     Source: {record.get('source')}")
                print(f"     Search Key: {record.get('search_key')}")
                print(f"     Location Key: {record.get('location_key')}")
                print(f"     Results Scraped: {record.get('results_scraped')}")
                print(f"     Created At: {record.get('created_at')}")
                print()
    except Exception as e:
        print(f"❌ Failed to fetch scraper history: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 60)
    print("✅ Scraper history insertion test completed successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_scraper_history_insertion()
    sys.exit(0 if success else 1)

