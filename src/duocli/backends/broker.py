from __future__ import annotations

from .base import DuoBackend


class BrokerBackend(DuoBackend):
    """Backend that calls a remote broker endpoint via HTTP.

    The broker holds Duo Admin API credentials and provides per-user
    accountability by validating the caller's OIDC bearer token.

    Not yet implemented — planned for Phase 2.
    """

    def __init__(self, url: str, token: str) -> None:
        self._url = url
        self._token = token

    def create_integration(self, name: str, integration_type: str) -> dict:
        raise NotImplementedError(
            "Broker mode is not yet implemented. Use direct mode with "
            "DUO_IKEY, DUO_SKEY, and DUO_HOST environment variables."
        )

    def delete_integration(self, integration_key: str) -> dict:
        raise NotImplementedError(
            "Broker mode is not yet implemented. Use direct mode with "
            "DUO_IKEY, DUO_SKEY, and DUO_HOST environment variables."
        )

    def list_integrations(self) -> list[dict]:
        raise NotImplementedError(
            "Broker mode is not yet implemented. Use direct mode with "
            "DUO_IKEY, DUO_SKEY, and DUO_HOST environment variables."
        )
