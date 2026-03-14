from __future__ import annotations

import json
import sys


def format_json(data: dict | list[dict]) -> None:
    """Write structured JSON to stdout."""
    print(json.dumps(data, indent=2))


def format_human_list(items: list[dict]) -> None:
    """Write a table of integrations to stdout."""
    if not items:
        print("No integrations found.")
        return

    # Column widths
    key_w = max(len(r.get("integration_key", "")) for r in items)
    name_w = max(len(r.get("name", "")) for r in items)
    type_w = max(len(r.get("type", "")) for r in items)

    key_w = max(key_w, len("KEY"))
    name_w = max(name_w, len("NAME"))
    type_w = max(type_w, len("TYPE"))

    header = f"{'KEY':<{key_w}}  {'NAME':<{name_w}}  {'TYPE':<{type_w}}"
    print(header)
    print("-" * len(header))
    for r in items:
        print(
            f"{r.get('integration_key', ''):<{key_w}}  "
            f"{r.get('name', ''):<{name_w}}  "
            f"{r.get('type', ''):<{type_w}}"
        )


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
