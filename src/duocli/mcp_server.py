"""MCP server exposing read-only duocli operations as tools."""

from __future__ import annotations

import time

from dotenv import load_dotenv
from fastmcp import FastMCP

from duocli.backends import get_backend

load_dotenv()

mcp = FastMCP("duocli")


def _since_to_seconds(since: str) -> int:
    """Convert a human duration like '24h' or '7d' to seconds."""
    multipliers = {"m": 60, "h": 3600, "d": 86400}
    unit = since[-1].lower()
    if unit not in multipliers:
        raise ValueError(f"Invalid since format: {since}. Use e.g. 30m, 24h, 7d")
    return int(since[:-1]) * multipliers[unit]


@mcp.tool
def list_apps() -> list[dict]:
    """List all Duo integrations with their name, type, and integration key."""
    backend = get_backend()
    return backend.list_integrations()


@mcp.tool
def get_app(integration_key: str) -> dict:
    """Get details of a single Duo integration by its integration key (starts with DI)."""
    backend = get_backend()
    return backend.get_integration(integration_key=integration_key)


@mcp.tool
def info_summary() -> dict:
    """Get Duo account summary: user count, admin count, integration count, edition, telephony credits."""
    backend = get_backend()
    return backend.get_info_summary()


@mcp.tool
def auth_logs(since: str = "24h") -> list[dict]:
    """Get authentication log events. Use 'since' for time window: 30m, 1h, 24h, 7d, 30d."""
    backend = get_backend()
    now_ms = int(time.time() * 1000)
    delta_ms = _since_to_seconds(since) * 1000
    return backend.get_authentication_logs(mintime=now_ms - delta_ms, maxtime=now_ms)


@mcp.tool
def admin_logs(since: str = "24h") -> list[dict]:
    """Get administrator action log events. Use 'since' for time window: 30m, 1h, 24h, 7d, 30d."""
    backend = get_backend()
    now_sec = int(time.time())
    delta_sec = _since_to_seconds(since)
    return backend.get_administrator_logs(mintime=now_sec - delta_sec)


@mcp.tool
def auth_stats(since: str = "24h") -> dict:
    """Get aggregate authentication attempt counts (success, failure, etc). Use 'since' for time window."""
    backend = get_backend()
    now_sec = int(time.time())
    delta_sec = _since_to_seconds(since)
    return backend.get_auth_stats(mintime=now_sec - delta_sec, maxtime=now_sec)


@mcp.tool
def list_policies() -> list[dict]:
    """List all Duo policies with their configuration."""
    backend = get_backend()
    return backend.list_policies()


if __name__ == "__main__":
    mcp.run()
