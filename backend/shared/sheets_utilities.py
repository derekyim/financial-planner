import logging
import os
import re
from typing import Optional

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

log = logging.getLogger(__name__)


class StorageQuotaError(Exception):
    """Raised when the service account has no Drive storage for file creation."""


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
        self._drive_service = None
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

    def create_line_chart(
        self,
        spreadsheet_url: str,
        source_sheet_name: str,
        title: str,
        domain_row: int,
        series_rows: list[int],
        series_labels: list[str],
        start_col: int,
        end_col: int,
        chart_sheet_name: str = "Charts",
    ) -> str:
        """Create a line chart on a new or existing 'Charts' tab.

        Uses the Google Sheets API batchUpdate (addChart) since gspread
        doesn't support chart creation directly.

        Args:
            spreadsheet_url: Full Google Sheets URL.
            source_sheet_name: Tab containing the data (e.g., "operations").
            title: Chart title.
            domain_row: 0-based row index for the X-axis labels (date spine).
            series_rows: List of 0-based row indices for each data series.
            series_labels: Display labels for each series.
            start_col: 0-based start column index for the data range.
            end_col: 0-based end column index (exclusive).
            chart_sheet_name: Name of the tab to place the chart on.

        Returns:
            Confirmation message with the chart tab name.
        """
        spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
        spreadsheet = self.client.open_by_key(spreadsheet_id)

        source_ws = spreadsheet.worksheet(source_sheet_name)
        source_sheet_id = source_ws.id

        try:
            chart_ws = spreadsheet.worksheet(chart_sheet_name)
            chart_sheet_id = chart_ws.id
        except gspread.exceptions.WorksheetNotFound:
            chart_ws = spreadsheet.add_worksheet(
                title=chart_sheet_name, rows=1, cols=1
            )
            chart_sheet_id = chart_ws.id

        def _row_range(row_idx: int) -> dict:
            return {
                "sheetId": source_sheet_id,
                "startRowIndex": row_idx,
                "endRowIndex": row_idx + 1,
                "startColumnIndex": start_col,
                "endColumnIndex": end_col,
            }

        series_specs = []
        for i, row_idx in enumerate(series_rows):
            spec: dict = {
                "series": {
                    "sourceRange": {"sources": [_row_range(row_idx)]}
                },
                "targetAxis": "LEFT_AXIS",
                "type": "LINE",
            }
            series_specs.append(spec)

        body = {
            "requests": [
                {
                    "addChart": {
                        "chart": {
                            "spec": {
                                "title": title,
                                "basicChart": {
                                    "chartType": "LINE",
                                    "legendPosition": "BOTTOM_LEGEND",
                                    "axis": [
                                        {
                                            "position": "BOTTOM_AXIS",
                                            "title": "Date",
                                        },
                                        {
                                            "position": "LEFT_AXIS",
                                            "title": "Value",
                                        },
                                    ],
                                    "domains": [
                                        {
                                            "domain": {
                                                "sourceRange": {
                                                    "sources": [
                                                        _row_range(domain_row)
                                                    ]
                                                }
                                            }
                                        }
                                    ],
                                    "series": series_specs,
                                    "headerCount": 0,
                                },
                            },
                            "position": {
                                "overlayPosition": {
                                    "anchorCell": {
                                        "sheetId": chart_sheet_id,
                                        "rowIndex": 0,
                                        "columnIndex": 0,
                                    },
                                    "widthPixels": 1200,
                                    "heightPixels": 600,
                                }
                            },
                        }
                    }
                }
            ]
        }

        spreadsheet.batch_update(body)
        return chart_sheet_name

    def _get_drive_service(self):
        """Lazily build and cache a Drive v3 service."""
        if self._drive_service is None:
            credentials = Credentials.from_service_account_file(
                self.credentials_path, scopes=self.SCOPES
            )
            self._drive_service = build("drive", "v3", credentials=credentials)
        return self._drive_service

    def _share_file(self, file_id: str) -> None:
        """Share a file with EMAIL_TO_SHARE_SLIDES_TO if set, otherwise make it link-accessible."""
        drive = self._get_drive_service()
        share_email = os.getenv("EMAIL_TO_SHARE_SLIDES_TO", "")
        if share_email:
            drive.permissions().create(
                fileId=file_id,
                body={"type": "user", "role": "writer", "emailAddress": share_email},
                fields="id",
                sendNotificationEmail=False,
            ).execute()
        else:
            drive.permissions().create(
                fileId=file_id,
                body={"type": "anyone", "role": "writer"},
                fields="id",
            ).execute()

    def copy_spreadsheet(self, source_url: str, new_name: str) -> str:
        """Copy a Google Sheets spreadsheet to a new file.

        Places the copy in the same parent folder as the original.
        If the service account has no Drive storage (common on free-tier GCP),
        raises ``StorageQuotaError`` with guidance.

        Args:
            source_url: Full URL of the spreadsheet to copy.
            new_name: Name for the new copy.

        Returns:
            The full URL of the newly created spreadsheet.

        Raises:
            StorageQuotaError: When the service account has no Drive storage.
        """
        from googleapiclient.errors import HttpError

        source_id = self._extract_spreadsheet_id(source_url)
        drive = self._get_drive_service()

        try:
            source_meta = drive.files().get(
                fileId=source_id, fields="parents"
            ).execute()
        except HttpError:
            source_meta = {}

        parents = source_meta.get("parents", [])
        copy_body: dict = {"name": new_name}
        if parents:
            copy_body["parents"] = parents

        try:
            copied = drive.files().copy(
                fileId=source_id,
                body=copy_body,
            ).execute()
        except HttpError as exc:
            if "storageQuotaExceeded" in str(exc):
                raise StorageQuotaError(
                    "The service account has no Drive storage (0-byte limit on "
                    "free-tier GCP projects). To enable copy_spreadsheet:\n"
                    "  1. Use a Google Workspace account with domain-wide "
                    "delegation, OR\n"
                    "  2. Upgrade the GCP project to provide the service "
                    "account with Drive storage."
                ) from exc
            raise

        new_id = copied["id"]
        new_url = f"https://docs.google.com/spreadsheets/d/{new_id}/edit"
        self._share_file(new_id)
        log.info("Copied spreadsheet %s → '%s' (%s)", source_id, new_name, new_id)
        return new_url

    def export_all_tabs(self, spreadsheet_url: str) -> list[dict]:
        """
        Export every tab with formulas preserved (for loading into a calc engine).

        Returns a list of dicts: [{"name": "Sheet1", "data": [[cell, ...], ...]}, ...]
        Each cell is either a formula string (starting with '=') or its computed value.
        """
        spreadsheet_id = self._extract_spreadsheet_id(spreadsheet_url)
        spreadsheet = self.client.open_by_key(spreadsheet_id)
        result = []
        for ws in spreadsheet.worksheets():
            formulas = ws.get_all_values(value_render_option='FORMULA')
            result.append({"name": ws.title, "data": formulas})
        return result
