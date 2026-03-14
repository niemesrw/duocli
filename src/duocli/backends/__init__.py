from __future__ import annotations

import os
import sys

from .base import DuoBackend
from .direct import DirectBackend


def get_backend() -> DuoBackend:
    """Select and return the appropriate backend based on environment variables."""
    broker_url = os.environ.get("DUOCLI_BROKER_URL")

    if broker_url:
        broker_token = os.environ.get("DUOCLI_BROKER_TOKEN")
        if not broker_token:
            print(
                "DUOCLI_BROKER_URL is set but DUOCLI_BROKER_TOKEN is missing.\n"
                "Broker mode requires both variables. Set DUOCLI_BROKER_TOKEN to "
                "an OIDC bearer token for the broker endpoint.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        from .broker import BrokerBackend

        return BrokerBackend(url=broker_url, token=broker_token)

    ikey = os.environ.get("DUO_IKEY")
    skey = os.environ.get("DUO_SKEY")
    host = os.environ.get("DUO_HOST")

    if ikey and skey and host:
        return DirectBackend(ikey=ikey, skey=skey, host=host)

    print(
        "No Duo credentials configured.\n\n"
        "Direct mode:  set DUO_IKEY, DUO_SKEY, and DUO_HOST\n"
        "Broker mode:  set DUOCLI_BROKER_URL and DUOCLI_BROKER_TOKEN",
        file=sys.stderr,
    )
    raise SystemExit(1)
