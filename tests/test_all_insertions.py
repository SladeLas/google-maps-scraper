"""Test script to run both entity and scraper history insertion tests."""

import sys
import importlib.util
from pathlib import Path

# Add the src directory to the path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
tests_dir = Path(__file__).parent

# Import test functions from other test files
spec1 = importlib.util.spec_from_file_location(
    "test_entities_insertion", tests_dir / "test_entities_insertion.py"
)
test_entities_module = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(test_entities_module)

spec2 = importlib.util.spec_from_file_location(
    "test_scraper_history_insertion", tests_dir / "test_scraper_history_insertion.py"
)
test_scraper_history_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(test_scraper_history_module)

test_entity_insertion = test_entities_module.test_entity_insertion
test_scraper_history_insertion = test_scraper_history_module.test_scraper_history_insertion


def run_all_tests():
    """Run all insertion tests."""
    print("\n" + "=" * 60)
    print("Running All Insertion Tests")
    print("=" * 60 + "\n")
    
    results = []
    
    # Test scraper history first (simpler)
    print("\n" + "─" * 60)
    results.append(("Scraper History", test_scraper_history_insertion()))
    
    # Test entities
    print("\n" + "─" * 60)
    results.append(("Entities", test_entity_insertion()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    for test_name, test_success in results:
        status = "✅ PASSED" if test_success else "❌ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed.")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    test_success = run_all_tests()
    sys.exit(0 if test_success else 1)

