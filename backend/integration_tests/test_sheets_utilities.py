"""
Integration tests for SheetsUtilities class.

These tests read from an actual Google Sheet to verify the functionality.
Requires:
    - Valid service account credentials file
    - The Google Sheet shared with the service account email

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
TEST_SHEET_NAME = "operations"


CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "../credentials.json")

# breakpoint()
print(f"Credentials path: {CREDENTIALS_PATH}")

@pytest.fixture(scope="module")
def sheets_client() -> SheetsUtilities:
    """
    Create a SheetsUtilities instance for testing.
    Scoped to module so we only authenticate once for all tests.
    """
    print(f"Credentials path: {CREDENTIALS_PATH}")
    if not os.path.exists(CREDENTIALS_PATH):
        pytest.skip(f"Credentials file not found at: {CREDENTIALS_PATH}")
    return SheetsUtilities(CREDENTIALS_PATH)


class TestSheetsUtilitiesRead:
    """Tests for reading operations from the Google Sheet."""
    
    def test_read_cell_c14_is_orders(self, sheets_client: SheetsUtilities):
        """Verify that cell C14 in the operations tab contains 'Orders'."""
        value = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "C14")
        assert value == "Orders", f"Expected 'Orders' in C14, got '{value}'"
    
    def test_read_cell_br14_is_12818(self, sheets_client: SheetsUtilities):
        """Verify that cell BR14 in the operations tab contains 12818."""
        value = sheets_client.read_cell(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR14")
        # Cell value might come back as string, so compare both ways
        assert value == "12818" or value == 12818, f"Expected 12818 in BR14, got '{value}'"
    
    def test_read_cell_br21_formula(self, sheets_client: SheetsUtilities):
        """Verify that cell BR21 contains the formula '=BR20+BR14'."""
        formula = sheets_client.read_cell_formula(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "BR21")
        assert formula == "=BR20+BR14", f"Expected '=BR20+BR14' in BR21, got '{formula}'"
    
    def test_read_range_returns_list_of_lists(self, sheets_client: SheetsUtilities):
        """Verify that read_range returns data in the expected format."""
        data = sheets_client.read_range(TEST_SPREADSHEET_URL, TEST_SHEET_NAME, "A1:C3")
        assert isinstance(data, list), "read_range should return a list"
        assert len(data) > 0, "read_range should return non-empty data"
        assert isinstance(data[0], list), "read_range should return a list of lists"
    
    def test_read_sheet_returns_all_data(self, sheets_client: SheetsUtilities):
        """Verify that read_sheet returns the entire sheet data."""
        data = sheets_client.read_sheet(TEST_SPREADSHEET_URL, TEST_SHEET_NAME)
        assert isinstance(data, list), "read_sheet should return a list"
        assert len(data) > 0, "read_sheet should return non-empty data"
        # The operations sheet should have at least 21 rows (since we check BR21)
        assert len(data) >= 21, f"Expected at least 21 rows, got {len(data)}"


class TestSheetsUtilitiesURLParsing:
    """Tests for URL parsing functionality."""
    
    def test_extract_spreadsheet_id_valid_url(self, sheets_client: SheetsUtilities):
        """Verify spreadsheet ID extraction from a valid URL."""
        url = "https://docs.google.com/spreadsheets/d/1yopikoACz8oY32Zv9FrGhb64_PlDwcO1e02WePBr4uM/edit?gid=123"
        spreadsheet_id = sheets_client._extract_spreadsheet_id(url)
        assert spreadsheet_id == "1yopikoACz8oY32Zv9FrGhb64_PlDwcO1e02WePBr4uM"
    
    def test_extract_spreadsheet_id_invalid_url(self, sheets_client: SheetsUtilities):
        """Verify that invalid URLs raise ValueError."""
        with pytest.raises(ValueError):
            sheets_client._extract_spreadsheet_id("https://google.com/not-a-sheet")
