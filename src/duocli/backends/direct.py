from __future__ import annotations

from datetime import datetime, timezone

import duo_client

from .base import DuoBackend


class DirectBackend(DuoBackend):
    """Backend that calls the Duo Admin API directly using env-var credentials."""

    def __init__(self, ikey: str, skey: str, host: str) -> None:
        self._admin = duo_client.Admin(ikey=ikey, skey=skey, host=host)

    def create_integration(self, name: str, integration_type: str, **kwargs) -> dict:
        try:
            result = self._admin.create_integration(
                name=name, integration_type=integration_type, **kwargs
            )
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {
            "status": "ok",
            "integration_key": result.get("integration_key", ""),
            "secret_key": result.get("secret_key", ""),
            "name": result.get("name", ""),
            "type": result.get("type", ""),
        }

    def delete_integration(self, integration_key: str) -> dict:
        try:
            self._admin.delete_integration(integration_key)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {"status": "ok", "integration_key": integration_key}

    def list_integrations(self) -> list[dict]:
        try:
            results = self._admin.get_integrations()
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return [
            {
                "integration_key": r.get("integration_key", ""),
                "name": r.get("name", ""),
                "type": r.get("type", ""),
            }
            for r in results
        ]

    def get_integration(self, integration_key: str) -> dict:
        try:
            result = self._admin.get_integration(integration_key)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {
            "integration_key": result.get("integration_key", ""),
            "name": result.get("name", ""),
            "type": result.get("type", ""),
            "status": result.get("status", ""),
            "policy_key": result.get("policy_key", ""),
            "notes": result.get("notes", ""),
            "enroll_policy": result.get("enroll_policy", ""),
            "groups_allowed": result.get("groups_allowed", []),
        }

    def get_info_summary(self) -> dict:
        try:
            result = self._admin.get_info_summary()
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return result

    def get_authentication_logs(
        self, mintime: int, maxtime: int, **kwargs
    ) -> list[dict]:
        try:
            response = self._admin.get_authentication_log(
                api_version=2, mintime=mintime, maxtime=maxtime, **kwargs
            )
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return [
            {
                "timestamp": _format_ts_ms(row.get("timestamp")),
                "user": row.get("user", {}).get("name", ""),
                "result": row.get("result", ""),
                "reason": row.get("reason", ""),
                "factor": row.get("factor", ""),
                "application": row.get("application", {}).get("name", ""),
                "ip": row.get("access_device", {}).get("ip", ""),
            }
            for row in response.get("authlogs", [])
        ]

    def get_auth_stats(self, mintime: int, maxtime: int) -> dict:
        try:
            result = self._admin.get_authentication_attempts(
                mintime=mintime, maxtime=maxtime
            )
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return {k.lower(): v for k, v in result.items()}

    def list_policies(self) -> list[dict]:
        try:
            results = self._admin.get_policies_v2()
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return [
            {
                "policy_key": p.get("policy_key", ""),
                "name": p.get("policy_name", ""),
                "enabled": p.get("enabled", False),
            }
            for p in results
        ]

    def get_policy(self, policy_key: str) -> dict:
        try:
            result = self._admin.get_policy_v2(policy_key)
        except RuntimeError as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
        return result

    def get_administrator_logs(self, mintime: int) -> list[dict]:
        try:
            results = self._admin.get_administrator_log(mintime=mintime)
        except RuntimeError as exc:
            return [{"status": "error", "message": str(exc), "code": 50000}]
        return [
            {
                "timestamp": _format_ts_sec(row.get("timestamp")),
                "admin": row.get("username", ""),
                "action": row.get("action", ""),
                "object": row.get("object", ""),
                "description": row.get("description", ""),
            }
            for row in results
        ]


def _format_ts_ms(ts) -> str:
    """Format a millisecond unix timestamp to ISO 8601."""
    if ts is None:
        return ""
    return datetime.fromtimestamp(int(ts) / 1000, tz=timezone.utc).isoformat()


def _format_ts_sec(ts) -> str:
    """Format a second unix timestamp to ISO 8601."""
    if ts is None:
        return ""
    return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
