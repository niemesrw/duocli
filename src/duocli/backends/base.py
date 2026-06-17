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

    @abstractmethod
    def get_auth_stats(self, mintime: int, maxtime: int) -> dict:
        """Get authentication attempt counts. Times are unix timestamps in seconds."""
        ...

    @abstractmethod
    def list_policies(self) -> list[dict]:
        """List all policies. Returns list of normalized dicts."""
        ...

    @abstractmethod
    def get_policy(self, policy_key: str) -> dict:
        """Get a single policy by key. Returns normalized result dict."""
        ...

    @abstractmethod
    def update_integration(self, integration_key: str, **kwargs) -> dict:
        """Update an integration. Returns normalized result dict."""
        ...

    @abstractmethod
    def get_user(self, username: str | None = None, user_id: str | None = None) -> dict:
        """Get a user by username or user_id. Returns normalized result dict."""
        ...

    @abstractmethod
    def get_user_groups(self, user_id: str) -> list[dict]:
        """Get groups for a user. Returns list of normalized dicts."""
        ...

    @abstractmethod
    def get_user_devices(self, user_id: str) -> dict:
        """Get phones, tokens, and WebAuthn credentials for a user."""
        ...

    @abstractmethod
    def calculate_policy(self, integration_key: str, user_id: str) -> dict:
        """Calculate the effective policy for a user and integration."""
        ...

    @abstractmethod
    def enroll_user(self, username: str, email: str, valid_secs: int | None = None) -> dict:
        """Enroll a user and send them an enrollment email."""
        ...

    @abstractmethod
    def send_sms_activation(self, user_id: str, valid_secs: int | None = None) -> dict:
        """Send Duo Mobile activation SMS to a user's first phone."""
        ...

    @abstractmethod
    def get_activity_logs(
        self, mintime: int, maxtime: int, limit: int = 500,
    ) -> list[dict]:
        """Get activity log events. Times are unix timestamps in ms. Limit caps event count."""
        ...

    @abstractmethod
    def get_trust_monitor_events(
        self, mintime: int, maxtime: int, limit: int = 500,
    ) -> list[dict]:
        """Get Trust Monitor events. Times are unix timestamps in ms. Limit caps event count."""
        ...
