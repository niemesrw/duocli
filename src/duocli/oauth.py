"""OAuth 2.1 / OIDC helpers for Duo SSO endpoints.

These hit the Duo SSO URLs directly (not the Admin API), so they use
``requests`` rather than ``duo_client.Admin``.

Duo OAuth 2.1 apps use per-application endpoints:
    https://<sso-host>/oauth2/<app-id>/token
    https://<sso-host>/oauth2/<app-id>/jwks
    etc.

Set DUO_OAUTH_BASE to the full base URL, e.g.:
    https://sso-XXXXXXXX.sso.duosecurity.com/oauth2/DIXXXXXXXXXXXXXXXXXX
"""
from __future__ import annotations

import requests


class OAuthClient:
    """Thin wrapper around Duo OAuth 2.1 endpoints."""

    def __init__(
        self,
        oauth_base: str,
        client_id: str | None = None,
        client_secret: str | None = None,
    ) -> None:
        self.oauth_base = oauth_base.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret

    # ── Client Credentials grant ──────────────────────────────────────

    def get_token(
        self,
        client_id: str,
        client_secret: str,
        scope: str = "agent:call",
    ) -> dict:
        """Exchange client credentials for an access token."""
        try:
            resp = requests.post(
                f"{self.oauth_base}/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "scope": scope,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "access_token": data.get("access_token", ""),
                "token_type": data.get("token_type", ""),
                "expires_in": data.get("expires_in", 0),
                "scope": data.get("scope", ""),
            }
        except requests.RequestException as exc:
            return {"status": "error", "message": str(exc), "code": 50000}

    # ── Token introspection ───────────────────────────────────────────

    def introspect(self, token: str) -> dict:
        """Introspect an access token."""
        try:
            resp = requests.post(
                f"{self.oauth_base}/token_introspection",
                data={"token": token},
                auth=(self.client_id or "", self.client_secret or ""),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            return {"status": "error", "message": str(exc), "code": 50000}

    # ── JWKS ──────────────────────────────────────────────────────────

    def get_jwks(self) -> dict:
        """Fetch the JSON Web Key Set."""
        try:
            resp = requests.get(f"{self.oauth_base}/jwks", timeout=15)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            return {"status": "error", "message": str(exc), "code": 50000}

    # ── OIDC Discovery ────────────────────────────────────────────────

    def discover(self) -> dict:
        """Fetch the OIDC discovery document."""
        try:
            resp = requests.get(
                f"{self.oauth_base}/.well-known/openid-configuration",
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            return {"status": "error", "message": str(exc), "code": 50000}
