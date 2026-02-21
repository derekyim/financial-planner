"""Pytest fixtures for financial agent tests.

Provides mock sheets client, memory stores, and sample data fixtures.
"""

import pytest
from unittest.mock import MagicMock, patch
from langgraph.store.memory import InMemoryStore

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires credentials/network)"
    )


def pytest_collection_modifyitems(config, items):
    """Skip integration tests by default unless -m integration is specified."""
    # If -m integration was passed, don't skip anything
    if config.getoption("-m") and "integration" in config.getoption("-m"):
        return
    
    skip_integration = pytest.mark.skip(reason="Integration test - run with: pytest -m integration")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


# Sample model documentation for testing
SAMPLE_MODEL_DOCUMENTATION = """
=== MODELING CONVENTIONS ===
This is a 3 statement model for historical "Actual" and future "Forecast" periods.
Column A contains markers for if something is an Input (contains • )
Column A contains markers for if something is a driver of high importance (marked with "Key Driver")
Column A contains markers for if something is a result of high importance (marked with "Key Result")
Column B contains the "durable_ids", a set of ids for each driver or result
Column C contains the "Friendly Name" of a Driver or Metric
Column K is the FIRST column of the date spine
Row 2 contains the date spine
Row 3 contains if this period is an "Actual" or historical value or a "Forecast" value

=== CRITICAL FORMULAS ===
==== EBITDA ====
Location: 'operations'!Row 194  |  Formula: =Row191 + Row192 + Row193
EBITDA = EBIT + Depreciation + Amortization
"""

# Sample key drivers and results data
SAMPLE_KEY_DRIVERS_DATA = [
    ["", "durable_id", "Name", "", "", "", "", "", "", "", "Jan-25", "Feb-25", "Mar-25"],
    ["Key Driver", "orders", "Orders", "", "", "", "", "", "", "", "221207", "225000", "230000"],
    ["Key Driver", "aov", "AoV (Average Order Value)", "", "", "", "", "", "", "", "75.40", "76.00", "77.00"],
    ["Key Driver", "cac", "CaC (Custom Acquisition Cost)", "", "", "", "", "", "", "", "43.50", "42.00", "41.00"],
    ["Key Result", "gross_sales", "Gross Sales", "", "", "", "", "", "", "", "21346139", "22000000", "23000000"],
    ["Key Result", "ebitda", "EBITDA", "", "", "", "", "", "", "", "1228810", "1300000", "1400000"],
    ["Key Result", "cash", "Cash", "", "", "", "", "", "", "", "1285003", "1350000", "1420000"],
]

# Sample operations data
SAMPLE_M_MONTHLY_DATA = [
    ["", "", ""],
    ["", "", "", "", "", "", "", "", "", "", "Jan-25", "Feb-25", "Mar-25"],
    ["", "", "", "", "", "", "", "", "", "", "Actual", "Actual", "Forecast"],
]


@pytest.fixture
def mock_sheets_client():
    """Create a mock SheetsUtilities client."""
    mock_client = MagicMock()
    
    def mock_read_sheet(url, sheet_name):
        if sheet_name == "Model Documentation":
            return [[line] for line in SAMPLE_MODEL_DOCUMENTATION.split("\n")]
        elif sheet_name == "Key Drivers and Results":
            return SAMPLE_KEY_DRIVERS_DATA
        elif sheet_name == "operations":
            return SAMPLE_M_MONTHLY_DATA
        elif sheet_name == "AuditLog":
            return [["Timestamp", "Requested By", "Status", "Description", "Data"]]
        elif sheet_name == "Tasks":
            return [["Timestamp", "Requested By", "Status", "Description", "Data"]]
        return []
    
    def mock_read_cell(url, sheet_name, cell_notation):
        cell_values = {
            ("operations", "K194"): "1228810",
            ("operations", "K191"): "1200000",
            ("operations", "K192"): "15000",
            ("operations", "K193"): "13810",
            ("operations", "K92"): "21346139",
        }
        return cell_values.get((sheet_name, cell_notation), "0")
    
    def mock_read_cell_formula(url, sheet_name, cell_notation):
        formulas = {
            ("operations", "K194"): "=K191+K192+K193",
            ("operations", "K92"): "=K80+K81",
        }
        return formulas.get((sheet_name, cell_notation), "")
    
    def mock_read_range(url, sheet_name, range_notation):
        if "A3:BZ3" in range_notation:
            return [["", "", ""] + ["Actual"] * 10 + ["Forecast"] * 10]
        return [[]]
    
    mock_client.read_sheet = mock_read_sheet
    mock_client.read_cell = mock_read_cell
    mock_client.read_cell_formula = mock_read_cell_formula
    mock_client.read_range = mock_read_range
    mock_client.write_range = MagicMock(return_value=None)
    mock_client._extract_spreadsheet_id = MagicMock(return_value="test_spreadsheet_id")
    
    return mock_client


@pytest.fixture
def memory_store():
    """Create an in-memory store for testing."""
    return InMemoryStore()


@pytest.fixture
def sample_spreadsheet_url():
    """Return a sample spreadsheet URL for testing."""
    return "https://docs.google.com/spreadsheets/d/test_id/edit"


@pytest.fixture
def mock_tools_initialized(mock_sheets_client, sample_spreadsheet_url):
    """Initialize tools with mock client."""
    with patch("agents.tools._sheets_client", mock_sheets_client):
        with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
            yield


@pytest.fixture
def sample_key_drivers():
    """Return sample Key Driver data."""
    return [
        {"id": "orders", "name": "Orders", "value": "221207", "cell": "K5"},
        {"id": "aov", "name": "AoV (Average Order Value)", "value": "75.40", "cell": "K6"},
        {"id": "cac", "name": "CaC (Custom Acquisition Cost)", "value": "43.50", "cell": "K7"},
    ]


@pytest.fixture
def sample_key_results():
    """Return sample Key Result data."""
    return [
        {"id": "gross_sales", "name": "Gross Sales", "value": "21346139", "cell": "K92"},
        {"id": "ebitda", "name": "EBITDA", "value": "1228810", "cell": "K194"},
        {"id": "cash", "name": "Cash", "value": "1285003", "cell": "K200"},
    ]
