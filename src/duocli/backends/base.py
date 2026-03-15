from __future__ import annotations

from abc import ABC, abstractmethod


class DuoBackend(ABC):
    """Abstract interface for Duo integration operations."""

    @abstractmethod
    def create_integration(self, name: str, integration_type: str, **kwargs) -> dict:
        """Create a new integration. Returns normalized result dict."""
        ...

    @abstractmethod
    def delete_integration(self, integration_key: str) -> dict:
        """Delete an integration by its key. Returns normalized result dict."""
        ...

    @abstractmethod
    def list_integrations(self) -> list[dict]:
        """List all integrations. Returns list of normalized dicts."""
        ...

    @abstractmethod
    def get_integration(self, integration_key: str) -> dict:
        """Get a single integration by key. Returns normalized result dict."""
        ...

    @abstractmethod
    def get_info_summary(self) -> dict:
        """Get summary counts of objects in the account."""
        ...

    @abstractmethod
    def get_authentication_logs(
        self, mintime: int, maxtime: int, **kwargs
    ) -> list[dict]:
        """Get authentication log events. Times are unix timestamps in ms."""
        ...

    @abstractmethod
    def get_administrator_logs(self, mintime: int) -> list[dict]:
        """Get administrator action log events. mintime is a unix timestamp in seconds."""
        ...
