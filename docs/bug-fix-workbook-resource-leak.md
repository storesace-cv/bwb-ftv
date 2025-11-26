# Bug Fix: Workbook Resource Leak in Excel Import Functions

## Summary

Fixed a critical resource leak in `services/products.py` where Excel workbooks were not being properly closed when exceptions occurred during import operations. This could lead to file handle exhaustion and locked files, particularly impacting Windows systems.

## Bug Description

### Location
- File: `services/products.py`
- Functions: `_upsert()` and `_load_prices()` (nested functions within `update_from_excel()`)

### Issue
The functions opened Excel workbooks using `openpyxl.load_workbook()` but only called `wb.close()` at the end of the function or before specific early returns. If an exception occurred during processing (e.g., database errors, data validation failures), the workbook would never be closed, leading to:

1. **File handle leaks**: Accumulation of open file handles over time
2. **Locked files**: On Windows, files remain locked and cannot be deleted or modified
3. **Resource exhaustion**: In long-running processes or systems with frequent imports, this could exhaust available file handles

### Code Pattern (Before Fix)

```python
def _upsert(file_path: Path, table: str) -> None:
    wb = load_workbook(file_path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    try:
        headers = list(next(rows))
    except StopIteration:
        wb.close()  # Closed here
        return
    # ... processing logic ...
    if not cols:
        wb.close()  # Closed here
        return
    # ... more processing ...
    # If exception occurs here, wb.close() is never called!
    wb.close()  # Only reached if no exceptions
```

## Solution

Wrapped all workbook operations in `try-finally` blocks to ensure `wb.close()` is always called, regardless of how the function exits (normal return, early return, or exception).

### Code Pattern (After Fix)

```python
def _upsert(file_path: Path, table: str) -> None:
    wb = load_workbook(file_path, read_only=True, data_only=True)
    try:
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        try:
            headers = list(next(rows))
        except StopIteration:
            return  # No manual close needed
        # ... processing logic ...
        if not cols:
            return  # No manual close needed
        # ... more processing ...
        # Even if exception occurs, finally block ensures cleanup
    finally:
        wb.close()  # Always called
```

## Changes Made

1. **services/products.py**:
   - Wrapped `_upsert()` function body in try-finally block
   - Wrapped `_load_prices()` function body in try-finally block
   - Removed manual `wb.close()` calls before early returns and exceptions
   - Moved `wb.close()` to finally blocks

2. **tests/test_workbook_resource_leak.py** (new file):
   - Added test verifying workbooks close on exceptions
   - Added test verifying workbooks close on early returns
   - Added test demonstrating the problem without try-finally

## Impact

### Positive Effects
- **Prevents resource leaks**: Workbooks are always closed, even on errors
- **Improves reliability**: Import operations are more robust under error conditions
- **Better Windows compatibility**: Files are no longer left locked after failures
- **Cleaner code**: Explicit resource management using try-finally pattern

### Risk Assessment
- **Low risk**: The change only affects resource cleanup, not business logic
- **Backward compatible**: No changes to function signatures or behavior
- **Well-tested**: All existing tests pass, plus new tests added

## Testing

### New Tests
- `test_workbook_closes_on_exception_in_try_finally`: Verifies proper cleanup on exceptions
- `test_workbook_closes_on_early_return_in_try_finally`: Verifies proper cleanup on early returns
- `test_workbook_resource_leak_without_finally`: Demonstrates the original problem

### Existing Tests
All 29 tests in `test_import_update.py` continue to pass, confirming no regression in import functionality.

## Recommendations

### Code Review Checklist
When reviewing similar code, check for:
1. File handles opened without try-finally or context managers
2. Database connections not properly closed
3. Network sockets left open
4. Any resource that needs explicit cleanup

### Best Practices
Consider using context managers (`with` statement) for resource management:

```python
# Even better approach (if openpyxl supported it fully):
with load_workbook(file_path, read_only=True, data_only=True) as wb:
    # Processing logic
    pass
# Automatic cleanup
```

Note: While openpyxl workbooks can be used with `with` statements, the `read_only=True` mode has some limitations, so try-finally is the safer approach here.

## Related Issues

This fix addresses a class of bugs related to resource management. Similar patterns should be reviewed in:
- Database connection handling
- File I/O operations
- Network operations
- Any code using external resources

## References

- Python documentation on try-finally: https://docs.python.org/3/tutorial/errors.html#defining-clean-up-actions
- openpyxl documentation: https://openpyxl.readthedocs.io/
- Resource management best practices: https://docs.python.org/3/library/contextlib.html
