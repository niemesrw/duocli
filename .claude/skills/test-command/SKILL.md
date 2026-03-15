---
name: test-command
description: |
  Run tests for a specific duocli command by name. Use when the user says
  "test auth-logs", "run tests for create-app", or wants to verify a
  single command works. Maps command names to pytest selectors.
disable-model-invocation: true
---

# Test a Specific duocli Command

Run tests for a single command without running the full suite.

## Usage

When the user says "test <command-name>", convert the command name to a pytest selector:

```bash
# Convert kebab-case command to snake_case for test matching
# e.g., "auth-logs" → "auth_logs", "create-app" → "create_app"
uv run pytest tests/test_cli.py -k "<snake_case_name>" -v
```

## Command → Test Class Mapping

| Command | Test selector | What it covers |
|---------|--------------|----------------|
| `create-app` | `-k "create_app"` | Help, validation, dry-run, success, error, JSON payload |
| `delete-app` | `-k "delete_app"` | Help, validation, dry-run, success, error |
| `list-apps` | `-k "list_apps"` | Help, success, error, fields |
| `get-app` | `-k "GetApp"` | Help, validation, dry-run, success, error, fields |
| `update-app` | `-k "UpdateApp"` | Help, validation, dry-run, key allowlist, success, error |
| `info-summary` | `-k "InfoSummary"` | Help, success, error |
| `list-policies` | `-k "ListPolicies"` | Help, success, error, fields |
| `get-policy` | `-k "GetPolicy"` | Help, success, error, fields |
| `auth-logs` | `-k "auth_logs"` | Help, success, error, fields |
| `admin-logs` | `-k "admin_logs"` | Help, success, error, fields |
| `auth-stats` | `-k "AuthStats"` | Help, success, error |
| `activity-logs` | `-k "ActivityLogs"` | Help, success, error, fields |
| `trust-monitor` | `-k "TrustMonitor"` | Help, success, error, fields |
| `schema` | `-k "Schema"` | Help, valid command, invalid command |

## Run all tests for a module

```bash
uv run pytest tests/test_cli.py -v          # All CLI tests
uv run pytest tests/test_validate.py -v     # Validation tests
uv run pytest tests/test_output.py -v       # Output formatting tests
uv run pytest tests/test_backend_selection.py -v  # Backend selection tests
```

## Run full suite

```bash
uv run pytest tests/ -v
```
