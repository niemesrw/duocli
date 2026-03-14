# duocli — Duo Security CLI Tool Design Spec

## Problem

Managing Duo Security integrations (applications) currently requires either the Duo Admin Panel UI or direct API scripting. There's no CLI tool that:
- LLM coding agents can invoke via shell commands
- Provides per-user accountability when using shared Admin API credentials
- Can be distributed as an open-source tool for others to deploy in their own environments

The raw Duo Admin API keys are static god-mode credentials with no built-in audit trail of who performed an action. Organizations need a way to broker access with identity and logging.

## Solution

An open-source Python CLI tool (`duocli`) with two operating modes:

1. **Direct mode** — reads Duo Admin API keys from environment variables (for local dev, solo use, or trusted automation)
2. **Broker mode** — CLI calls a self-deployed Lambda/API Gateway that holds the keys, authenticates the caller via a bearer token, and logs actions with caller identity

## Phasing

- **Phase 1**: CLI with direct mode + pluggable backend abstraction
- **Phase 2**: Reference AWS Lambda broker (CDK stack) with audit logging

---

## CLI Interface

### Commands

```bash
# Create an integration
duocli create-app --name "My Web App" --type websdk

# Delete an integration
duocli delete-app --ikey DIXXXXXXXXXXXXXXXXXX

# List integrations (useful for discovery)
duocli list-apps
```

### Output

JSON to stdout by default (LLM-friendly). `--human` formats successful results as tables.

Output contract:
- On success, the command writes exactly one structured result object or array to stdout.
- On failure, the command writes exactly one structured error object to stdout and may write a short human-readable diagnostic to stderr.
- `--human` affects only successful output formatting. Errors remain structured JSON on stdout so callers can parse them consistently.
- Warnings, debug output, and informational messages go to stderr.

**Success:**
```json
{"status": "ok", "integration_key": "DI...", "secret_key": "...", "name": "My Web App", "type": "websdk"}
```

**Error:**
```json
{"status": "error", "message": "Integration not found", "code": 40401}
```

### Exit Codes

- `0` — success
- `1` — user/input error (missing args, invalid flags, missing required auth configuration)
- `2` — API/network error (Duo API failure, broker failure, connection timeout)

### Global Flags

- `--human` — human-readable table output instead of JSON for successful responses
- `--version` — print version and exit
- `--help` — descriptive help text (important for LLM agent discoverability)

### Integration Type Handling

The `--type` value is passed through to the Duo Admin API without client-side validation. The API rejects invalid types with a clear error message. This avoids hardcoding a type list that changes over time. Valid types include `websdk`, `1password`, `adminapi`, etc. — see [Duo Admin API docs](https://duo.com/docs/adminapi#integrations) for the full list.

### Optional Parameters

Phase 1 exposes only `--name` and `--type` for `create-app`. Additional `create_integration` parameters such as `enroll_policy`, `adminapi_*` permissions, and `groups_allowed` are out of scope for Phase 1. A future enhancement could add `--param key=value` pass-through for power users.

---

## Architecture

### Project Structure

```
duocli/
├── duocli.py              # uv inline script entrypoint (thin dispatcher)
├── pyproject.toml         # Package metadata, dependencies, CLI entry point
├── src/
│   └── duocli/
│       ├── __init__.py
│       ├── cli.py         # Click CLI definition
│       ├── output.py      # JSON + human-readable output formatting
│       └── backends/
│           ├── __init__.py # get_backend() selection logic
│           ├── base.py    # DuoBackend abstract interface
│           ├── direct.py  # Wraps duo_client.Admin, reads env vars
│           └── broker.py  # Calls Lambda/API Gateway endpoint
├── broker/                # Phase 2: Reference AWS CDK stack
│   ├── cdk/
│   └── lambda/
└── tests/
```

### Backend Abstraction

The abstraction is at the operation level, not the client level. In broker mode, the CLI has no Duo credentials and cannot construct a `duo_client.Admin`. The backend interface defines the operations, and each implementation handles auth differently.

```python
from abc import ABC, abstractmethod

class DuoBackend(ABC):
    @abstractmethod
    def create_integration(self, name: str, integration_type: str) -> dict: ...

    @abstractmethod
    def delete_integration(self, integration_key: str) -> dict: ...

    @abstractmethod
    def list_integrations(self) -> list[dict]: ...

class DirectBackend(DuoBackend):
    """Reads DUO_IKEY, DUO_SKEY, DUO_HOST from environment.
    Wraps duo_client.Admin internally."""
    ...

class BrokerBackend(DuoBackend):
    """Calls a remote broker endpoint via HTTP."""
    ...
```

### Backend Selection Logic

1. If `DUOCLI_BROKER_URL` is set:
   - If `DUOCLI_BROKER_TOKEN` is also set → `BrokerBackend`
   - Otherwise → error with clear setup instructions for broker authentication
2. If `DUO_IKEY` + `DUO_SKEY` + `DUO_HOST` are all set → `DirectBackend`
3. Otherwise → error with clear setup instructions

### DirectBackend

Wraps `duo_client.Admin` internally:
- Constructs `duo_client.Admin(ikey, skey, host)` from env vars
- Calls `admin.create_integration(name, integration_type)` and returns a normalized dict
- Calls `admin.delete_integration(ikey)` and returns a success/failure dict
- Calls `admin.get_integrations()` for listing and handles pagination via the generator
- Catches `RuntimeError` from `duo_client` and converts it to structured error dicts

### BrokerBackend

Calls the broker over HTTPS:
- Sends `Authorization: Bearer <token>` on every request
- Expects the broker to validate the token against a configured OIDC issuer and audience
- Relies on the broker to log a stable caller identifier from claims such as `sub` and `email`
- Returns the same normalized success/error shapes as `DirectBackend`

This bearer-token contract is the mechanism that provides per-user accountability in broker mode.

### Output Layer

- `format_json(data)` — writes structured success or error JSON to stdout
- `format_human(data)` — writes tabular output to stdout for successful responses only
- `format_error(data)` — writes structured error JSON to stdout plus an optional one-line diagnostic to stderr
- All warnings and debug output go to stderr

---

## Distribution

### uv inline script

`duocli.py` at the repo root with inline metadata:

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["duo-client>=5.0", "click>=8.0"]
# ///
```

Users can run: `uv run duocli.py create-app --name "Foo" --type websdk`

### Package install

`pyproject.toml` with `[project.scripts]` entry point so `pip install .` or `uv pip install .` makes `duocli` available as a command.

---

## Dependencies

- `duo-client` (>=5.0) — Official Duo Python client
- `click` (>=8.0) — CLI framework with clean help text and argument parsing
- Python >=3.9

---

## Reference Broker (Phase 2)

### Components

- **API Gateway** — HTTPS endpoint
- **API Gateway authorizer or Lambda validation layer** — validates the caller's bearer token against a configured OIDC issuer and audience
- **Lambda** — reads validated identity claims, proxies to the Duo Admin API, and logs actions
- **Secrets Manager** — stores Duo Admin API keys (`ikey`, `skey`, `host`)
- **CloudWatch Logs** — structured audit trail with who, what, when, request id, command, and target integration key

### Auth for Broker

Reference implementation uses OIDC bearer tokens so each request carries a unique caller identity. The broker validates the token and logs `sub` plus a human-meaningful claim such as `email` when present.

For service-to-service automation, a future non-human auth mode may be added, but that mode would not satisfy the per-user accountability requirement and should be documented separately.

### CDK Stack

AWS CDK (TypeScript) in `broker/cdk/` per blanxlait conventions.

---

## Security Considerations

- Admin API secret key must never be logged or included in error output
- In direct mode, Phase 1 accepts Duo credentials only via environment variables; no credential CLI flags are supported
- Broker mode keys live in Secrets Manager, never on the CLI user's machine
- Broker mode audit logs must include the validated caller identity from the bearer token, not just network metadata such as source IP
- `create-app` output includes the new integration's secret key, so print a stderr warning: `"WARNING: secret_key is sensitive — store securely"`
- `list-apps` does not return secret keys because the Duo API does not include them in list responses
- Consider adding `--no-secret` to `create-app` in a future version to suppress the secret from output when stdout may be logged

---

## Testing

- Unit tests for backend selection logic
- Unit tests for broker auth preconditions (`DUOCLI_BROKER_URL` without `DUOCLI_BROKER_TOKEN` should fail clearly)
- Unit tests for output formatting
- Unit tests for the error emission contract (structured error on stdout, optional diagnostic on stderr)
- Integration test against the Duo Admin API (requires real credentials, run manually)
- CLI smoke tests: `duocli --help`, `duocli create-app --help`

---

## Verification Plan

1. `uv run duocli.py --help` — should show commands and descriptions
2. `uv run duocli.py create-app --name "Test" --type websdk` — should create an integration in direct mode when Duo credentials are configured
3. `uv run duocli.py list-apps` — should list integrations as JSON
4. `uv run duocli.py delete-app --ikey <from step 2>` — should delete the integration
5. Verify `--human` produces table output for successful responses
6. Verify missing direct-mode credentials produce a clear error message and exit code `1`
7. Verify broker mode fails clearly if `DUOCLI_BROKER_URL` is set without `DUOCLI_BROKER_TOKEN`
8. Verify error responses remain JSON on stdout even when `--human` is set
