from __future__ import annotations

import json
import sys


def format_json(data: dict | list[dict]) -> None:
    """Write structured JSON to stdout."""
    print(json.dumps(data, indent=2))


_MAX_COL_WIDTH = 60


def format_human_list(
    items: list[dict],
    columns: list[str] | None = None,
    max_col_width: int = _MAX_COL_WIDTH,
) -> None:
    """Write a table to stdout. Columns default to the keys of the first item."""
    if not items:
        print("No results found.")
        return

    if columns is None:
        columns = list(items[0].keys())

    # Compute column widths (capped)
    widths = {}
    for col in columns:
        header_label = col.upper().replace("_", " ")
        data_width = max(len(_truncate(str(r.get(col, "")), max_col_width)) for r in items)
        widths[col] = max(min(data_width, max_col_width), len(header_label))

    # Header
    header_parts = [f"{col.upper().replace('_', ' '):<{widths[col]}}" for col in columns]
    header = "  ".join(header_parts)
    print(header)
    print("-" * len(header))

    # Rows
    for r in items:
        row_parts = [
            f"{_truncate(str(r.get(col, '')), widths[col]):<{widths[col]}}"
            for col in columns
        ]
        print("  ".join(row_parts))


def _truncate(value: str, max_width: int) -> str:
    if len(value) <= max_width:
        return value
    return value[: max_width - 3] + "..."


def format_human_single(data: dict) -> None:
    """Write a single result as key-value pairs to stdout."""
    for key, value in data.items():
        if key == "status":
            continue
        print(f"{key}: {value}")


def format_error(data: dict) -> None:
    """Write structured error JSON to stdout and a diagnostic to stderr."""
    print(json.dumps(data, indent=2))
    message = data.get("message", "unknown error")
    print(f"Error: {message}", file=sys.stderr)


def warn_secret_key() -> None:
    """Print a stderr warning about secret key sensitivity."""
    print(
        "WARNING: secret_key is sensitive — store securely",
        file=sys.stderr,
    )
