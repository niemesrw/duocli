from __future__ import annotations

import re
import sys
import time

import click
from dotenv import load_dotenv

from duocli import __version__
from duocli.backends import get_backend
from duocli.output import (
    format_error,
    format_human_list,
    format_human_single,
    format_json,
    warn_secret_key,
)


@click.group()
@click.option("--human", is_flag=True, help="Human-readable output instead of JSON.")
@click.version_option(version=__version__, prog_name="duocli")
@click.pass_context
def cli(ctx: click.Context, human: bool) -> None:
    """Manage Duo Security integrations from the command line."""
    load_dotenv()
    ctx.ensure_object(dict)
    ctx.obj["human"] = human


@cli.command("create-app")
@click.option("--name", required=True, help="Name for the new integration.")
@click.option(
    "--type",
    "integration_type",
    required=True,
    help="Integration type (e.g. websdk, adminapi). Passed through to Duo API.",
)
@click.pass_context
def create_app(ctx: click.Context, name: str, integration_type: str) -> None:
    """Create a new Duo integration."""
    backend = get_backend()
    result = backend.create_integration(name=name, integration_type=integration_type)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)

    warn_secret_key()


@cli.command("delete-app")
@click.option("--ikey", required=True, help="Integration key of the app to delete.")
@click.pass_context
def delete_app(ctx: click.Context, ikey: str) -> None:
    """Delete a Duo integration."""
    backend = get_backend()
    result = backend.delete_integration(integration_key=ikey)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)


@cli.command("list-apps")
@click.pass_context
def list_apps(ctx: click.Context) -> None:
    """List all Duo integrations."""
    backend = get_backend()
    results = backend.list_integrations()

    # Check if the result is an error (single-element list with error status)
    if len(results) == 1 and results[0].get("status") == "error":
        format_error(results[0])
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_list(results)
    else:
        format_json(results)


@cli.command("auth-logs")
@click.option(
    "--since",
    default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.pass_context
def auth_logs(ctx: click.Context, since: str) -> None:
    """Show authentication log events."""
    backend = get_backend()
    now_ms = int(time.time() * 1000)
    delta_ms = _parse_since(since) * 1000
    mintime = now_ms - delta_ms
    results = backend.get_authentication_logs(mintime=mintime, maxtime=now_ms)

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_list(
            results,
            columns=["timestamp", "user", "result", "factor", "application", "ip"],
        )
    else:
        format_json(results)


@cli.command("admin-logs")
@click.option(
    "--since",
    default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.pass_context
def admin_logs(ctx: click.Context, since: str) -> None:
    """Show administrator action log events."""
    backend = get_backend()
    now_sec = int(time.time())
    delta_sec = _parse_since(since)
    mintime = now_sec - delta_sec
    results = backend.get_administrator_logs(mintime=mintime)

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_list(
            results,
            columns=["timestamp", "admin", "action", "object"],
        )
    else:
        format_json(results)


def _parse_since(value: str) -> int:
    """Parse a human-friendly duration string into seconds.

    Examples: '1h' -> 3600, '7d' -> 604800, '30m' -> 1800
    """
    match = re.fullmatch(r"(\d+)\s*([mhd])", value.strip().lower())
    if not match:
        raise click.BadParameter(
            f"Invalid duration '{value}'. Use format like 30m, 6h, or 7d."
        )
    amount = int(match.group(1))
    unit = match.group(2)
    multipliers = {"m": 60, "h": 3600, "d": 86400}
    return amount * multipliers[unit]


def _is_error_list(results: list[dict]) -> bool:
    return len(results) == 1 and results[0].get("status") == "error"
