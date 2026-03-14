from __future__ import annotations

import os
import pytest

from duocli.backends import get_backend
from duocli.backends.direct import DirectBackend
from duocli.backends.broker import BrokerBackend


def _clear_env(monkeypatch):
    """Remove all duocli-related env vars."""
    for var in ("DUOCLI_BROKER_URL", "DUOCLI_BROKER_TOKEN", "DUO_IKEY", "DUO_SKEY", "DUO_HOST"):
        monkeypatch.delenv(var, raising=False)


class TestGetBackend:
    def test_direct_mode(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("DUO_IKEY", "DITEST")
        monkeypatch.setenv("DUO_SKEY", "testskey")
        monkeypatch.setenv("DUO_HOST", "api-test.duosecurity.com")

        backend = get_backend()
        assert isinstance(backend, DirectBackend)

    def test_broker_mode(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("DUOCLI_BROKER_URL", "https://broker.example.com")
        monkeypatch.setenv("DUOCLI_BROKER_TOKEN", "test-token")

        backend = get_backend()
        assert isinstance(backend, BrokerBackend)

    def test_broker_url_without_token_fails(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("DUOCLI_BROKER_URL", "https://broker.example.com")

        with pytest.raises(SystemExit) as exc_info:
            get_backend()
        assert exc_info.value.code == 1

    def test_no_credentials_fails(self, monkeypatch):
        _clear_env(monkeypatch)

        with pytest.raises(SystemExit) as exc_info:
            get_backend()
        assert exc_info.value.code == 1

    def test_partial_direct_credentials_fails(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("DUO_IKEY", "DITEST")
        # Missing DUO_SKEY and DUO_HOST

        with pytest.raises(SystemExit) as exc_info:
            get_backend()
        assert exc_info.value.code == 1

    def test_broker_takes_priority_over_direct(self, monkeypatch):
        _clear_env(monkeypatch)
        monkeypatch.setenv("DUOCLI_BROKER_URL", "https://broker.example.com")
        monkeypatch.setenv("DUOCLI_BROKER_TOKEN", "test-token")
        monkeypatch.setenv("DUO_IKEY", "DITEST")
        monkeypatch.setenv("DUO_SKEY", "testskey")
        monkeypatch.setenv("DUO_HOST", "api-test.duosecurity.com")

        backend = get_backend()
        assert isinstance(backend, BrokerBackend)
