"""
Integration test for SheetsUtilities.copy_spreadsheet().

Copies a real Google Sheet, verifies the copy exists and has data,
then deletes the copy to clean up.

Requires:
    - Valid service account credentials file at ../credentials.json
    - The source Google Sheet shared with the service account email
    - SPREADSHEET_URL env var (or .env file) pointing to the source sheet

Run with: pytest integration_tests/test_copy_spreadsheet.py -m integration -v
"""
import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.config import load_env
load_env()

from shared.sheets_utilities import SheetsUtilities, StorageQuotaError

pytestmark = pytest.mark.integration

SOURCE_SPREADSHEET_URL = os.getenv(
    "SPREADSHEET_URL",
    "https://docs.google.com/spreadsheets/d/"
    "16c6izAKDmyJ3lTR_xXnvsUnOJslxvnTxUwbDmlv8aFI/edit",
)
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "../credentials.json")


@pytest.fixture(scope="module")
def sheets_client() -> SheetsUtilities:
    if not os.path.exists(CREDENTIALS_PATH):
        pytest.skip(f"Credentials file not found at: {CREDENTIALS_PATH}")
    return SheetsUtilities(CREDENTIALS_PATH)


class TestCopySpreadsheet:
    """Tests for copying a Google Sheets spreadsheet via Drive API."""

    def test_copy_spreadsheet_creates_accessible_copy(self, sheets_client: SheetsUtilities):
        """Copy the Powdered Drink City model, verify it, then delete it."""
        timestamp = datetime.now().strftime("%Y-%m-%d:%H:%M:%S")
        new_name = f"Powdered Drink City - Financial Model - TEST-{timestamp}"

        # --- Copy ---
        try:
            new_url = sheets_client.copy_spreadsheet(SOURCE_SPREADSHEET_URL, new_name)
        except StorageQuotaError:
            pytest.skip(
                "Service account has 0-byte Drive storage (free-tier GCP). "
                "Copy requires a Workspace account with domain-wide delegation "
                "or a GCP project that grants the SA Drive storage."
            )

        new_id = sheets_client._extract_spreadsheet_id(new_url)

        try:
            assert new_url.startswith("https://docs.google.com/spreadsheets/d/")
            assert new_id != sheets_client._extract_spreadsheet_id(SOURCE_SPREADSHEET_URL)

            # --- Verify the copy has real data ---
            value = sheets_client.read_cell(new_url, "operations", "C14")
            assert value == "Orders", f"Expected 'Orders' in C14 of copy, got '{value}'"

            tabs = [ws.title for ws in sheets_client.client.open_by_key(new_id).worksheets()]
            assert "operations" in tabs, f"'operations' tab missing. Tabs: {tabs}"

            print(f"\nCopy created successfully: {new_name}")
            print(f"URL: {new_url}")
            print(f"Tabs: {tabs}")

        finally:
            # --- Cleanup: delete the copy ---
            drive = sheets_client._get_drive_service()
            drive.files().delete(fileId=new_id).execute()
            print(f"Cleaned up test copy: {new_id}")
