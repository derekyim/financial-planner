"""Unit tests for Google Sheets tool wrappers."""

import pytest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.tools import (
    read_model_documentation,
    read_key_drivers_and_results,
    read_cell_value,
    read_cell_formula,
    trace_formula_chain,
    find_forecast_columns,
    _index_to_column,
    initialize_tools,
)


class TestIndexToColumn:
    """Tests for column index conversion."""

    def test_single_letter_columns(self):
        """Test conversion of single letter columns."""
        assert _index_to_column(0) == "A"
        assert _index_to_column(1) == "B"
        assert _index_to_column(25) == "Z"

    def test_double_letter_columns(self):
        """Test conversion of double letter columns."""
        assert _index_to_column(26) == "AA"
        assert _index_to_column(27) == "AB"
        assert _index_to_column(51) == "AZ"
        assert _index_to_column(52) == "BA"

    def test_triple_letter_columns(self):
        """Test conversion of triple letter columns."""
        # 26 + 26*26 = 702 is "AAA"
        assert _index_to_column(702) == "AAA"


class TestReadModelDocumentation:
    """Tests for read_model_documentation tool."""

    def test_reads_documentation_successfully(self, mock_sheets_client, sample_spreadsheet_url):
        """Test that documentation is read and formatted correctly."""
        with patch("agents.tools._sheets_client", mock_sheets_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                result = read_model_documentation.invoke({})
                
                assert "MODELING CONVENTIONS" in result
                assert "CRITICAL FORMULAS" in result
                assert "EBITDA" in result

    def test_handles_error_gracefully(self, sample_spreadsheet_url):
        """Test error handling when sheets client fails."""
        mock_client = MagicMock()
        mock_client.read_sheet.side_effect = Exception("API Error")
        
        with patch("agents.tools._sheets_client", mock_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                result = read_model_documentation.invoke({})
                
                assert "Error reading Model Documentation" in result


class TestReadKeyDriversAndResults:
    """Tests for read_key_drivers_and_results tool."""

    def test_reads_key_metrics(self, mock_sheets_client, sample_spreadsheet_url):
        """Test that Key Drivers and Results are read correctly."""
        with patch("agents.tools._sheets_client", mock_sheets_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                result = read_key_drivers_and_results.invoke({})
                
                assert "Orders" in result
                assert "AoV" in result
                assert "Gross Sales" in result
                assert "EBITDA" in result


class TestReadCellValue:
    """Tests for read_cell_value tool."""

    def test_reads_cell_value(self, mock_sheets_client, sample_spreadsheet_url):
        """Test reading a specific cell value."""
        with patch("agents.tools._sheets_client", mock_sheets_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                result = read_cell_value.invoke({
                    "sheet_name": "operations",
                    "cell_notation": "K194"
                })
                
                assert "operations!K194" in result
                assert "1228810" in result


class TestReadCellFormula:
    """Tests for read_cell_formula tool."""

    def test_reads_formula(self, mock_sheets_client, sample_spreadsheet_url):
        """Test reading a cell formula."""
        with patch("agents.tools._sheets_client", mock_sheets_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                result = read_cell_formula.invoke({
                    "sheet_name": "operations",
                    "cell_notation": "K194"
                })
                
                assert "=K191+K192+K193" in result

    def test_handles_static_value(self, mock_sheets_client, sample_spreadsheet_url):
        """Test handling cells with static values (no formula)."""
        mock_sheets_client.read_cell_formula = MagicMock(return_value="1000")
        
        with patch("agents.tools._sheets_client", mock_sheets_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                result = read_cell_formula.invoke({
                    "sheet_name": "operations",
                    "cell_notation": "K5"
                })
                
                assert "static value" in result


class TestFindForecastColumns:
    """Tests for find_forecast_columns tool."""

    def test_finds_forecast_columns(self, mock_sheets_client, sample_spreadsheet_url):
        """Test finding forecast period columns."""
        with patch("agents.tools._sheets_client", mock_sheets_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                result = find_forecast_columns.invoke({})
                
                assert "Forecast columns" in result


class TestTraceFormulaChain:
    """Tests for trace_formula_chain tool."""

    def test_traces_simple_formula(self, mock_sheets_client, sample_spreadsheet_url):
        """Test tracing a simple formula chain."""
        with patch("agents.tools._sheets_client", mock_sheets_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                result = trace_formula_chain.invoke({
                    "sheet_name": "operations",
                    "cell_notation": "K194",
                    "max_depth": 2
                })
                
                assert "Formula chain" in result
                assert "K194" in result

    def test_respects_max_depth(self, mock_sheets_client, sample_spreadsheet_url):
        """Test that max_depth is respected."""
        with patch("agents.tools._sheets_client", mock_sheets_client):
            with patch("agents.tools._current_spreadsheet_url", sample_spreadsheet_url):
                result = trace_formula_chain.invoke({
                    "sheet_name": "operations",
                    "cell_notation": "K194",
                    "max_depth": 1
                })
                
                # Should not go too deep
                assert "Formula chain" in result
