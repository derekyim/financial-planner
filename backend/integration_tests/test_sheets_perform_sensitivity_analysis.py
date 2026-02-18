"""
Integration tests for sensitivity analysis functionality.

These tests perform actual sensitivity analysis on the Google Sheet.
Results are written to a 'sensitivity_table' tab.

NOTE: These are integration tests that require:
1. A valid Google service account credentials file
2. Access to the test spreadsheet
3. Network connectivity

Run with: pytest -m integration
Skip with: pytest -m "not integration"
"""
import os
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.sheets_utilities import SheetsUtilities
from shared.sensitivity_analysis import SensitivityAnalyzer, create_analyzer

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# Test configuration
TEST_SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1yopikoACz8oY32Zv9FrGhb64_PlDwcO1e02WePBr4uM/edit"
TEST_SHEET_NAME = "tests"
OUTPUT_SHEET_NAME = "sensitivity_table"
DEFAULT_API_DELAY = 2
# Path to credentials
CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), "../credentials.json")


@pytest.fixture(scope="module")
def sheets_client() -> SheetsUtilities:
    """Create a SheetsUtilities instance for testing."""
    if not os.path.exists(CREDENTIALS_PATH):
        pytest.skip(f"Credentials file not found at: {CREDENTIALS_PATH}")
    return SheetsUtilities(CREDENTIALS_PATH)


@pytest.fixture(scope="module")
def analyzer(sheets_client: SheetsUtilities) -> SensitivityAnalyzer:
    """Create a SensitivityAnalyzer instance for testing."""
    return SensitivityAnalyzer(sheets_client)


class TestSensitivityAnalyzer:
    """Tests for the SensitivityAnalyzer class."""
    
    def test_generate_multipliers(self, analyzer: SensitivityAnalyzer):
        """Test that multiplier generation produces correct values."""
        multipliers = analyzer._generate_multipliers(
            percent_interval=0.05,
            percent_total_range=0.1
        )
        
        # Should have 5 values: 0.90, 0.95, 1.00, 1.05, 1.10
        assert len(multipliers) == 5, f"Expected 5 multipliers, got {len(multipliers)}"
        
        # Check first, middle, and last values
        assert multipliers[0] == 0.9, f"First multiplier should be 0.9, got {multipliers[0]}"
        assert multipliers[2] == 1.0, f"Middle multiplier should be 1.0, got {multipliers[2]}"
        assert multipliers[4] == 1.1, f"Last multiplier should be 1.1, got {multipliers[4]}"
        
        print(f"Generated multipliers: {multipliers}")
    
    def test_build_cell_reference(self, analyzer: SensitivityAnalyzer):
        """Test cell reference building."""
        assert analyzer._build_cell_reference("BT", 15) == "BT15"
        assert analyzer._build_cell_reference("A", 1) == "A1"
        assert analyzer._build_cell_reference("ZZ", 100) == "ZZ100"
    
    def test_column_to_number(self, analyzer: SensitivityAnalyzer):
        """Test column letter to number conversion."""
        assert analyzer._column_to_number("A") == 1
        assert analyzer._column_to_number("B") == 2
        assert analyzer._column_to_number("Z") == 26
        assert analyzer._column_to_number("AA") == 27
        assert analyzer._column_to_number("AB") == 28
        assert analyzer._column_to_number("AZ") == 52
        assert analyzer._column_to_number("BA") == 53
        assert analyzer._column_to_number("BT") == 72
        assert analyzer._column_to_number("BU") == 73
        assert analyzer._column_to_number("BV") == 74
        print("Column to number conversions verified!")
    
    def test_number_to_column(self, analyzer: SensitivityAnalyzer):
        """Test number to column letter conversion."""
        assert analyzer._number_to_column(1) == "A"
        assert analyzer._number_to_column(2) == "B"
        assert analyzer._number_to_column(26) == "Z"
        assert analyzer._number_to_column(27) == "AA"
        assert analyzer._number_to_column(28) == "AB"
        assert analyzer._number_to_column(52) == "AZ"
        assert analyzer._number_to_column(53) == "BA"
        assert analyzer._number_to_column(72) == "BT"
        assert analyzer._number_to_column(73) == "BU"
        assert analyzer._number_to_column(74) == "BV"
        print("Number to column conversions verified!")
    
    def test_generate_column_range(self, analyzer: SensitivityAnalyzer):
        """Test column range generation."""
        # Single column
        assert analyzer._generate_column_range("BT", "BT") == ["BT"]
        
        # Multi-column range
        assert analyzer._generate_column_range("BT", "BV") == ["BT", "BU", "BV"]
        
        # Longer range
        assert analyzer._generate_column_range("A", "E") == ["A", "B", "C", "D", "E"]
        
        print("Column range generation verified!")
    
    def test_perform_sensitivity_on_test_sheet(self, analyzer: SensitivityAnalyzer):
        """
        Perform full sensitivity analysis on the 'tests' sheet.
        
        Variables:
            - BT15: Input variable 1
            - BT17: Input variable 2
            - BT87: Target/output variable
            
        Parameters:
            - percent_interval: 0.05 (5% steps)
            - percent_total_range: 0.10 (90% to 110%)
            
        Expected: 5 x 5 = 25 result tuples
        """
        print("\n" + "=" * 60)
        print("SENSITIVITY ANALYSIS TEST")
        print("=" * 60)
        
        results = analyzer.perform_sensitivity(
            spreadsheet_url=TEST_SPREADSHEET_URL,
            source_sheet=TEST_SHEET_NAME,
            row_variable_1=15,
            row_variable_2=17,
            row_target=87,
            percent_interval=0.05,
            percent_total_range=0.1,
            start_month="BT",
            end_month="BT",
            output_sheet=OUTPUT_SHEET_NAME,
            api_delay=DEFAULT_API_DELAY  # 10 second delay between API calls
        )
        
        # Verify we got the expected number of results
        expected_count = 5 * 5  # 25 combinations
        assert len(results) == expected_count, \
            f"Expected {expected_count} results, got {len(results)}"
        
        # Verify tuple structure
        assert all(len(r) == 3 for r in results), \
            "All results should be 3-tuples (mult1, mult2, target)"
        
        # Verify all multiplier values are within expected range
        for mult1, mult2, target in results:
            assert 0.9 <= mult1 <= 1.1, f"mult1 out of range: {mult1}"
            assert 0.9 <= mult2 <= 1.1, f"mult2 out of range: {mult2}"
        
        # Print summary statistics
        target_values = [r[2] for r in results]
        print(f"\nResults Summary:")
        print(f"  Total combinations: {len(results)}")
        print(f"  Target min: {min(target_values):.2f}")
        print(f"  Target max: {max(target_values):.2f}")
        print(f"  Target at [1.0, 1.0]: {results[12][2]:.2f}")  # Middle of 25 results
        
        print(f"\n✓ Sensitivity analysis complete!")
        print(f"  Results written to '{OUTPUT_SHEET_NAME}' tab")
    
    def test_perform_sensitivity_multi_column(self, analyzer: SensitivityAnalyzer):
        """
        Perform sensitivity analysis across multiple columns (BT to BV).
        
        This test:
        1. Stores original values for BT15, BU15, BV15 and BT17, BU17, BV17
        2. Applies multipliers to ALL columns simultaneously
        3. Reads only the LAST column's target (BV87) as the result
        4. Restores all original values
        
        Variables:
            - Row 15 across BT:BV: Input variable 1
            - Row 17 across BT:BV: Input variable 2
            - BV87: Target/output variable (last column only)
            
        Parameters:
            - percent_interval: 0.05 (5% steps)
            - percent_total_range: 0.10 (90% to 110%)
            
        Expected: 5 x 5 = 25 result tuples
        """
        print("\n" + "=" * 60)
        print("MULTI-COLUMN SENSITIVITY ANALYSIS TEST (BT to BV)")
        print("=" * 60)
        
        results = analyzer.perform_sensitivity(
            spreadsheet_url=TEST_SPREADSHEET_URL,
            source_sheet=TEST_SHEET_NAME,
            row_variable_1=15,
            row_variable_2=17,
            row_target=87,
            percent_interval=0.05,
            percent_total_range=0.1,
            start_month="BT",
            end_month="CD",  # Multi-column: BT, BU, BV
            output_sheet="sensitivity_table_multi",
            api_delay=DEFAULT_API_DELAY
        )
        
        # Verify we got the expected number of results
        expected_count = 5 * 5  # 25 combinations
        assert len(results) == expected_count, \
            f"Expected {expected_count} results, got {len(results)}"
        
        # Verify tuple structure
        assert all(len(r) == 3 for r in results), \
            "All results should be 3-tuples (mult1, mult2, target)"
        
        # Verify all multiplier values are within expected range
        for mult1, mult2, target in results:
            assert 0.9 <= mult1 <= 1.1, f"mult1 out of range: {mult1}"
            assert 0.9 <= mult2 <= 1.1, f"mult2 out of range: {mult2}"
        
        # Print summary statistics
        target_values = [r[2] for r in results]
        print(f"\nResults Summary:")
        print(f"  Columns analyzed: BT, BU, BV")
        print(f"  Target cell: BV87 (last column)")
        print(f"  Total combinations: {len(results)}")
        print(f"  Target min: {min(target_values):.2f}")
        print(f"  Target max: {max(target_values):.2f}")
        print(f"  Target at [1.0, 1.0]: {results[12][2]:.2f}")  # Middle of 25 results
        
        print(f"\n✓ Multi-column sensitivity analysis complete!")
        print(f"  Results written to 'sensitivity_table_multi' tab")


class TestSensitivityAnalyzerFactory:
    """Tests for the factory function."""
    
    def test_create_analyzer(self):
        """Test that create_analyzer works with valid credentials."""
        if not os.path.exists(CREDENTIALS_PATH):
            pytest.skip(f"Credentials file not found at: {CREDENTIALS_PATH}")
        
        analyzer = create_analyzer(CREDENTIALS_PATH)
        assert isinstance(analyzer, SensitivityAnalyzer)
        assert analyzer.sheets is not None
