from __future__ import annotations

from abc import ABC, abstractmethod


class DuoBackend(ABC):
    """Abstract interface for Duo integration operations."""

    @abstractmethod
    def create_integration(self, name: str, integration_type: str) -> dict:
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
