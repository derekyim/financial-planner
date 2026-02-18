"""
Integration tests for SheetsUtilities write operations.

These tests modify actual data in the Google Sheet and restore original values after.
Requires:
    - Valid service account credentials file
    - The Google Sheet shared with the service account email (with Editor access)

Run with: pytest -m integration
Skip with: pytest -m "not integration"
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.sheets_utilities import SheetsUtilities

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# Test configuration
TEST_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1yopikoACz8oY32Zv9FrGhb64_PlDwcO1e02WePBr4uM/edit"
TEST_SHEET_NAME = "tests"

# Path to credentials - can be overridden with environment variable
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "../credentials.json")

@pytest.fixture(scope="module")
def sheets_client() -> SheetsUtilities:
    """
    Create a SheetsUtilities instance for testing.
    Scoped to module so we only authenticate once for all tests.
    """
    if not os.path.exists(CREDENTIALS_PATH):
        pytest.skip(f"Credentials file not found at: {CREDENTIALS_PATH}")
    return SheetsUtilities(CREDENTIALS_PATH)


class TestSheetsUtilitiesWriteOperations:
    """
    Tests for write operations on the Google Sheet.
    
    These tests modify cells and verify the changes, then restore original values.
    """
    
    def test_write_and_verify_changes(self, sheets_client: SheetsUtilities):
        """
        Test that verifies write operations by:
        1. Recording original values of BR14, BR18, BR19, BR20
        2. Changing BR14 to 10000 and verifying
        3. Changing BR18 to 1.23 and verifying
        4. Changing BR19 to 0.88 and verifying
        5. Verifying BR87 changed from 5221557.90 to 5218981.73
        6. Restoring original values
        """
        # Step 1: Record original values
        original_br14 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR14")
        original_br18 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR18")
        original_br19 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR19")
        original_br20 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR20")
        
        print(f"\nOriginal values:")
        print(f"  BR14: {original_br14}")
        print(f"  BR18: {original_br18}")
        print(f"  BR19: {original_br19}")
        print(f"  BR20: {original_br20}")
        
        # Also record BR87 initial value for verification
        initial_br87 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR87")
        print(f"  BR87 (before changes): {initial_br87}")
        
        try:
            # Step 2: Change BR14 to 10000 and verify
            print("\nChanging BR14 to 10000...")
            sheets_client.write_range(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR14", [[10000]])
            new_br14 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR14")
            print(f"  BR14 after change: {new_br14}")
            assert new_br14 == "10000" or float(new_br14) == 10000, \
                f"Expected BR14 to be 10000, got '{new_br14}'"
            
            # Step 3: Change BR18 to 1.23 and verify
            print("\nChanging BR18 to 1.23...")
            sheets_client.write_range(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR18", [[1.23]])
            new_br18 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR18")
            print(f"  BR18 after change: {new_br18}")
            assert float(new_br18) == 1.23, \
                f"Expected BR18 to be 1.23, got '{new_br18}'"
            
            # Step 4: Change BR19 to 0.88 and verify
            print("\nChanging BR19 to 0.88...")
            sheets_client.write_range(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR19", [[0.88]])
            new_br19 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR19")
            print(f"  BR19 after change: {new_br19}")
            assert float(new_br19) == 0.88, \
                f"Expected BR19 to be 0.88, got '{new_br19}'"
            
            # Step 5: Verify BR87 changed to expected value
            print("\nVerifying BR87 cascading change...")
            final_br87 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR87")
            print(f"  BR87 (after changes): {final_br87}")
            
            # Allow for small floating point differences
            expected_br87 = 5218981.73
            actual_br87 = float(final_br87.replace(',', '')) if isinstance(final_br87, str) else float(final_br87)
            assert abs(actual_br87 - expected_br87) < 0.01, \
                f"Expected BR87 to be ~{expected_br87}, got {actual_br87}"
            
            print("\n✓ All write operations verified successfully!")
            
        finally:
            # Step 6: Restore original values (always runs, even if test fails)
            print("\nRestoring original values...")
            
            # Restore BR14
            sheets_client.write_range(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR14", [[original_br14]])
            print(f"  Restored BR14 to: {original_br14}")
            
            # Restore BR18
            sheets_client.write_range(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR18", [[original_br18]])
            print(f"  Restored BR18 to: {original_br18}")
            
            # Restore BR19
            sheets_client.write_range(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR19", [[original_br19]])
            print(f"  Restored BR19 to: {original_br19}")
            
            # Restore BR20 (in case it was affected)
            sheets_client.write_range(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR20", [[original_br20]])
            print(f"  Restored BR20 to: {original_br20}")
            
            # Verify restoration
            restored_br87 = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR87")
            print(f"  BR87 after restoration: {restored_br87}")
            
            print("\n✓ Original values restored!")
