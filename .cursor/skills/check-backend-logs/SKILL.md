---
name: check-backend-logs
description: Scan backend terminal output for Python tracebacks and errors, then locate the offending source code and suggest fixes. Use when user says "check backend logs", "check logs", "backend error", "agent error", "check for errors", or mentions seeing a traceback.
---

# Check Backend Logs

Scan the project's running backend terminals for Python errors and propose fixes.

## Workflow

### Step 1: Find terminal files

Terminal files live in the terminals folder (path provided in system context as `Terminals folder`). List all `.txt` files:

```bash
ls "$TERMINALS_FOLDER"/*.txt
```

### Step 2: Scan for errors

Read each terminal file and search for these patterns (most recent occurrence first):
- `Traceback (most recent call last):`
- `Error:` (SyntaxError, IndentationError, ImportError, etc.)
- `Exception:`
- `FAILED` or `CRITICAL`

Use ripgrep for speed:

```bash
rg -l "Traceback|Error:|Exception:" "$TERMINALS_FOLDER"/*.txt
```

Then read the matching files, focusing on the **last** traceback in each file (the most recent error).

### Step 3: Parse the traceback

Extract from the traceback:
1. **Error type** — the last line (e.g., `IndentationError: unexpected indent`)
2. **File path** — from `File "/path/to/file.py", line N`
3. **Line number** — from the same line
4. **Code snippet** — the line shown in the traceback

### Step 4: Read the source

Read the offending file around the reported line number (±15 lines of context) to understand the issue.

### Step 5: Diagnose and fix

Common patterns:

| Error | Typical cause | Fix approach |
|-------|--------------|--------------|
| `IndentationError` | Duplicate/leftover lines, mixed tabs/spaces | Remove duplicates, normalize indentation |
| `SyntaxError` | Missing colon, unmatched brackets, bad string | Fix syntax at reported line |
| `ImportError` / `ModuleNotFoundError` | Missing dependency or wrong import path | Install package or fix import |
| `AttributeError` | Wrong method/property name | Check API docs, fix name |
| `TypeError` | Wrong argument count or type | Match function signature |
| `KeyError` | Missing dict key | Add key check or fix key name |

### Step 6: Report to user

Summarize findings in this format:

```
**Error found** in terminal [terminal_id]:
- **Type**: [ErrorType]: [message]
- **File**: `[filepath]` line [N]
- **Cause**: [brief diagnosis]
- **Fix**: [what you changed or recommend]
```

If multiple errors are found, report each one. If no errors are found, say so.

## Important notes

- Always check **all** terminal files, not just the first one.
- Focus on the **most recent** traceback in each file (scroll to bottom).
- If the error is in a third-party library (site-packages), look for the last project file in the call stack instead.
- After fixing, suggest the user restart the backend if needed.
