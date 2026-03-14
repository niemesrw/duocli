# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "duo-client>=5.0",
#     "click>=8.0",
#     "python-dotenv>=1.0",
# ]
# ///
"""duocli — Duo Security CLI tool.

Run with: uv run run_duocli.py [command] [options]
"""

import sys
import os

# Add src/ to path so duocli package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from duocli.cli import cli

if __name__ == "__main__":
    cli()
