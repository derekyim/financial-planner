"""
Sensitivity analysis module for Google Sheets.

Performs two-variable sensitivity analysis by varying input cells
and capturing the effect on a target cell.
"""
import os
import time
from typing import Optional
from shared.sheets_utilities import SheetsUtilities

# Default delay between API calls to avoid rate limiting (in seconds)
DEFAULT_API_DELAY = 2


class SensitivityAnalyzer:
    """Performs sensitivity analysis on Google Sheets data."""
    
    def __init__(self, sheets_client: SheetsUtilities):
        """
        Initialize with an authenticated SheetsUtilities client.
        
        Args:
            sheets_client: Authenticated SheetsUtilities instance
        """
        self.sheets = sheets_client
    
    def _generate_multipliers(self, percent_interval: float, percent_total_range: float) -> list[float]:
        """
        Generate list of multipliers for sensitivity analysis.
        
        Args:
            percent_interval: Step size between multipliers (e.g., 0.05 for 5%)
            percent_total_range: Total range from 1.0 (e.g., 0.25 for 75% to 125%)
            
        Returns:
            List of multipliers, e.g., [0.75, 0.80, 0.85, ..., 1.20, 1.25]
        """
        multipliers = []
        current = 1.0 - percent_total_range
        end = 1.0 + percent_total_range
        
        while current <= end + 0.0001:  # Small epsilon for floating point
            multipliers.append(round(current, 4))
            current += percent_interval
        
        return multipliers
    
    def _build_cell_reference(self, column: str, row: int) -> str:
        """Build A1 notation cell reference from column and row."""
        return f"{column}{row}"
    
    def _column_to_number(self, column: str) -> int:
        """
        Convert Excel-style column letter to number.
        A=1, B=2, ..., Z=26, AA=27, AB=28, ..., BT=72, etc.
        """
        result = 0
        for char in column.upper():
            result = result * 26 + (ord(char) - ord('A') + 1)
        return result
    
    def _number_to_column(self, number: int) -> str:
        """
        Convert number to Excel-style column letter.
        1=A, 2=B, ..., 26=Z, 27=AA, 28=AB, ..., 72=BT, etc.
        """
        result = ""
        while number > 0:
            number, remainder = divmod(number - 1, 26)
            result = chr(ord('A') + remainder) + result
        return result
    
    def _generate_column_range(self, start_col: str, end_col: str) -> list[str]:
        """
        Generate list of columns from start to end (inclusive).
        
        Args:
            start_col: Starting column (e.g., 'BT')
            end_col: Ending column (e.g., 'BV')
            
        Returns:
            List of columns, e.g., ['BT', 'BU', 'BV']
        """
        start_num = self._column_to_number(start_col)
        end_num = self._column_to_number(end_col)
        
        return [self._number_to_column(i) for i in range(start_num, end_num + 1)]
    
    def perform_sensitivity(
        self,
        spreadsheet_url: str,
        source_sheet: str,
        row_variable_1: int,
        row_variable_2: int,
        row_target: int,
        percent_interval: float,
        percent_total_range: float,
        start_month: str,
        end_month: str,
        output_sheet: str = "sensitivity_table",
        api_delay: float = DEFAULT_API_DELAY
    ) -> list[tuple[float, float, float]]:
        """
        Perform two-variable sensitivity analysis.
        
        Varies two input cells across a range of multipliers and captures
        the effect on a target cell. Results are written to an output sheet.
        
        Args:
            spreadsheet_url: Full Google Sheets URL
            source_sheet: Name of the tab containing the model
            row_variable_1: Row number for first input variable
            row_variable_2: Row number for second input variable
            row_target: Row number for target/output variable
            percent_interval: Step size between multipliers (e.g., 0.05)
            percent_total_range: Total range from 1.0 (e.g., 0.25)
            start_month: Starting column letter for analysis (e.g., 'BT')
            end_month: Ending column letter (e.g., 'BV'). Can be same as start_month for single column.
            output_sheet: Name of tab to write results (default: 'sensitivity_table')
            api_delay: Seconds to wait between API calls to avoid rate limiting (default: 10)
            
        Returns:
            List of tuples: (multiplier_1, multiplier_2, target_value)
        """
        # Generate column range
        columns = self._generate_column_range(start_month, end_month)
        target_column = columns[-1]  # Use last column for target value
        
        # Build range references for batch read/write
        range_var1 = f"{start_month}{row_variable_1}:{end_month}{row_variable_1}"
        range_var2 = f"{start_month}{row_variable_2}:{end_month}{row_variable_2}"
        
        print(f"Sensitivity Analysis Setup:")
        print(f"  Columns: {columns}")
        print(f"  Variable 1 range: {range_var1}")
        print(f"  Variable 2 range: {range_var2}")
        print(f"  Target: {target_column}{row_target}")
        
        # Read original values as ranges (single API call each)
        raw_var1 = self.sheets.read_range(spreadsheet_url, source_sheet, range_var1)
        time.sleep(api_delay)
        raw_var2 = self.sheets.read_range(spreadsheet_url, source_sheet, range_var2)
        time.sleep(api_delay)
        
        # Convert to list of floats (range returns [[val1, val2, val3]])
        original_values_var1: list[float] = [
            float(str(v).replace(',', '')) for v in raw_var1[0]
        ]
        original_values_var2: list[float] = [
            float(str(v).replace(',', '')) for v in raw_var2[0]
        ]
        
        print(f"  Original row {row_variable_1} values: {original_values_var1}")
        print(f"  Original row {row_variable_2} values: {original_values_var2}")
        
        # Generate multipliers
        multipliers = self._generate_multipliers(percent_interval, percent_total_range)
        print(f"  Multipliers: {multipliers}")
        print(f"  Total combinations: {len(multipliers) ** 2}")
        
        # Results storage
        results: list[tuple[float, float, float]] = []
        
        # Matrix for output (with headers)
        output_matrix = []
        
        # Header row: corner label + multiplier_2 values
        header_label = f"Row{row_variable_1}\\Row{row_variable_2}"
        header_row = [header_label] + [str(m) for m in multipliers]
        output_matrix.append(header_row)
        
        # Cell reference for target (last column)
        cell_target = self._build_cell_reference(target_column, row_target)
        
        try:
            for mult1 in multipliers:
                # Apply multiplier 1 to ALL columns in row_variable_1 (single API call)
                new_values_var1 = [[v * mult1 for v in original_values_var1]]
                self.sheets.write_range(spreadsheet_url, source_sheet, range_var1, new_values_var1)
                time.sleep(api_delay)
                
                # Row for this multiplier_1 value
                result_row = [str(mult1)]
                
                for mult2 in multipliers:
                    # Apply multiplier 2 to ALL columns in row_variable_2 (single API call)
                    new_values_var2 = [[v * mult2 for v in original_values_var2]]
                    self.sheets.write_range(spreadsheet_url, source_sheet, range_var2, new_values_var2)
                    time.sleep(api_delay)
                    
                    # Read target value (from LAST column only)
                    target_value = self.sheets.read_cell(spreadsheet_url, source_sheet, cell_target)
                    time.sleep(api_delay)
                    target_float = float(str(target_value).replace(',', ''))
                    
                    # Store result
                    results.append((mult1, mult2, target_float))
                    result_row.append(str(round(target_float, 2)))
                    
                    print(f"  [{mult1:.2f}, {mult2:.2f}] -> {target_float:.2f}")
                
                output_matrix.append(result_row)
            
            # Write results to output sheet
            print(f"\nWriting results to '{output_sheet}' tab...")
            self._write_results(spreadsheet_url, output_sheet, output_matrix)
            time.sleep(api_delay)
            print(f"  Wrote {len(results)} results")
            
        finally:
            # Restore ALL original values (single API call per row)
            print("\nRestoring original values...")
            self.sheets.write_range(spreadsheet_url, source_sheet, range_var1, [original_values_var1])
            time.sleep(api_delay)
            self.sheets.write_range(spreadsheet_url, source_sheet, range_var2, [original_values_var2])
            time.sleep(api_delay)
            print(f"  Restored {range_var1} to {original_values_var1}")
            print(f"  Restored {range_var2} to {original_values_var2}")
        
        return results
    
    def _write_results(self, spreadsheet_url: str, sheet_name: str, matrix: list[list[str]]) -> None:
        """
        Write results matrix to a sheet.
        
        Creates the sheet if it doesn't exist, or clears and rewrites if it does.
        
        Args:
            spreadsheet_url: Full Google Sheets URL
            sheet_name: Name of the tab to write to
            matrix: 2D list of values to write
        """
        spreadsheet_id = self.sheets._extract_spreadsheet_id(spreadsheet_url)
        spreadsheet = self.sheets.client.open_by_key(spreadsheet_id)
        
        # Try to get existing worksheet, or create new one
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            worksheet.clear()
        except Exception:
            # Worksheet doesn't exist, create it
            worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=len(matrix) + 10, cols=len(matrix[0]) + 10)
        
        # Write the matrix
        worksheet.update(range_name='A1', values=matrix)


def create_analyzer(credentials_path: str) -> SensitivityAnalyzer:
    """
    Factory function to create a SensitivityAnalyzer with credentials.
    
    Args:
        credentials_path: Path to Google service account JSON file
        
    Returns:
        Configured SensitivityAnalyzer instance
    """
    sheets = SheetsUtilities(credentials_path)
    return SensitivityAnalyzer(sheets)
