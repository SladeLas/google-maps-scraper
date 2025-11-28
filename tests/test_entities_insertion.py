"""Test script for inserting entity records into the database."""

import json
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from slade_digital_scrapers.infrastructure.models.entities.repository import upsert_entities
from slade_digital_scrapers.infrastructure.database.schema import test_connection


def load_test_data(json_path: str) -> list[dict]:
    """Load entity data from the response JSON file."""
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_entity_insertion():
    """Test inserting entities from the response JSON file."""
    print("=" * 60)
    print("Testing Entity Insertion")
    print("=" * 60)
    
    # Test database connection first
    print("\n1. Testing database connection...")
    if not test_connection():
        print("❌ Database connection failed. Please check your configuration.")
        return False
    print("✅ Database connection successful!")
    
    # Load test data
    print("\n2. Loading test data from response JSON...")
    json_path = project_root / "response_1764064679215.json"
    
    if not json_path.exists():
        print(f"❌ Test data file not found: {json_path}")
        return False
    
    try:
        entities = load_test_data(str(json_path))
        print(f"✅ Loaded {len(entities)} entities from JSON file")
    except Exception as e:
        print(f"❌ Failed to load JSON file: {e}")
        return False
    
    # Display sample entity
    if entities:
        print(f"\n3. Sample entity structure:")
        sample = entities[0]
        print(f"   - Name: {sample.get('name')}")
        print(f"   - Place ID: {sample.get('place_id')}")
        print(f"   - Address: {sample.get('address', 'N/A')[:50]}...")
        print(f"   - Rating: {sample.get('rating', 'N/A')}")
        print(f"   - Reviews: {sample.get('reviews_count', 'N/A')}")
        print(f"   - Categories: {len(sample.get('categories', []))} categories")
    
    # Insert entities
    print(f"\n4. Inserting {len(entities)} entities into database...")
    try:
        rows_inserted = upsert_entities(entities)
        print(f"✅ Successfully processed {rows_inserted} entities")
        print(f"   (This includes both new inserts and updates to existing records)")
    except Exception as e:
        print(f"❌ Failed to insert entities: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("✅ Entity insertion test completed successfully!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_entity_insertion()
    sys.exit(0 if success else 1)

