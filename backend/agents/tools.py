"""LangChain tool wrappers for Google Sheets operations.

This module wraps SheetsUtilities methods as LangChain @tool functions
for use by the financial analysis agents.
"""

import re
import json
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool

from shared.sheets_utilities import SheetsUtilities


# Global sheets client - will be initialized when tools are created
_sheets_client: Optional[SheetsUtilities] = None
_current_spreadsheet_url: Optional[str] = None
_service_account_email: Optional[str] = None

# Configurable tab names with sensible defaults
_tab_config = {
    "model_documentation": "Model Documentation",
    "key_drivers_results": "Key Drivers and Results",
    "main_monthly": "operations",  # Main operations tab
    "tasks": "Tasks",
    "audit_log": "AuditLog",
}


def initialize_tools(
    credentials_path: str,
    spreadsheet_url: str,
    tab_names: Optional[dict] = None,
) -> None:
    """Initialize the tools with credentials and spreadsheet URL.

    Args:
        credentials_path: Path to Google service account JSON file.
        spreadsheet_url: URL of the Google Sheet to work with.
        tab_names: Optional dict to override default tab names. Keys:
            - model_documentation: Tab with model docs (default: "Model Documentation")
            - key_drivers_results: Tab with KPIs (default: "Key Drivers and Results")
            - main_monthly: Main operations tab (default: "operations")
            - tasks: Tasks tab (default: "Tasks")
            - audit_log: Audit log tab (default: "AuditLog")
    """
    global _sheets_client, _current_spreadsheet_url, _service_account_email, _tab_config
    _sheets_client = SheetsUtilities(credentials_path)
    _current_spreadsheet_url = spreadsheet_url
    
    # Update tab config if provided
    if tab_names:
        _tab_config.update(tab_names)
    
    # Extract service account email for better error messages
    try:
        with open(credentials_path) as f:
            creds_data = json.load(f)
            _service_account_email = creds_data.get("client_email", "unknown")
    except Exception:
        _service_account_email = "unknown"


def get_tab_name(key: str) -> str:
    """Get the configured tab name for a given key."""
    return _tab_config.get(key, key)


def _resolve_sheet_name(sheet_name: str) -> str:
    """Resolve a sheet name to its actual name in the spreadsheet.
    
    This handles cases where the model documentation mentions tab names
    that differ from the actual spreadsheet tab names.
    
    Args:
        sheet_name: The sheet name to resolve.
        
    Returns:
        The actual sheet name in the spreadsheet.
    """
    # Common aliases - map documentation names to actual tab names
    aliases = {
        "m - monthly": get_tab_name("main_monthly"),
        "m-monthly": get_tab_name("main_monthly"),
        "monthly": get_tab_name("main_monthly"),
        "model documentation": get_tab_name("model_documentation"),
        "key drivers and results": get_tab_name("key_drivers_results"),
        "tasks": get_tab_name("tasks"),
        "auditlog": get_tab_name("audit_log"),
        "audit log": get_tab_name("audit_log"),
    }
    
    resolved = aliases.get(sheet_name.lower().strip(), sheet_name)
    return resolved


def get_sheets_client() -> SheetsUtilities:
    """Get the initialized sheets client."""
    if _sheets_client is None:
        raise RuntimeError("Tools not initialized. Call initialize_tools() first.")
    return _sheets_client


def get_spreadsheet_url() -> str:
    """Get the current spreadsheet URL."""
    if _current_spreadsheet_url is None:
        raise RuntimeError("Tools not initialized. Call initialize_tools() first.")
    return _current_spreadsheet_url


def _format_sheets_error(e: Exception, operation: str) -> str:
    """Format a Google Sheets error with helpful context.
    
    Args:
        e: The exception that was raised.
        operation: Description of the operation that failed.
        
    Returns:
        A helpful error message with troubleshooting steps.
    """
    error_type = type(e).__name__
    error_str = str(e)
    
    # Check for permission errors
    if isinstance(e, PermissionError) or "403" in error_str or "permission" in error_str.lower():
        return (
            f"PERMISSION ERROR: Cannot access spreadsheet for {operation}.\n\n"
            f"The service account does not have access to this spreadsheet.\n"
            f"To fix this:\n"
            f"1. Open the Google Spreadsheet\n"
            f"2. Click 'Share' button (top right)\n"
            f"3. Add this email with Editor access: {_service_account_email}\n"
            f"4. Click 'Send' (uncheck 'Notify people')\n\n"
            f"Original error: {error_type}: {error_str}"
        )
    
    # Check for not found errors
    if "404" in error_str or "not found" in error_str.lower():
        return (
            f"NOT FOUND ERROR: {operation} failed.\n"
            f"The spreadsheet or sheet tab may not exist.\n"
            f"Original error: {error_type}: {error_str}"
        )
    
    # Check for authentication errors
    if "401" in error_str or "auth" in error_str.lower() or "credential" in error_str.lower():
        return (
            f"AUTHENTICATION ERROR: {operation} failed.\n"
            f"The credentials may be invalid or expired.\n"
            f"Check that credentials.json is a valid service account key file.\n"
            f"Original error: {error_type}: {error_str}"
        )
    
    # Default error message
    return f"Error {operation}: {error_type}: {error_str}"


@tool
def read_model_documentation() -> str:
    """Read the Model Documentation tab to understand model structure and conventions.

    This should be called FIRST when starting to work with a new model.
    Returns the full contents of the Model Documentation tab which contains:
    - Modeling conventions
    - Column/row structure explanations
    - Critical formulas
    - Rules for working with the model

    Returns:
        The full text content of the Model Documentation tab.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    tab_name = get_tab_name("model_documentation")

    try:
        data = sheets.read_sheet(url, tab_name)
        # Flatten the 2D array into readable text
        lines = []
        for row in data:
            line = " | ".join(str(cell) for cell in row if cell)
            if line.strip():
                lines.append(line)
        return "\n".join(lines)
    except Exception as e:
        error_type = type(e).__name__
        error_str = str(e).lower()
        # If tab not found, try to provide helpful info from main tab
        if "notfound" in error_type.lower() or "not found" in error_str or "worksheet" in error_str:
            try:
                # Fall back to listing available tabs
                wb = sheets.client.open_by_url(url)
                available = [ws.title for ws in wb.worksheets()]
                return (
                    f"Tab '{tab_name}' not found. Available tabs: {', '.join(available)}.\n\n"
                    f"Consider using read_sheet_tab() with one of these tab names, "
                    f"or update the tab configuration."
                )
            except Exception:
                pass
        return _format_sheets_error(e, f"reading Model Documentation (tab: {tab_name})")


@tool
def read_key_drivers_and_results() -> str:
    """Read the Key Drivers and Results tab to see important metrics.

    This tab shows high-level Key Drivers (inputs) and Key Results (outputs)
    that the user cares about most. Use this to understand which metrics
    are most important for analysis.

    If the dedicated tab doesn't exist, this will extract Key Drivers and 
    Key Results from the main operations tab.

    Returns:
        Formatted content of the Key Drivers and Results tab.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    tab_name = get_tab_name("key_drivers_results")

    try:
        data = sheets.read_sheet(url, tab_name)
        lines = []
        for row in data:
            line = " | ".join(str(cell) for cell in row if cell)
            if line.strip():
                lines.append(line)
        return "\n".join(lines)
    except Exception as e:
        error_type = type(e).__name__
        error_str = str(e).lower()
        # If dedicated tab not found, extract from main operations tab
        if "notfound" in error_type.lower() or "not found" in error_str or "worksheet" in error_str:
            try:
                main_tab = get_tab_name("main_monthly")
                data = sheets.read_sheet(url, main_tab)
                
                # Extract rows that are Key Drivers or Key Results
                drivers = []
                results = []
                for row in data:
                    if len(row) > 0:
                        marker = str(row[0]).strip().lower()
                        if "key driver" in marker:
                            name = row[2] if len(row) > 2 else "Unknown"
                            drivers.append(f"  - {name}")
                        elif "key result" in marker:
                            name = row[2] if len(row) > 2 else "Unknown"
                            results.append(f"  - {name}")
                
                if drivers or results:
                    output = f"Extracted from '{main_tab}' tab:\n\n"
                    if drivers:
                        output += "KEY DRIVERS (inputs you can change):\n" + "\n".join(drivers) + "\n\n"
                    if results:
                        output += "KEY RESULTS (outputs to monitor):\n" + "\n".join(results)
                    return output
                else:
                    return f"Tab '{tab_name}' not found and could not extract Key Drivers/Results from '{main_tab}'."
            except Exception as inner_e:
                return f"Tab '{tab_name}' not found. Fallback also failed: {str(inner_e)}"
        return _format_sheets_error(e, f"reading Key Drivers and Results (tab: {tab_name})")


@tool
def read_sheet_tab(sheet_name: str) -> str:
    """Read all contents from a specific sheet tab.

    Args:
        sheet_name: Name of the tab to read (e.g., "operations", "income_statement").

    Returns:
        Formatted content of the sheet tab.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    resolved_name = _resolve_sheet_name(sheet_name)

    try:
        data = sheets.read_sheet(url, resolved_name)
        lines = []
        for i, row in enumerate(data, 1):
            line = f"Row {i}: " + " | ".join(str(cell) for cell in row if cell)
            if line.strip() != f"Row {i}:":
                lines.append(line)
        return "\n".join(lines)
    except Exception as e:
        extra = f" (resolved from '{sheet_name}')" if resolved_name != sheet_name else ""
        return _format_sheets_error(e, f"reading sheet '{resolved_name}'{extra}")


@tool
def read_cell_value(sheet_name: str, cell_notation: str) -> str:
    """Read the value of a specific cell.

    Args:
        sheet_name: Name of the tab containing the cell (e.g., "operations").
        cell_notation: A1 notation for the cell (e.g., "K92", "BR21").

    Returns:
        The cell's computed value as a string.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    resolved_name = _resolve_sheet_name(sheet_name)

    try:
        value = sheets.read_cell(url, resolved_name, cell_notation)
        return f"Cell {resolved_name}!{cell_notation} = {value}"
    except Exception as e:
        extra = f" (resolved from '{sheet_name}')" if resolved_name != sheet_name else ""
        return _format_sheets_error(e, f"reading cell {resolved_name}!{cell_notation}{extra}")


@tool
def read_cell_formula(sheet_name: str, cell_notation: str) -> str:
    """Read the formula of a specific cell (not its computed value).

    Use this to understand HOW a value is calculated.

    Args:
        sheet_name: Name of the tab containing the cell (e.g., "operations").
        cell_notation: A1 notation for the cell (e.g., "K92", "BR194").

    Returns:
        The cell's formula (e.g., "=K191+K192+K193").
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    resolved_name = _resolve_sheet_name(sheet_name)

    try:
        formula = sheets.read_cell_formula(url, resolved_name, cell_notation)
        formula_str = str(formula) if formula is not None else None
        if formula_str and formula_str.startswith("="):
            return f"Formula at {resolved_name}!{cell_notation}: {formula_str}"
        else:
            return f"Cell {resolved_name}!{cell_notation} contains a static value: {formula_str}"
    except Exception as e:
        extra = f" (resolved from '{sheet_name}')" if resolved_name != sheet_name else ""
        return _format_sheets_error(e, f"reading formula at {resolved_name}!{cell_notation}{extra}")


@tool
def read_range(sheet_name: str, range_notation: str) -> str:
    """Read values from a range of cells.

    Args:
        sheet_name: Name of the tab containing the range (e.g., "operations").
        range_notation: A1 notation for the range (e.g., "K5:BV5", "A1:C10").

    Returns:
        Formatted values from the range.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    resolved_name = _resolve_sheet_name(sheet_name)

    try:
        data = sheets.read_range(url, resolved_name, range_notation)
        lines = []
        for i, row in enumerate(data):
            line = " | ".join(str(cell) for cell in row)
            lines.append(f"Row {i+1}: {line}")
        return f"Range {resolved_name}!{range_notation}:\n" + "\n".join(lines)
    except Exception as e:
        extra = f" (resolved from '{sheet_name}')" if resolved_name != sheet_name else ""
        return _format_sheets_error(e, f"reading range {resolved_name}!{range_notation}{extra}")


@tool
def sum_range(sheet_name: str, range_notation: str) -> str:
    """Read a range of cells and compute sum, average, min, max, and count.

    Use this whenever you need to total values across months, quarters, or years
    instead of doing mental math on individual cell values.

    Args:
        sheet_name: Name of the tab (e.g., "operations").
        range_notation: A1 notation for the range (e.g., "BS29:CD29").

    Returns:
        Aggregation results with exact values.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    resolved_name = _resolve_sheet_name(sheet_name)

    try:
        data = sheets.read_range(url, resolved_name, range_notation)
        numbers = []
        for row in data:
            for cell in row:
                if cell is None:
                    continue
                try:
                    numbers.append(float(cell))
                except (ValueError, TypeError):
                    continue

        if not numbers:
            return f"No numeric values found in {resolved_name}!{range_notation}."

        total = sum(numbers)
        avg = total / len(numbers)
        lo = min(numbers)
        hi = max(numbers)

        return (
            f"Aggregation of {resolved_name}!{range_notation} ({len(numbers)} numeric values):\n"
            f"  Sum:     ${total:,.2f}\n"
            f"  Average: ${avg:,.2f}\n"
            f"  Min:     ${lo:,.2f}\n"
            f"  Max:     ${hi:,.2f}\n"
            f"  Count:   {len(numbers)}"
        )
    except Exception as e:
        extra = f" (resolved from '{sheet_name}')" if resolved_name != sheet_name else ""
        return _format_sheets_error(e, f"summing range {resolved_name}!{range_notation}{extra}")


@tool
def trace_formula_chain(sheet_name: str, cell_notation: str, max_depth: int = 5) -> str:
    """Trace the formula dependencies for a cell to understand its calculation chain.

    This recursively follows formula references to show how a value is computed.

    Args:
        sheet_name: Name of the tab containing the cell (e.g., "operations").
        cell_notation: A1 notation for the cell to trace (e.g., "K195").
        max_depth: Maximum recursion depth (default 5).

    Returns:
        A description of the formula chain showing dependencies.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    resolved_name = _resolve_sheet_name(sheet_name)

    def extract_cell_references(formula: str) -> list[tuple[str, str]]:
        """Extract cell references from a formula.

        Returns list of (sheet_name, cell_ref) tuples.
        """
        refs = []
        # Match sheet references like 'Sheet Name'!A1 or SheetName!A1
        sheet_ref_pattern = r"'?([^'!]+)'?!([A-Z]+[0-9]+)"
        for match in re.finditer(sheet_ref_pattern, formula):
            refs.append((match.group(1), match.group(2)))

        # Match simple cell references like A1, BR21
        simple_ref_pattern = r"(?<![A-Z])([A-Z]+[0-9]+)(?![0-9])"
        for match in re.finditer(simple_ref_pattern, formula):
            # Only add if not already captured with sheet reference
            cell_ref = match.group(1)
            if not any(r[1] == cell_ref for r in refs):
                refs.append((sheet_name, cell_ref))

        return refs

    def trace_recursive(current_sheet: str, cell_ref: str, depth: int, visited: set) -> list[str]:
        """Recursively trace formula dependencies."""
        if depth > max_depth:
            return [f"  {'  ' * depth}... (max depth reached)"]

        # Resolve sheet name for nested references too
        resolved_current = _resolve_sheet_name(current_sheet)
        key = f"{resolved_current}!{cell_ref}"
        if key in visited:
            return [f"  {'  ' * depth}{key} (circular reference)"]
        visited.add(key)

        try:
            raw_formula = sheets.read_cell_formula(url, resolved_current, cell_ref)
            formula = str(raw_formula) if raw_formula is not None else None
            value = sheets.read_cell(url, resolved_current, cell_ref)
        except Exception as e:
            return [f"  {'  ' * depth}{key}: Error - {str(e)}"]

        lines = []
        indent = "  " * depth

        if formula and formula.startswith("="):
            lines.append(f"{indent}{key} = {formula} (value: {value})")
            refs = extract_cell_references(formula)
            for ref_sheet, ref_cell in refs:
                lines.extend(trace_recursive(ref_sheet, ref_cell, depth + 1, visited))
        else:
            lines.append(f"{indent}{key} = {value} (static value)")

        return lines

    try:
        visited: set[str] = set()
        chain_lines = trace_recursive(resolved_name, cell_notation, 0, visited)
        return f"Formula chain for {resolved_name}!{cell_notation}:\n" + "\n".join(chain_lines)
    except Exception as e:
        extra = f" (resolved from '{sheet_name}')" if resolved_name != sheet_name else ""
        return _format_sheets_error(e, f"tracing formula chain for {resolved_name}!{cell_notation}{extra}")


@tool
def write_cell_value(sheet_name: str, cell_notation: str, value: str) -> str:
    """Write a value to a specific cell.

    CAUTION: Only write to Forecast columns, never to Actual columns.

    Args:
        sheet_name: Name of the tab containing the cell (e.g., "operations").
        cell_notation: A1 notation for the cell (e.g., "BT5").
        value: The value to write.

    Returns:
        Confirmation message.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    resolved_name = _resolve_sheet_name(sheet_name)

    try:
        sheets.write_range(url, resolved_name, cell_notation, [[value]])
        return f"Successfully wrote '{value}' to {resolved_name}!{cell_notation}"
    except Exception as e:
        extra = f" (resolved from '{sheet_name}')" if resolved_name != sheet_name else ""
        return _format_sheets_error(e, f"writing to {resolved_name}!{cell_notation}{extra}")


@tool
def write_range_values(sheet_name: str, start_cell: str, values: str) -> str:
    """Write multiple values to a range starting at a cell.

    CAUTION: Only write to Forecast columns, never to Actual columns.

    Args:
        sheet_name: Name of the tab containing the range (e.g., "operations").
        start_cell: A1 notation for the starting cell (e.g., "BT5").
        values: JSON string of values as 2D array (e.g., '[[1, 2, 3]]' for a row).

    Returns:
        Confirmation message.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    resolved_name = _resolve_sheet_name(sheet_name)

    try:
        parsed_values = json.loads(values)
        sheets.write_range(url, resolved_name, start_cell, parsed_values)
        return f"Successfully wrote values to {resolved_name}!{start_cell}"
    except json.JSONDecodeError as e:
        return f"Error parsing values JSON: {str(e)}"
    except Exception as e:
        extra = f" (resolved from '{sheet_name}')" if resolved_name != sheet_name else ""
        return _format_sheets_error(e, f"writing to {resolved_name}!{start_cell}{extra}")


@tool
def write_to_audit_log(
    action_description: str,
    status: str,
    data: str,
    requested_by: str = "Financial Agent",
) -> str:
    """Write an entry to the AuditLog tab.

    Per the model rules, EVERY action must be logged to AuditLog.

    Args:
        action_description: Description of the action taken.
        status: Status of action ("success", "failure", "pending").
        data: JSON string containing data generated by this action.
        requested_by: Who requested the action (default: "Financial Agent").

    Returns:
        Confirmation message.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()

    audit_tab = get_tab_name("audit_log")
    try:
        existing_data = sheets.read_sheet(url, audit_tab)
        next_row = len(existing_data) + 1

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_row = [[timestamp, requested_by, status, action_description, data]]
        sheets.write_range(url, audit_tab, f"A{next_row}", new_row)

        return f"Successfully logged action to {audit_tab} row {next_row}"
    except Exception as e:
        err_msg = str(e)
        if "WorksheetNotFound" in err_msg or "not found" in err_msg.lower():
            return f"AuditLog tab '{audit_tab}' not found in spreadsheet; skipping audit entry."
        return _format_sheets_error(e, f"writing to {audit_tab}")


@tool
def read_tasks() -> str:
    """Read pending tasks from the Tasks tab.

    Per the model rules, when asked to "Complete the Next Dysprosium Task",
    read from this tab to get the task details.

    Returns:
        Formatted list of tasks with their details.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()

    try:
        data = sheets.read_sheet(url, "Tasks")
        lines = []
        for i, row in enumerate(data):
            if i == 0:
                lines.append("TASKS:")
                lines.append("-" * 50)
            else:
                line = f"Task {i}: " + " | ".join(str(cell) for cell in row if cell)
                lines.append(line)
        return "\n".join(lines)
    except Exception as e:
        return _format_sheets_error(e, "reading Tasks")


@tool
def mark_task_complete(task_row: int) -> str:
    """Mark a task as complete in the Tasks tab.

    Args:
        task_row: The row number of the task to mark complete.

    Returns:
        Confirmation message.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()

    try:
        # Update status column (assumed to be column C based on requirements)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheets.write_range(url, "Tasks", f"C{task_row}", [["success"]])
        sheets.write_range(url, "Tasks", f"A{task_row}", [[timestamp]])
        return f"Successfully marked task at row {task_row} as complete"
    except Exception as e:
        return _format_sheets_error(e, f"marking task at row {task_row} complete")


@tool
def find_forecast_columns() -> str:
    """Find which columns are marked as 'Forecast' periods.

    Reads row 2 (or row 3) to identify which columns contain 'Forecast' vs 'Actual'.
    Only Forecast columns should be modified.

    Returns:
        List of column letters that are Forecast periods.
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    main_tab = get_tab_name("main_monthly")

    try:
        # Try row 2 first (common in some models), then row 3
        for row_num in [2, 3]:
            try:
                data = sheets.read_range(url, main_tab, f"A{row_num}:EZ{row_num}")
                if data and data[0]:
                    forecast_cols = []
                    for i, cell in enumerate(data[0]):
                        if str(cell).lower().strip() == "forecast":
                            col_letter = _index_to_column(i)
                            forecast_cols.append(col_letter)
                    
                    if forecast_cols:
                        return f"Forecast columns (from row {row_num}): {', '.join(forecast_cols)}"
            except Exception:
                continue
        
        return f"No Forecast columns found in '{main_tab}' tab (checked rows 2 and 3)"
    except Exception as e:
        return _format_sheets_error(e, f"finding forecast columns in '{main_tab}'")


def _get_month_map():
    import calendar
    m = {name.lower(): num for num, name in enumerate(calendar.month_abbr) if num}
    m.update({name.lower(): num for num, name in enumerate(calendar.month_name) if num})
    return m


def _parse_mon_yy(text: str, month_map: dict) -> tuple:
    """Parse 'Mon-YY', 'Mon-YYYY', 'Month YYYY' into (month, year) or (None, None)."""
    match = re.match(r"^([A-Za-z]+)[- /](\d{2,4})$", text.strip())
    if match:
        m = month_map.get(match.group(1).lower())
        y = int(match.group(2))
        if y < 100:
            y += 2000
        return (m, y) if m else (None, None)
    return (None, None)


def _parse_cell_date(val_str: str, month_map: dict) -> tuple:
    """Parse a cell value into (month, year), trying Mon-YY first then dateutil."""
    from dateutil import parser as dateparser
    m, y = _parse_mon_yy(val_str, month_map)
    if m is not None:
        return (m, y)
    try:
        parsed = dateparser.parse(val_str)
        if parsed:
            return (parsed.month, parsed.year)
    except (ValueError, TypeError):
        pass
    return (None, None)


def _load_date_spine() -> tuple:
    """Load the date spine from row 2 and return (main_tab, row_data) or raise."""
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    main_tab = get_tab_name("main_monthly")
    data = sheets.read_range(url, main_tab, "K2:EZ2")
    if not data or not data[0]:
        return (main_tab, [])
    return (main_tab, data[0])


@tool
def find_date_column(date_query: str) -> str:
    """Find which column corresponds to a given date or month.

    The date spine is in row 2 of the operations tab, starting at column K.
    Use this BEFORE reading a metric value for a specific month.

    Args:
        date_query: A date reference like "Apr-25", "April 2025", "Apr 2025",
                    "Q2 2025", "2025-04-30", etc.

    Returns:
        The column letter and cell value, e.g., "Column BX (operations!BX2 = Apr-25)"
    """
    from dateutil import parser as dateparser

    month_map = _get_month_map()

    try:
        main_tab, row = _load_date_spine()
        if not row:
            return "No date spine found in row 2."

        target_month, target_year = _parse_mon_yy(date_query, month_map)

        if target_month is None:
            try:
                parsed = dateparser.parse(date_query, dayfirst=False)
                if parsed:
                    target_month = parsed.month
                    target_year = parsed.year
            except (ValueError, TypeError):
                pass

        if target_month is None:
            return f"Could not parse '{date_query}' as a date. Try formats like 'Apr-25', 'April 2025', '2025-04-30'."

        for i, cell_val in enumerate(row):
            if cell_val is None or str(cell_val).strip() == "":
                continue
            cell_month, cell_year = _parse_cell_date(str(cell_val), month_map)
            if cell_month == target_month and cell_year == target_year:
                col_letter = _index_to_column(i + 10)
                return f"Column {col_letter} (cell {main_tab}!{col_letter}2 = {cell_val})"

        return f"No column found matching '{date_query}' in the date spine (row 2). Available dates start at {row[0]} and end at {row[-1] if row else 'unknown'}."
    except Exception as e:
        return _format_sheets_error(e, f"finding date column for '{date_query}'")


@tool
def find_date_range(period: str) -> str:
    """Find the start and end columns for a date range (year, quarter, or custom).

    Use this when the user asks about a full year, quarter, or multi-month span.
    Returns start/end column letters so you can build a range like "BS29:CD29"
    for use with read_range, then sum the values.

    Args:
        period: A period like "2025", "Q2 2025", "Q1 2024", "H1 2025",
                "Jan-25 to Jun-25", "2024", etc.

    Returns:
        Start and end columns with instructions, e.g.,
        "Range: BS to CD (Jan-25 through Dec-25, 12 months).
         To read a metric across this range, use read_range with e.g. 'BS29:CD29'
         then sum the numeric values."
    """
    month_map = _get_month_map()

    try:
        main_tab, row = _load_date_spine()
        if not row:
            return "No date spine found in row 2."

        parsed_spine = []
        for i, cell_val in enumerate(row):
            if cell_val is None or str(cell_val).strip() == "":
                parsed_spine.append((i, None, None, str(cell_val) if cell_val else ""))
                continue
            m, y = _parse_cell_date(str(cell_val), month_map)
            parsed_spine.append((i, m, y, str(cell_val)))

        period_stripped = period.strip()

        start_month, start_year, end_month, end_year = None, None, None, None

        # "2025" — full year
        year_match = re.match(r"^(\d{4})$", period_stripped)
        if year_match:
            yr = int(year_match.group(1))
            start_month, start_year = 1, yr
            end_month, end_year = 12, yr

        # "Q1 2025", "Q2 2024", etc.
        if start_month is None:
            q_match = re.match(r"^[Qq]([1-4])\s*(\d{4})$", period_stripped)
            if q_match:
                q = int(q_match.group(1))
                yr = int(q_match.group(2))
                start_month = (q - 1) * 3 + 1
                end_month = q * 3
                start_year = end_year = yr

        # "H1 2025", "H2 2025"
        if start_month is None:
            h_match = re.match(r"^[Hh]([12])\s*(\d{4})$", period_stripped)
            if h_match:
                h = int(h_match.group(1))
                yr = int(h_match.group(2))
                start_month = 1 if h == 1 else 7
                end_month = 6 if h == 1 else 12
                start_year = end_year = yr

        # "Jan-25 to Jun-25", "Apr 2024 to Sep 2024"
        if start_month is None:
            range_match = re.match(
                r"^([A-Za-z0-9 -]+?)\s+to\s+([A-Za-z0-9 -]+)$",
                period_stripped, re.IGNORECASE,
            )
            if range_match:
                sm, sy = _parse_mon_yy(range_match.group(1), month_map)
                em, ey = _parse_mon_yy(range_match.group(2), month_map)
                if sm and em:
                    start_month, start_year = sm, sy
                    end_month, end_year = em, ey

        if start_month is None:
            return (
                f"Could not parse '{period}' as a date range. "
                "Try formats like '2025', 'Q2 2025', 'H1 2025', or 'Jan-25 to Jun-25'."
            )

        first_col = None
        last_col = None
        first_label = ""
        last_label = ""
        count = 0

        for idx, m, y, label in parsed_spine:
            if m is None or y is None:
                continue
            in_range = (
                (y > start_year or (y == start_year and m >= start_month))
                and (y < end_year or (y == end_year and m <= end_month))
            )
            if in_range:
                col = _index_to_column(idx + 10)
                if first_col is None:
                    first_col = col
                    first_label = label
                last_col = col
                last_label = label
                count += 1

        if first_col is None:
            return f"No columns found in the date spine matching '{period}'."

        return (
            f"Range: {first_col} to {last_col} ({first_label} through {last_label}, {count} months).\n"
            f"To read a metric across this range, use read_range with e.g. '{first_col}<ROW>:{last_col}<ROW>' "
            f"(replace <ROW> with the metric's row number), then sum the numeric values."
        )
    except Exception as e:
        return _format_sheets_error(e, f"finding date range for '{period}'")


@tool
def find_metric_row(metric_name: str, sheet_name: str = "operations") -> str:
    """Find which row contains a given metric by searching column C.

    Use this to dynamically locate metrics instead of relying on hardcoded row numbers.

    Args:
        metric_name: The metric to find (e.g., "Orders", "EBITDA", "Gross Sales").
        sheet_name: Tab to search in (default: "operations").

    Returns:
        Row number and cell reference, e.g., "Row 15 (operations!C15 = Orders)"
    """
    sheets = get_sheets_client()
    url = get_spreadsheet_url()
    resolved_name = _resolve_sheet_name(sheet_name)

    try:
        data = sheets.read_range(url, resolved_name, "C1:C300")
        if not data:
            return f"No data found in column C of '{resolved_name}'."

        query_lower = metric_name.strip().lower()
        exact_match = None
        partial_matches = []

        for i, row_data in enumerate(data):
            cell_val = row_data[0] if row_data else None
            if cell_val is None:
                continue
            cell_str = str(cell_val).strip()
            if cell_str.lower() == query_lower:
                exact_match = (i + 1, cell_str)
                break
            if query_lower in cell_str.lower():
                partial_matches.append((i + 1, cell_str))

        if exact_match:
            row_num, label = exact_match
            return f"Row {row_num} ({resolved_name}!C{row_num} = {label})"

        if partial_matches:
            results = [f"  Row {r}: {label}" for r, label in partial_matches[:5]]
            return f"No exact match for '{metric_name}'. Partial matches in '{resolved_name}':\n" + "\n".join(results)

        return f"Metric '{metric_name}' not found in column C of '{resolved_name}'."
    except Exception as e:
        return _format_sheets_error(e, f"finding metric row for '{metric_name}' in '{resolved_name}'")


def _index_to_column(index: int) -> str:
    """Convert 0-based index to Excel column letter."""
    result = ""
    index += 1  # Convert to 1-based
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result


# Export the list of all tools for binding to agents
ALL_TOOLS = [
    read_model_documentation,
    read_key_drivers_and_results,
    read_sheet_tab,
    read_cell_value,
    read_cell_formula,
    read_range,
    sum_range,
    trace_formula_chain,
    write_cell_value,
    write_range_values,
    write_to_audit_log,
    read_tasks,
    mark_task_complete,
    find_forecast_columns,
    find_date_column,
    find_date_range,
    find_metric_row,
]

READ_ONLY_TOOLS = [
    read_model_documentation,
    read_key_drivers_and_results,
    read_sheet_tab,
    read_cell_value,
    read_cell_formula,
    read_range,
    sum_range,
    trace_formula_chain,
    find_forecast_columns,
    find_date_column,
    find_date_range,
    find_metric_row,
]

GOAL_SEEK_TOOLS = [
    read_model_documentation,
    read_key_drivers_and_results,
    read_sheet_tab,
    read_cell_value,
    read_cell_formula,
    read_range,
    sum_range,
    trace_formula_chain,
    write_cell_value,
    write_range_values,
    write_to_audit_log,
    find_forecast_columns,
    find_date_column,
    find_date_range,
    find_metric_row,
]
