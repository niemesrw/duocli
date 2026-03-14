# duocli

CLI tool for managing Duo Security integrations.

## Quick Start

```bash
# Set credentials
export DUO_IKEY=your_integration_key
export DUO_SKEY=your_secret_key
export DUO_HOST=api-XXXXXXXX.duosecurity.com

# Run with uv (no install needed)
uv run duocli.py list-apps
uv run duocli.py create-app --name "My App" --type websdk
uv run duocli.py delete-app --ikey DIXXXXXXXXXXXXXXXXXX
```
