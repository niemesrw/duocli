from __future__ import annotations

import duo_client

from .base import DuoBackend


class DirectBackend(DuoBackend):
    """Backend that calls the Duo Admin API directly using env-var credentials."""

    def __init__(self, ikey: str, skey: str, host: str) -> None:
        self._admin = duo_client.Admin(ikey=ikey, skey=skey, host=host)

    def create_integration(self, name: str, integration_type: str) -> dict:
        try:
            result = self._admin.create_integration(
                name=name, integration_type=integration_type
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
