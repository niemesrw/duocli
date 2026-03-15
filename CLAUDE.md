# duocli

CLI for managing Duo Security integrations via the Admin API. Supports CRUD on applications, policy inspection, and log retrieval. Currently in Phase 1 (direct API access); Phase 2 (broker mode) is stubbed.

## Quick start

```bash
# Credentials (direct mode) — set in .env or export
export DUO_IKEY=your_integration_key
export DUO_SKEY=your_secret_key
export DUO_HOST=api-XXXXXXXX.duosecurity.com

# Run
uv run duo create-app --name "My App" --type websdk
uv run duo list-apps --human

# Tests
uv run pytest tests/ -v
```

## Architecture

### Backend abstraction

`DuoBackend` (ABC in `backends/base.py`) defines all operations. Two implementations:

- **DirectBackend** (`backends/direct.py`) — wraps `duo_client.Admin`, catches `RuntimeError` → returns `{"status": "error", "message": ..., "code": 50000}`. Never raises.
- **BrokerBackend** (`backends/broker.py`) — Phase 2 stub, all methods raise `NotImplementedError`.

`get_backend()` in `backends/__init__.py` selects mode by env vars. Broker takes priority if both are set.

### CLI patterns

All commands in `cli.py` follow: validate inputs → check `--dry-run` → `get_backend()` → call method → check for error status → format output.

### Output contract

- **Success**: JSON to stdout (default) or human-readable table/key-value with `--human`
- **Errors**: Always JSON to stdout + diagnostic to stderr, even with `--human`
- **Exit codes**: `0` success, `1` input/validation/credential error, `2` API error

## Key conventions

- **Env vars only for credentials** — no CLI flags for secrets
- **Backends catch RuntimeError** → return error dicts with `"code": 50000` (never raise)
- **Input validation before backend selection** — `--dry-run` works without credentials
- **Type passthrough** — no client-side enum validation on Duo types; extra kwargs forwarded to SDK
- **update-app key allowlist** — `_VALID_UPDATE_KEYS` frozenset; unknown keys → exit(1) with code 10000
- **Normalized flat responses** — backends reshape SDK dicts to a standard flat structure with safe defaults

## Testing

pytest + Click `CliRunner`. 98 tests across 4 files.

**Mocking pattern**:
```python
@patch("duocli.cli.load_dotenv")
@patch("duocli.cli.get_backend")
def test_something(mock_backend, mock_dotenv):
    backend = MagicMock()
    mock_backend.return_value = backend
    backend.some_method.return_value = {"status": "ok", ...}
```

**Test ordering per command**: help → missing args → validation → dry-run → success → error → fields

## File map

```
src/duocli/
├── cli.py              # Click group + all 14 commands
├── output.py           # format_json, format_error, format_human_list/single
├── validate.py         # validate_integration_key, validate_name, validate_type
└── backends/
    ├── __init__.py     # get_backend() factory
    ├── base.py         # DuoBackend ABC
    ├── direct.py       # DirectBackend (Duo SDK wrapper)
    └── broker.py       # BrokerBackend (Phase 2 stub)

tests/
├── test_cli.py              # Command tests (bulk of tests)
├── test_output.py           # Output formatter tests
├── test_backend_selection.py # Backend selection logic
└── test_validate.py         # Input validator tests
```

## Adding a new command

1. Add abstract method to `DuoBackend` in `backends/base.py`
2. Implement in `DirectBackend` — catch `RuntimeError`, return normalized dict
3. Add `NotImplementedError` stub in `BrokerBackend`
4. Add Click command in `cli.py` — follow validate → dry-run → backend → error check → format pattern
5. Add tests in `test_cli.py` — help, validation, dry-run, success, error cases
6. Commit
