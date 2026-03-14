from __future__ import annotations

import sys

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
