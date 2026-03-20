from __future__ import annotations

import json
import re
import sys
import time

import os

import click
from dotenv import load_dotenv

from duocli import __version__
from duocli.backends import get_backend
from duocli.oauth import OAuthClient
from duocli.output import (
    format_error,
    format_human_list,
    format_human_single,
    format_json,
    warn_secret_key,
)
from duocli.validate import validate_integration_key, validate_name, validate_type


_VALID_UPDATE_KEYS = frozenset({
    "name", "visual_style", "greeting", "notes", "enroll_policy",
    "username_normalization_policy", "adminapi_admins", "adminapi_info",
    "adminapi_integrations", "adminapi_read_log", "adminapi_read_resource",
    "adminapi_settings", "adminapi_write_resource", "reset_secret_key",
    "trusted_device_days", "ip_whitelist", "ip_whitelist_enroll_policy",
    "groups_allowed", "self_service_allowed", "sso", "user_access",
})


@click.group()
@click.option("--human", is_flag=True, help="Human-readable output instead of JSON.")
@click.version_option(version=__version__, prog_name="duocli")
@click.pass_context
def cli(ctx: click.Context, human: bool) -> None:
    """Manage Duo Security integrations from the command line."""
    load_dotenv()
    ctx.ensure_object(dict)
    ctx.obj["human"] = human


class _MutuallyExclusiveOption(click.Option):
    """Click option that is mutually exclusive with another option."""

    def __init__(self, *args, mutually_exclusive: list[str] | None = None, **kwargs):
        self._mutually_exclusive = mutually_exclusive or []
        super().__init__(*args, **kwargs)

    def handle_parse_result(self, ctx, opts, args):
        current = self.name in opts and opts[self.name] is not None
        for other in self._mutually_exclusive:
            if other in opts and opts[other] is not None and current:
                raise click.UsageError(
                    f"--{self.name.replace('_', '-')} is mutually exclusive with "
                    f"--{other.replace('_', '-')}"
                )
        return super().handle_parse_result(ctx, opts, args)


@cli.command("create-app")
@click.option("--name", default=None, help="Name for the new integration.")
@click.option(
    "--type",
    "integration_type",
    default=None,
    help="Integration type (e.g. websdk, adminapi). Passed through to Duo API.",
)
@click.option(
    "--json",
    "json_payload",
    default=None,
    cls=_MutuallyExclusiveOption,
    mutually_exclusive=["name", "integration_type"],
    help="JSON payload with all params (mutually exclusive with --name/--type).",
)
@click.option("--dry-run", is_flag=True, help="Validate inputs and show what would happen without calling API.")
@click.pass_context
def create_app(
    ctx: click.Context,
    name: str | None,
    integration_type: str | None,
    json_payload: str | None,
    dry_run: bool,
) -> None:
    """Create a new Duo integration."""
    if json_payload is not None:
        try:
            params = json.loads(json_payload)
        except json.JSONDecodeError as exc:
            format_error({"status": "error", "message": f"Invalid JSON: {exc}", "code": 10000})
            sys.exit(1)
        if not isinstance(params, dict):
            format_error({"status": "error", "message": "JSON payload must be an object", "code": 10000})
            sys.exit(1)
        name = params.pop("name", None)
        integration_type = params.pop("type", None)
        extra_kwargs = params
    else:
        extra_kwargs = {}

    if not name or not integration_type:
        format_error({
            "status": "error",
            "message": "Both --name and --type are required (or provide them via --json)",
            "code": 10000,
        })
        sys.exit(1)

    validate_name(name)
    validate_type(integration_type)

    if dry_run:
        payload = {"dry_run": True, "action": "create_integration", "params": {"name": name, "type": integration_type}}
        if extra_kwargs:
            payload["params"].update(extra_kwargs)
        format_json(payload)
        return

    backend = get_backend()
    result = backend.create_integration(name=name, integration_type=integration_type, **extra_kwargs)

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
@click.option("--dry-run", is_flag=True, help="Validate inputs and show what would happen without calling API.")
@click.pass_context
def delete_app(ctx: click.Context, ikey: str, dry_run: bool) -> None:
    """Delete a Duo integration."""
    validate_integration_key(ikey)

    if dry_run:
        format_json({"dry_run": True, "action": "delete_integration", "params": {"integration_key": ikey}})
        return

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
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def list_apps(ctx: click.Context, fields: str | None) -> None:
    """List all Duo integrations."""
    backend = get_backend()
    results = backend.list_integrations()

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    _output_list(ctx, results, fields)


@cli.command("get-app")
@click.option("--ikey", required=True, help="Integration key of the app to retrieve.")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.option("--dry-run", is_flag=True, help="Validate inputs and show what would happen without calling API.")
@click.pass_context
def get_app(ctx: click.Context, ikey: str, fields: str | None, dry_run: bool) -> None:
    """Get details of a single Duo integration."""
    validate_integration_key(ikey)

    if dry_run:
        format_json({"dry_run": True, "action": "get_integration", "params": {"integration_key": ikey}})
        return

    backend = get_backend()
    result = backend.get_integration(integration_key=ikey)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if fields:
        field_list = [f.strip() for f in fields.split(",")]
        result = _filter_fields_single(result, field_list)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)


@cli.command("info-summary")
@click.pass_context
def info_summary(ctx: click.Context) -> None:
    """Show summary counts of objects in the Duo account."""
    backend = get_backend()
    result = backend.get_info_summary()

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)


@cli.command("auth-logs")
@click.option(
    "--since",
    default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def auth_logs(ctx: click.Context, since: str, fields: str | None) -> None:
    """Show authentication log events."""
    backend = get_backend()
    now_ms = int(time.time() * 1000)
    delta_ms = _parse_since(since) * 1000
    mintime = now_ms - delta_ms
    results = backend.get_authentication_logs(mintime=mintime, maxtime=now_ms)

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    _output_list(ctx, results, fields,
                 default_columns=["timestamp", "user", "result", "factor", "application", "ip"])


@cli.command("admin-logs")
@click.option(
    "--since",
    default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def admin_logs(ctx: click.Context, since: str, fields: str | None) -> None:
    """Show administrator action log events."""
    backend = get_backend()
    now_sec = int(time.time())
    delta_sec = _parse_since(since)
    mintime = now_sec - delta_sec
    results = backend.get_administrator_logs(mintime=mintime)

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    _output_list(ctx, results, fields,
                 default_columns=["timestamp", "admin", "action", "object"])


@cli.command("auth-stats")
@click.option(
    "--since",
    default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.pass_context
def auth_stats(ctx: click.Context, since: str) -> None:
    """Show aggregate authentication attempt counts."""
    backend = get_backend()
    now_sec = int(time.time())
    delta_sec = _parse_since(since)
    mintime = now_sec - delta_sec
    result = backend.get_auth_stats(mintime=mintime, maxtime=now_sec)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)


@cli.command("list-policies")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def list_policies(ctx: click.Context, fields: str | None) -> None:
    """List all Duo policies."""
    backend = get_backend()
    results = backend.list_policies()

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    _output_list(ctx, results, fields)


@cli.command("get-policy")
@click.option("--id", "policy_id", required=True, help="Policy key to retrieve.")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def get_policy(ctx: click.Context, policy_id: str, fields: str | None) -> None:
    """Get details of a single Duo policy."""
    backend = get_backend()
    result = backend.get_policy(policy_key=policy_id)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if fields:
        field_list = [f.strip() for f in fields.split(",")]
        result = _filter_fields_single(result, field_list)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)


@cli.command("update-app")
@click.option("--ikey", required=True, help="Integration key of the app to update.")
@click.option("--json", "json_payload", required=True, help="JSON payload with update params.")
@click.option("--dry-run", is_flag=True, help="Validate inputs and show what would happen without calling API.")
@click.pass_context
def update_app(ctx: click.Context, ikey: str, json_payload: str, dry_run: bool) -> None:
    """Update a Duo integration."""
    validate_integration_key(ikey)

    try:
        params = json.loads(json_payload)
    except json.JSONDecodeError as exc:
        format_error({"status": "error", "message": f"Invalid JSON: {exc}", "code": 10000})
        sys.exit(1)
    if not isinstance(params, dict) or not params:
        format_error({"status": "error", "message": "JSON payload must be a non-empty object", "code": 10000})
        sys.exit(1)

    unknown_keys = set(params.keys()) - _VALID_UPDATE_KEYS
    if unknown_keys:
        format_error({
            "status": "error",
            "message": f"Unsupported update keys: {', '.join(sorted(unknown_keys))}",
            "code": 10000,
        })
        sys.exit(1)

    if dry_run:
        format_json({"dry_run": True, "action": "update_integration", "params": {"integration_key": ikey, **params}})
        return

    backend = get_backend()
    result = backend.update_integration(integration_key=ikey, **params)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)

    if "reset_secret_key" in params:
        warn_secret_key()


@cli.command("activity-logs")
@click.option(
    "--since", default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.option("--limit", default=500, type=int, help="Max events to return. Default: 500.")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def activity_logs(ctx: click.Context, since: str, limit: int, fields: str | None) -> None:
    """Show activity log events."""
    backend = get_backend()
    now_ms = int(time.time() * 1000)
    delta_ms = _parse_since(since) * 1000
    mintime = now_ms - delta_ms
    results = backend.get_activity_logs(mintime=mintime, maxtime=now_ms, limit=limit)

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    _output_list(ctx, results, fields,
                 default_columns=["timestamp", "action", "actor", "target", "application", "ip"])


@cli.command("trust-monitor")
@click.option(
    "--since", default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.option("--limit", default=500, type=int, help="Max events to return. Default: 500.")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def trust_monitor(ctx: click.Context, since: str, limit: int, fields: str | None) -> None:
    """Show Trust Monitor events."""
    backend = get_backend()
    now_ms = int(time.time() * 1000)
    delta_ms = _parse_since(since) * 1000
    mintime = now_ms - delta_ms
    results = backend.get_trust_monitor_events(mintime=mintime, maxtime=now_ms, limit=limit)

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    _output_list(ctx, results, fields,
                 default_columns=["timestamp", "type", "priority", "description"])


@cli.command("schema")
@click.argument("command_name")
@click.pass_context
def schema(ctx: click.Context, command_name: str) -> None:
    """Show JSON schema describing accepted parameters for a command."""
    parent = ctx.parent
    if parent is None:
        format_error({"status": "error", "message": "No parent context", "code": 10000})
        sys.exit(1)

    cmd = cli.get_command(ctx, command_name)
    if cmd is None:
        format_error({"status": "error", "message": f"Unknown command: {command_name}", "code": 10000})
        sys.exit(1)

    params = []
    for param in cmd.params:
        if isinstance(param, click.Option):
            param_info = {
                "name": param.opts[0] if param.opts else param.name,
                "type": param.type.name,
                "required": param.required,
            }
            if param.is_flag:
                param_info["type"] = "flag"
            try:
                if param.default is not None and param.default != () and not param.required:
                    param_info["default"] = param.default
            except (TypeError, AttributeError):
                pass
            if param.help:
                param_info["help"] = param.help
            params.append(param_info)

    format_json({"command": command_name, "params": params})


def _get_oauth_client() -> OAuthClient:
    """Build an OAuthClient from env vars, or exit with a helpful message."""
    oauth_base = os.environ.get("DUO_OAUTH_BASE")
    client_id = os.environ.get("DUO_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("DUO_OAUTH_CLIENT_SECRET")
    if not oauth_base:
        format_error({"status": "error", "message": "DUO_OAUTH_BASE is required for OAuth commands (e.g. https://sso-xxx.sso.duosecurity.com/oauth2/APPID)", "code": 10000})
        raise SystemExit(1)
    return OAuthClient(oauth_base=oauth_base, client_id=client_id, client_secret=client_secret)


@cli.command("oauth-token")
@click.option("--scope", default="agent:call", help="Space-separated scopes to request. Default: agent:call.")
@click.option("--client-id", default=None, help="Override DUO_OAUTH_CLIENT_ID env var.")
@click.option("--client-secret", default=None, help="Override DUO_OAUTH_CLIENT_SECRET env var.")
@click.pass_context
def oauth_token(ctx: click.Context, scope: str, client_id: str | None, client_secret: str | None) -> None:
    """Exchange client credentials for an OAuth 2.1 access token."""
    client = _get_oauth_client()
    cid = client_id or client.client_id
    csec = client_secret or client.client_secret
    if not cid or not csec:
        format_error({"status": "error", "message": "Client ID and secret are required (via --client-id/--client-secret or DUO_OAUTH_CLIENT_ID/DUO_OAUTH_CLIENT_SECRET)", "code": 10000})
        sys.exit(1)
    result = client.get_token(client_id=cid, client_secret=csec, scope=scope)
    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)
    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)


@cli.command("oauth-introspect")
@click.option("--token", required=True, help="Access token to introspect.")
@click.pass_context
def oauth_introspect(ctx: click.Context, token: str) -> None:
    """Introspect an OAuth access token via Duo's introspection endpoint."""
    client = _get_oauth_client()
    result = client.introspect(token=token)
    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)
    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)


@cli.command("oauth-jwks")
@click.pass_context
def oauth_jwks(ctx: click.Context) -> None:
    """Fetch the JWKS (JSON Web Key Set) from Duo's SSO endpoint."""
    client = _get_oauth_client()
    result = client.get_jwks()
    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)
    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)


@cli.command("oauth-discover")
@click.pass_context
def oauth_discover(ctx: click.Context) -> None:
    """Fetch the OIDC discovery document from Duo's SSO endpoint."""
    client = _get_oauth_client()
    result = client.discover()
    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)
    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)


def _output_list(
    ctx: click.Context,
    results: list[dict],
    fields: str | None,
    default_columns: list[str] | None = None,
) -> None:
    """Filter fields and format list output (JSON or human table)."""
    if fields:
        columns = [f.strip() for f in fields.split(",")]
        results = _filter_fields(results, columns)
    else:
        columns = default_columns

    if ctx.obj["human"]:
        format_human_list(results, columns=columns)
    else:
        format_json(results)


_SINCE_MULTIPLIERS = {"m": 60, "h": 3600, "d": 86400}


def _parse_since(value: str) -> int:
    """Parse a human-friendly duration string into seconds."""
    match = re.fullmatch(r"(\d+)\s*([mhd])", value.strip().lower())
    if not match:
        raise click.BadParameter(
            f"Invalid duration '{value}'. Use format like 30m, 6h, or 7d."
        )
    amount = int(match.group(1))
    unit = match.group(2)
    return amount * _SINCE_MULTIPLIERS[unit]


def _is_error_list(results: list[dict]) -> bool:
    return len(results) == 1 and results[0].get("status") == "error"


def _filter_fields(items: list[dict], fields: list[str]) -> list[dict]:
    """Filter each item to only include the specified fields."""
    return [{k: item.get(k, "") for k in fields} for item in items]


def _filter_fields_single(item: dict, fields: list[str]) -> dict:
    """Filter a single item to only include the specified fields."""
    return {k: item.get(k, "") for k in fields}
