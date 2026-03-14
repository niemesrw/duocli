#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["duo-client>=5.0", "click>=8.0", "python-dotenv>=1.0"]
# ///
"""Duo Security CLI — manage integrations from the command line.

Usage (standalone via uv):
    uv run duo create-app --name "My App" --type websdk
    uv run duo delete-app --ikey DIXXXXXXXXXXXXXXXXXX
    uv run duo list-apps
    uv run duo --human list-apps

Usage (installed):
    duocli create-app --name "My App" --type websdk

Environment variables:
    Direct mode:  DUO_IKEY, DUO_SKEY, DUO_HOST
    Broker mode:  DUOCLI_BROKER_URL, DUOCLI_BROKER_TOKEN
"""

import sys
import os

# Allow running as a standalone script by adding src/ to the path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from duocli.cli import cli

if __name__ == "__main__":
    cli()
