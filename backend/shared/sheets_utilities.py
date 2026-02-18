import re
from typing import Optional
import gspread
from google.oauth2.service_account import Credentials

class SheetsUtilities:
    """Utility class for reading and writing Google Sheets using a service account."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    def __init__(self, credentials_path: str):
        """
        Initialize with path to service account JSON credentials file.
        
        Args:
            credentials_path: Path to the service account JSON file
        """
        self.credentials_path = credentials_path
        self.client: Optional[gspread.Client] = None
        self.authenticate()
    
    def authenticate(self) -> gspread.Client:
        """
        Authenticate with Google Sheets API using service account credentials.
        
        Returns:
            Authenticated gspread client
        """
        credentials = Credentials.from_service_account_file(
            self.credentials_path,
            scopes=self.SCOPES
        )
        self.client = gspread.authorize(credentials)
        return self.client
    
    def _extract_spreadsheet_id(self, spreadsheet_url: str) -> str:
        """
        Extract the spreadsheet ID from a Google Sheets URL.
        
        Args:
            spreadsheet_url: Full Google Sheets URL
            
        Returns:
            The spreadsheet ID string
        """
        # Pattern matches the ID between /d/ and the next /
        pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
        match = re.search(pattern, spreadsheet_url)
        if not match:
            raise ValueError(f"Could not extract spreadsheet ID from URL: {spreadsheet_url}")
        return match.group(1)
    
    def read_sheet(self, spreadsheet_url: str, sheet_name: str) -> list[list]:
        """
        Read all values from a specific sheet/tab.
        
        Args:
            spreadsheet_url: Full Google Sheets URL
            sheet_name: Name of the tab to read
            
        Returns:
            List of lists containing all cell values
        """
        spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.get_all_values()
    
    def write_sheet(self, spreadsheet_url: str, sheet_name: str, values: list[list]) -> None:
        """
        Write values to a sheet, replacing all existing content.
        Starts writing from cell A1.
        
        Args:
            spreadsheet_url: Full Google Sheets URL
            sheet_name: Name of the tab to write to
            values: List of lists containing values to write
        """
        spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        
        # Clear existing content and write new values
        worksheet.clear()
        if values:
            worksheet.update(range_name='A1', values=values)
    
    def read_range(self, spreadsheet_url: str, sheet_name: str, range_notation: str) -> list[list]:
        """
        Read values from a specific range.
        
        Args:
            spreadsheet_url: Full Google Sheets URL
            sheet_name: Name of the tab to read from
            range_notation: A1 notation for the range (e.g., 'A1:C10')
            
        Returns:
            List of lists containing cell values in the range
        """
        spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.get(range_notation)
    
    def write_range(self, spreadsheet_url: str, sheet_name: str, range_notation: str, values: list[list]) -> None:
        """
        Write values to a specific range.
        
        Args:
            spreadsheet_url: Full Google Sheets URL
            sheet_name: Name of the tab to write to
            range_notation: A1 notation for the starting range (e.g., 'A1' or 'B2:D5')
            values: List of lists containing values to write
        """
        spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        worksheet.update(range_name=range_notation, values=values)
    
    def read_cell(self, spreadsheet_url: str, sheet_name: str, cell_notation: str) -> str:
        """
        Read a single cell value.
        
        Args:
            spreadsheet_url: Full Google Sheets URL
            sheet_name: Name of the tab to read from
            cell_notation: A1 notation for the cell (e.g., 'C14')
            
        Returns:
            The cell value as a string
        """
        spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.acell(cell_notation).value
    
    def read_cell_formula(self, spreadsheet_url: str, sheet_name: str, cell_notation: str) -> str:
        """
        Read a cell's formula (not its computed value).
        
        Args:
            spreadsheet_url: Full Google Sheets URL
            sheet_name: Name of the tab to read from
            cell_notation: A1 notation for the cell (e.g., 'BR21')
            
        Returns:
            The cell formula as a string (e.g., '=BR20+BR14')
        """
        spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)
        return worksheet.acell(cell_notation, value_render_option='FORMULA').value
