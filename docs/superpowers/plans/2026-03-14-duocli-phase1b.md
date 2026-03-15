# duocli Phase 1b Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add provisioning + security ops commands to duocli (get-app, info-summary, list-policies, get-policy, update-app, activity-logs, trust-monitor, auth-stats).

**Architecture:** Eight new CLI commands following existing patterns. Each command gets a backend abstract method, DirectBackend implementation, BrokerBackend stub, CLI handler, and tests. A single-item field filtering helper and update-app key allowlist are the only new shared utilities.

**Tech Stack:** Python 3.9+, Click, duo_client, pytest

**Spec:** `docs/superpowers/specs/2026-03-14-duocli-phase1b-design.md`

---

## File Structure

| File | Change | Responsibility |
|------|--------|---------------|
| `src/duocli/backends/base.py` | Modify | Add 8 abstract methods |
| `src/duocli/backends/direct.py` | Modify | Implement 8 methods wrapping duo_client |
| `src/duocli/backends/broker.py` | Modify | Add 8 NotImplementedError stubs |
| `src/duocli/cli.py` | Modify | Add 8 CLI commands, `_filter_fields_single()`, `_VALID_UPDATE_KEYS` |
| `tests/test_cli.py` | Modify | Tests for all 8 new commands |

---

## Chunk 1: Easy Reads (get-app, info-summary, auth-stats)

### Task 1: `get-app` backend + CLI + tests

**Files:**
- Modify: `src/duocli/backends/base.py`
- Modify: `src/duocli/backends/direct.py`
- Modify: `src/duocli/backends/broker.py`
- Modify: `src/duocli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add `get_integration` to backend ABC**

In `src/duocli/backends/base.py`, add after `list_integrations`:

```python
@abstractmethod
def get_integration(self, integration_key: str) -> dict:
    """Get a single integration by key. Returns normalized result dict."""
    ...
```

- [ ] **Step 2: Implement in DirectBackend**

In `src/duocli/backends/direct.py`, add after `list_integrations`:

```python
def get_integration(self, integration_key: str) -> dict:
    try:
        result = self._admin.get_integration(integration_key)
    except RuntimeError as exc:
        return {"status": "error", "message": str(exc), "code": 50000}
    return {
        "integration_key": result.get("integration_key", ""),
        "name": result.get("name", ""),
        "type": result.get("type", ""),
        "status": result.get("status", ""),
        "policy_key": result.get("policy_key", ""),
        "notes": result.get("notes", ""),
        "enroll_policy": result.get("enroll_policy", ""),
        "groups_allowed": result.get("groups_allowed", []),
    }
```

- [ ] **Step 3: Stub in BrokerBackend**

In `src/duocli/backends/broker.py`, add:

```python
def get_integration(self, integration_key: str) -> dict:
    raise NotImplementedError(_NOT_IMPLEMENTED_MSG)
```

- [ ] **Step 4: Add `_filter_fields_single()` helper to cli.py**

In `src/duocli/cli.py`, add after `_filter_fields`:

```python
def _filter_fields_single(item: dict, fields: list[str]) -> dict:
    """Filter a single item to only include the specified fields."""
    return {k: item.get(k, "") for k in fields}
```

- [ ] **Step 5: Add `get-app` CLI command**

In `src/duocli/cli.py`, add after `list_apps`:

```python
@cli.command("get-app")
@click.option("--ikey", required=True, help="Integration key of the app to retrieve.")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.option("--dry-run", is_flag=True, help="Validate inputs and show what would happen without calling API.")
@click.pass_context
def get_app(ctx: click.Context, ikey: str, fields: str | None, dry_run: bool) -> None:
    """Get details of a single Duo integration."""
    validate_integration_key(ikey)

    if dry_run:
        format_json({"dry_run": True, "action": "get_integration", "params": {"integration_key": ikey}})
        return

    backend = get_backend()
    result = backend.get_integration(integration_key=ikey)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if fields:
        field_list = [f.strip() for f in fields.split(",")]
        result = _filter_fields_single(result, field_list)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)
```

- [ ] **Step 6: Write tests for `get-app`**

In `tests/test_cli.py`, add:

```python
class TestGetApp:
    def test_get_app_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-app", "--help"])
        assert result.exit_code == 0
        assert "--ikey" in result.output
        assert "--fields" in result.output

    def test_get_app_rejects_bad_ikey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-app", "--ikey", "BADKEY"])
        assert result.exit_code != 0

    @patch("duocli.cli.load_dotenv")
    def test_get_app_dry_run(self, mock_dotenv):
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["get-app", "--ikey", ikey, "--dry-run"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["params"]["integration_key"] == ikey

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_get_app_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_integration.return_value = {
            "integration_key": "DIAAAAAAAAAAAAAAAAA",
            "name": "Test App",
            "type": "websdk",
            "status": "active",
            "policy_key": "",
            "notes": "",
            "enroll_policy": "",
            "groups_allowed": [],
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["get-app", "--ikey", "DIAAAAAAAAAAAAAAAAA"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Test App"

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_get_app_fields(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_integration.return_value = {
            "integration_key": "DIAAAAAAAAAAAAAAAAA",
            "name": "Test App",
            "type": "websdk",
            "status": "active",
            "policy_key": "",
            "notes": "",
            "enroll_policy": "",
            "groups_allowed": [],
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["get-app", "--ikey", "DIAAAAAAAAAAAAAAAAA", "--fields", "name,type"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert set(data.keys()) == {"name", "type"}
```

- [ ] **Step 7: Run tests**

Run: `uv run pytest tests/test_cli.py -v -k "get_app"`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add src/duocli/backends/base.py src/duocli/backends/direct.py src/duocli/backends/broker.py src/duocli/cli.py tests/test_cli.py
git commit -m "Add get-app command for single integration lookup"
```

---

### Task 2: `info-summary` backend + CLI + tests

**Files:**
- Modify: `src/duocli/backends/base.py`
- Modify: `src/duocli/backends/direct.py`
- Modify: `src/duocli/backends/broker.py`
- Modify: `src/duocli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add `get_info_summary` to backend ABC**

In `src/duocli/backends/base.py`, add:

```python
@abstractmethod
def get_info_summary(self) -> dict:
    """Get summary counts of objects in the account."""
    ...
```

- [ ] **Step 2: Implement in DirectBackend**

In `src/duocli/backends/direct.py`, add:

```python
def get_info_summary(self) -> dict:
    try:
        result = self._admin.get_info_summary()
    except RuntimeError as exc:
        return {"status": "error", "message": str(exc), "code": 50000}
    return result
```

- [ ] **Step 3: Stub in BrokerBackend**

```python
def get_info_summary(self) -> dict:
    raise NotImplementedError(_NOT_IMPLEMENTED_MSG)
```

- [ ] **Step 4: Add `info-summary` CLI command**

In `src/duocli/cli.py`, add:

```python
@cli.command("info-summary")
@click.pass_context
def info_summary(ctx: click.Context) -> None:
    """Show summary counts of objects in the Duo account."""
    backend = get_backend()
    result = backend.get_info_summary()

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)
```

- [ ] **Step 5: Write tests**

```python
class TestInfoSummary:
    def test_info_summary_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["info-summary", "--help"])
        assert result.exit_code == 0

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_info_summary_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_info_summary.return_value = {
            "integration_count": 5,
            "user_count": 10,
            "admin_count": 2,
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["info-summary"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["integration_count"] == 5

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_info_summary_error(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_info_summary.return_value = {
            "status": "error", "message": "API error", "code": 50000,
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["info-summary"])
        assert result.exit_code == 2
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/test_cli.py -v -k "info_summary"`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/duocli/backends/base.py src/duocli/backends/direct.py src/duocli/backends/broker.py src/duocli/cli.py tests/test_cli.py
git commit -m "Add info-summary command for account object counts"
```

---

### Task 3: `auth-stats` backend + CLI + tests

**Files:**
- Modify: `src/duocli/backends/base.py`
- Modify: `src/duocli/backends/direct.py`
- Modify: `src/duocli/backends/broker.py`
- Modify: `src/duocli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add `get_auth_stats` to backend ABC**

In `src/duocli/backends/base.py`, add:

```python
@abstractmethod
def get_auth_stats(self, mintime: int, maxtime: int) -> dict:
    """Get authentication attempt counts. Times are unix timestamps in seconds."""
    ...
```

- [ ] **Step 2: Implement in DirectBackend**

The API returns uppercase keys (`SUCCESS`, `FAILURE`, `FRAUD`, `ERROR`); normalize to lowercase.

In `src/duocli/backends/direct.py`, add:

```python
def get_auth_stats(self, mintime: int, maxtime: int) -> dict:
    try:
        result = self._admin.get_authentication_attempts(
            mintime=mintime, maxtime=maxtime
        )
    except RuntimeError as exc:
        return {"status": "error", "message": str(exc), "code": 50000}
    return {k.lower(): v for k, v in result.items()}
```

- [ ] **Step 3: Stub in BrokerBackend**

```python
def get_auth_stats(self, mintime: int, maxtime: int) -> dict:
    raise NotImplementedError(_NOT_IMPLEMENTED_MSG)
```

- [ ] **Step 4: Add `auth-stats` CLI command**

Note: `get_authentication_attempts` uses **seconds** (like admin-logs), not milliseconds.

In `src/duocli/cli.py`, add:

```python
@cli.command("auth-stats")
@click.option(
    "--since",
    default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.pass_context
def auth_stats(ctx: click.Context, since: str) -> None:
    """Show aggregate authentication attempt counts."""
    backend = get_backend()
    now_sec = int(time.time())
    delta_sec = _parse_since(since)
    mintime = now_sec - delta_sec
    result = backend.get_auth_stats(mintime=mintime, maxtime=now_sec)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)
```

- [ ] **Step 5: Write tests**

```python
class TestAuthStats:
    def test_auth_stats_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auth-stats", "--help"])
        assert result.exit_code == 0
        assert "--since" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_auth_stats_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_auth_stats.return_value = {
            "success": 100, "failure": 5, "fraud": 0, "error": 1,
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["auth-stats", "--since", "7d"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] == 100
        assert "SUCCESS" not in data  # normalized to lowercase
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/test_cli.py -v -k "auth_stats"`
Expected: All pass

- [ ] **Step 7: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add src/duocli/backends/base.py src/duocli/backends/direct.py src/duocli/backends/broker.py src/duocli/cli.py tests/test_cli.py
git commit -m "Add auth-stats command for aggregate auth attempt counts"
```

---

## Chunk 2: Policies + Update (list-policies, get-policy, update-app)

### Task 4: `list-policies` backend + CLI + tests

**Files:**
- Modify: `src/duocli/backends/base.py`
- Modify: `src/duocli/backends/direct.py`
- Modify: `src/duocli/backends/broker.py`
- Modify: `src/duocli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add `list_policies` to backend ABC**

In `src/duocli/backends/base.py`, add:

```python
@abstractmethod
def list_policies(self) -> list[dict]:
    """List all policies. Returns list of normalized dicts."""
    ...
```

- [ ] **Step 2: Implement in DirectBackend**

`get_policies_v2()` without limit returns full list via iterator. Normalize each policy to stable top-level keys.

In `src/duocli/backends/direct.py`, add:

```python
def list_policies(self) -> list[dict]:
    try:
        results = self._admin.get_policies_v2()
    except RuntimeError as exc:
        return [{"status": "error", "message": str(exc), "code": 50000}]
    return [
        {
            "policy_key": p.get("policy_key", ""),
            "name": p.get("policy_name", ""),
            "enabled": p.get("enabled", False),
        }
        for p in results
    ]
```

- [ ] **Step 3: Stub in BrokerBackend**

```python
def list_policies(self) -> list[dict]:
    raise NotImplementedError(_NOT_IMPLEMENTED_MSG)
```

- [ ] **Step 4: Add `list-policies` CLI command**

In `src/duocli/cli.py`, add:

```python
@cli.command("list-policies")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def list_policies(ctx: click.Context, fields: str | None) -> None:
    """List all Duo policies."""
    backend = get_backend()
    results = backend.list_policies()

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    _output_list(ctx, results, fields)
```

- [ ] **Step 5: Write tests**

```python
class TestListPolicies:
    def test_list_policies_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list-policies", "--help"])
        assert result.exit_code == 0
        assert "--fields" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_list_policies_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.list_policies.return_value = [
            {"policy_key": "PK001", "name": "Default", "enabled": True},
            {"policy_key": "PK002", "name": "Strict", "enabled": False},
        ]
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["list-policies"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2
        assert data[0]["policy_key"] == "PK001"

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_list_policies_fields(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.list_policies.return_value = [
            {"policy_key": "PK001", "name": "Default", "enabled": True},
        ]
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["list-policies", "--fields", "policy_key,name"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert set(data[0].keys()) == {"policy_key", "name"}
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/test_cli.py -v -k "list_policies"`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/duocli/backends/base.py src/duocli/backends/direct.py src/duocli/backends/broker.py src/duocli/cli.py tests/test_cli.py
git commit -m "Add list-policies command for policy discovery"
```

---

### Task 5: `get-policy` backend + CLI + tests

**Files:**
- Modify: `src/duocli/backends/base.py`
- Modify: `src/duocli/backends/direct.py`
- Modify: `src/duocli/backends/broker.py`
- Modify: `src/duocli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add `get_policy` to backend ABC**

```python
@abstractmethod
def get_policy(self, policy_key: str) -> dict:
    """Get a single policy by key. Returns normalized result dict."""
    ...
```

- [ ] **Step 2: Implement in DirectBackend**

```python
def get_policy(self, policy_key: str) -> dict:
    try:
        result = self._admin.get_policy_v2(policy_key)
    except RuntimeError as exc:
        return {"status": "error", "message": str(exc), "code": 50000}
    return result
```

Note: Policy objects have complex nested structure. Return as-is from API since the shape is already agent-readable and the fields vary by policy type.

- [ ] **Step 3: Stub in BrokerBackend**

```python
def get_policy(self, policy_key: str) -> dict:
    raise NotImplementedError(_NOT_IMPLEMENTED_MSG)
```

- [ ] **Step 4: Add `get-policy` CLI command**

```python
@cli.command("get-policy")
@click.option("--id", "policy_id", required=True, help="Policy key to retrieve.")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def get_policy(ctx: click.Context, policy_id: str, fields: str | None) -> None:
    """Get details of a single Duo policy."""
    backend = get_backend()
    result = backend.get_policy(policy_key=policy_id)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if fields:
        field_list = [f.strip() for f in fields.split(",")]
        result = _filter_fields_single(result, field_list)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)
```

- [ ] **Step 5: Write tests**

```python
class TestGetPolicy:
    def test_get_policy_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-policy", "--help"])
        assert result.exit_code == 0
        assert "--id" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_get_policy_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_policy.return_value = {
            "policy_key": "PK001",
            "policy_name": "Default",
            "enabled": True,
            "sections": {},
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["get-policy", "--id", "PK001"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["policy_key"] == "PK001"

    def test_get_policy_missing_id(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-policy"])
        assert result.exit_code != 0
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/test_cli.py -v -k "get_policy"`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/duocli/backends/base.py src/duocli/backends/direct.py src/duocli/backends/broker.py src/duocli/cli.py tests/test_cli.py
git commit -m "Add get-policy command for policy inspection"
```

---

### Task 6: `update-app` backend + CLI + tests

**Files:**
- Modify: `src/duocli/backends/base.py`
- Modify: `src/duocli/backends/direct.py`
- Modify: `src/duocli/backends/broker.py`
- Modify: `src/duocli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add `update_integration` to backend ABC**

```python
@abstractmethod
def update_integration(self, integration_key: str, **kwargs) -> dict:
    """Update an integration. Returns normalized result dict."""
    ...
```

- [ ] **Step 2: Implement in DirectBackend**

```python
def update_integration(self, integration_key: str, **kwargs) -> dict:
    try:
        result = self._admin.update_integration(integration_key, **kwargs)
    except RuntimeError as exc:
        return {"status": "error", "message": str(exc), "code": 50000}
    return {
        "status": "ok",
        "integration_key": result.get("integration_key", ""),
        "name": result.get("name", ""),
        "type": result.get("type", ""),
    }
```

- [ ] **Step 3: Stub in BrokerBackend**

```python
def update_integration(self, integration_key: str, **kwargs) -> dict:
    raise NotImplementedError(_NOT_IMPLEMENTED_MSG)
```

- [ ] **Step 4: Add `_VALID_UPDATE_KEYS` allowlist to cli.py**

Add near the top of `cli.py`, after imports:

```python
_VALID_UPDATE_KEYS = frozenset({
    "name", "visual_style", "greeting", "notes", "enroll_policy",
    "username_normalization_policy", "adminapi_admins", "adminapi_info",
    "adminapi_integrations", "adminapi_read_log", "adminapi_read_resource",
    "adminapi_settings", "adminapi_write_resource", "reset_secret_key",
    "trusted_device_days", "ip_whitelist", "ip_whitelist_enroll_policy",
    "groups_allowed", "self_service_allowed", "sso", "user_access",
})
```

- [ ] **Step 5: Add `update-app` CLI command**

```python
@cli.command("update-app")
@click.option("--ikey", required=True, help="Integration key of the app to update.")
@click.option("--json", "json_payload", required=True, help="JSON payload with update params.")
@click.option("--dry-run", is_flag=True, help="Validate inputs and show what would happen without calling API.")
@click.pass_context
def update_app(ctx: click.Context, ikey: str, json_payload: str, dry_run: bool) -> None:
    """Update a Duo integration."""
    validate_integration_key(ikey)

    try:
        params = json.loads(json_payload)
    except json.JSONDecodeError as exc:
        format_error({"status": "error", "message": f"Invalid JSON: {exc}", "code": 10000})
        sys.exit(1)
    if not isinstance(params, dict) or not params:
        format_error({"status": "error", "message": "JSON payload must be a non-empty object", "code": 10000})
        sys.exit(1)

    unknown_keys = set(params.keys()) - _VALID_UPDATE_KEYS
    if unknown_keys:
        format_error({
            "status": "error",
            "message": f"Unsupported update keys: {', '.join(sorted(unknown_keys))}",
            "code": 10000,
        })
        sys.exit(1)

    if dry_run:
        format_json({"dry_run": True, "action": "update_integration", "params": {"integration_key": ikey, **params}})
        return

    backend = get_backend()
    result = backend.update_integration(integration_key=ikey, **params)

    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    if ctx.obj["human"]:
        format_human_single(result)
    else:
        format_json(result)

    if "reset_secret_key" in params:
        warn_secret_key()
```

- [ ] **Step 6: Write tests**

```python
class TestUpdateApp:
    def test_update_app_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["update-app", "--help"])
        assert result.exit_code == 0
        assert "--ikey" in result.output
        assert "--json" in result.output

    def test_update_app_rejects_bad_ikey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["update-app", "--ikey", "BADKEY", "--json", '{"notes": "x"}'])
        assert result.exit_code != 0

    @patch("duocli.cli.load_dotenv")
    def test_update_app_rejects_empty_payload(self, mock_dotenv):
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", "{}"])
        assert result.exit_code == 1

    @patch("duocli.cli.load_dotenv")
    def test_update_app_rejects_unknown_keys(self, mock_dotenv):
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", '{"bogus_field": "x"}'])
        assert result.exit_code == 1
        assert "bogus_field" in result.output

    @patch("duocli.cli.load_dotenv")
    def test_update_app_dry_run(self, mock_dotenv):
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", '{"notes": "test"}', "--dry-run"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["action"] == "update_integration"
        assert data["params"]["notes"] == "test"

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_update_app_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.update_integration.return_value = {
            "status": "ok",
            "integration_key": "DIAAAAAAAAAAAAAAAAA",
            "name": "Updated",
            "type": "websdk",
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        ikey = "DI" + "A" * 18 + "A"
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", '{"notes": "hello"}'])
        assert result.exit_code == 0
        mock_backend.update_integration.assert_called_once_with(
            integration_key=ikey, notes="hello"
        )

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_update_app_reset_secret_warns(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.update_integration.return_value = {
            "status": "ok",
            "integration_key": "DIAAAAAAAAAAAAAAAAA",
            "name": "Test",
            "type": "websdk",
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        ikey = "DI" + "A" * 18 + "A"
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", '{"reset_secret_key": true}'])
        assert result.exit_code == 0
        assert "secret_key is sensitive" in result.output  # CliRunner merges stdout+stderr
```

- [ ] **Step 7: Run tests**

Run: `uv run pytest tests/test_cli.py -v -k "update_app"`
Expected: All pass

- [ ] **Step 8: Run all tests**

Run: `uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 9: Commit**

```bash
git add src/duocli/backends/base.py src/duocli/backends/direct.py src/duocli/backends/broker.py src/duocli/cli.py tests/test_cli.py
git commit -m "Add update-app command with key allowlist and dry-run"
```

---

## Chunk 3: Security Ops Logs (activity-logs, trust-monitor)

### Task 7: `activity-logs` backend + CLI + tests

**Files:**
- Modify: `src/duocli/backends/base.py`
- Modify: `src/duocli/backends/direct.py`
- Modify: `src/duocli/backends/broker.py`
- Modify: `src/duocli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add `get_activity_logs` to backend ABC**

```python
@abstractmethod
def get_activity_logs(
    self, mintime: int, maxtime: int, limit: int = 500,
) -> list[dict]:
    """Get activity log events. Times are unix timestamps in ms. Limit caps event count."""
    ...
```

- [ ] **Step 2: Implement in DirectBackend**

Backend pages through `next_offset` until limit reached or results exhausted. Normalizes nested API items to flat dicts.

```python
def get_activity_logs(
    self, mintime: int, maxtime: int, limit: int = 500,
) -> list[dict]:
    try:
        events = []
        kwargs = {"mintime": str(mintime), "maxtime": str(maxtime)}
        while len(events) < limit:
            response = self._admin.get_activity_logs(**kwargs)
            items = response.get("items", [])
            if not items:
                break
            for item in items:
                if len(events) >= limit:
                    break
                events.append({
                    "timestamp": item.get("ts", ""),
                    "action": item.get("action", ""),
                    "actor": item.get("actor", {}).get("name", ""),
                    "actor_type": item.get("actor", {}).get("type", ""),
                    "target": item.get("target", {}).get("name", ""),
                    "target_type": item.get("target", {}).get("type", ""),
                    "application": item.get("application", {}).get("name", ""),
                    "ip": item.get("access_device", {}).get("ip", {}).get("address", ""),
                })
            next_offset = response.get("metadata", {}).get("next_offset")
            if not next_offset:
                break
            kwargs["next_offset"] = next_offset
    except RuntimeError as exc:
        return [{"status": "error", "message": str(exc), "code": 50000}]
    return events
```

- [ ] **Step 3: Stub in BrokerBackend**

```python
def get_activity_logs(
    self, mintime: int, maxtime: int, limit: int = 500,
) -> list[dict]:
    raise NotImplementedError(_NOT_IMPLEMENTED_MSG)
```

- [ ] **Step 4: Add `activity-logs` CLI command**

```python
@cli.command("activity-logs")
@click.option(
    "--since", default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.option("--limit", default=500, type=int, help="Max events to return. Default: 500.")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def activity_logs(ctx: click.Context, since: str, limit: int, fields: str | None) -> None:
    """Show activity log events."""
    backend = get_backend()
    now_ms = int(time.time() * 1000)
    delta_ms = _parse_since(since) * 1000
    mintime = now_ms - delta_ms
    results = backend.get_activity_logs(mintime=mintime, maxtime=now_ms, limit=limit)

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    _output_list(ctx, results, fields,
                 default_columns=["timestamp", "action", "actor", "target", "application", "ip"])
```

- [ ] **Step 5: Write tests**

```python
class TestActivityLogs:
    def test_activity_logs_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["activity-logs", "--help"])
        assert result.exit_code == 0
        assert "--since" in result.output
        assert "--limit" in result.output
        assert "--fields" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_activity_logs_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_activity_logs.return_value = [
            {"timestamp": "2026-03-14T00:00:00Z", "action": "create", "actor": "admin",
             "actor_type": "admin", "target": "app", "target_type": "integration",
             "application": "Test", "ip": "1.2.3.4"},
        ]
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["activity-logs", "--since", "1h"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["action"] == "create"

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_activity_logs_passes_limit(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_activity_logs.return_value = []
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["activity-logs", "--since", "1h", "--limit", "10"])
        assert result.exit_code == 0
        mock_backend.get_activity_logs.assert_called_once()
        call_kwargs = mock_backend.get_activity_logs.call_args
        assert call_kwargs.kwargs.get("limit") == 10 or call_kwargs[1].get("limit") == 10
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/test_cli.py -v -k "activity_logs"`
Expected: All pass

- [ ] **Step 7: Commit**

```bash
git add src/duocli/backends/base.py src/duocli/backends/direct.py src/duocli/backends/broker.py src/duocli/cli.py tests/test_cli.py
git commit -m "Add activity-logs command with pagination and limit cap"
```

---

### Task 8: `trust-monitor` backend + CLI + tests

**Files:**
- Modify: `src/duocli/backends/base.py`
- Modify: `src/duocli/backends/direct.py`
- Modify: `src/duocli/backends/broker.py`
- Modify: `src/duocli/cli.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Add `get_trust_monitor_events` to backend ABC**

```python
@abstractmethod
def get_trust_monitor_events(
    self, mintime: int, maxtime: int, limit: int = 500,
) -> list[dict]:
    """Get Trust Monitor events. Times are unix timestamps in ms. Limit caps event count."""
    ...
```

- [ ] **Step 2: Implement in DirectBackend**

Iterates `get_trust_monitor_events_iterator()` and collects events up to the limit.

```python
def get_trust_monitor_events(
    self, mintime: int, maxtime: int, limit: int = 500,
) -> list[dict]:
    try:
        events = []
        for event in self._admin.get_trust_monitor_events_iterator(
            mintime=mintime, maxtime=maxtime,
        ):
            events.append({
                "timestamp": event.get("surfaced_timestamp", ""),
                "type": event.get("type", ""),
                "priority": event.get("priority", ""),
                "description": event.get("triage_event_uri", ""),
                "from_common_netblock": event.get("from_common_netblock", ""),
                "sekey": event.get("sekey", ""),
            })
            if len(events) >= limit:
                break
    except RuntimeError as exc:
        return [{"status": "error", "message": str(exc), "code": 50000}]
    return events
```

- [ ] **Step 3: Stub in BrokerBackend**

```python
def get_trust_monitor_events(
    self, mintime: int, maxtime: int, limit: int = 500,
) -> list[dict]:
    raise NotImplementedError(_NOT_IMPLEMENTED_MSG)
```

- [ ] **Step 4: Add `trust-monitor` CLI command**

```python
@cli.command("trust-monitor")
@click.option(
    "--since", default="24h",
    help="Time window: e.g. 1h, 6h, 7d, 30d. Default: 24h.",
)
@click.option("--limit", default=500, type=int, help="Max events to return. Default: 500.")
@click.option("--fields", default=None, help="Comma-separated list of fields to include in output.")
@click.pass_context
def trust_monitor(ctx: click.Context, since: str, limit: int, fields: str | None) -> None:
    """Show Trust Monitor events."""
    backend = get_backend()
    now_ms = int(time.time() * 1000)
    delta_ms = _parse_since(since) * 1000
    mintime = now_ms - delta_ms
    results = backend.get_trust_monitor_events(mintime=mintime, maxtime=now_ms, limit=limit)

    if _is_error_list(results):
        format_error(results[0])
        sys.exit(2)

    _output_list(ctx, results, fields,
                 default_columns=["timestamp", "type", "priority", "description"])
```

- [ ] **Step 5: Write tests**

```python
class TestTrustMonitor:
    def test_trust_monitor_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["trust-monitor", "--help"])
        assert result.exit_code == 0
        assert "--since" in result.output
        assert "--limit" in result.output
        assert "--fields" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_trust_monitor_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_trust_monitor_events.return_value = [
            {"timestamp": "1710000000000", "type": "auth_anomaly",
             "priority": "high", "description": "https://duo.com/...",
             "from_common_netblock": False, "sekey": "SE123"},
        ]
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["trust-monitor", "--since", "7d"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["type"] == "auth_anomaly"

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_trust_monitor_passes_limit(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_trust_monitor_events.return_value = []
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["trust-monitor", "--since", "1h", "--limit", "10"])
        assert result.exit_code == 0
        call_kwargs = mock_backend.get_trust_monitor_events.call_args
        assert call_kwargs.kwargs.get("limit") == 10 or call_kwargs[1].get("limit") == 10
```

- [ ] **Step 6: Run tests**

Run: `uv run pytest tests/test_cli.py -v -k "trust_monitor"`
Expected: All pass

- [ ] **Step 7: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All pass

- [ ] **Step 8: Commit**

```bash
git add src/duocli/backends/base.py src/duocli/backends/direct.py src/duocli/backends/broker.py src/duocli/cli.py tests/test_cli.py
git commit -m "Add trust-monitor command with cursor abstraction and limit cap"
```

---

## Chunk 4: Verification

### Task 9: End-to-end verification

Run through the verification steps from the spec. These require real Duo credentials.

- [ ] **Step 1: Verify get-app**

```bash
duocli get-app --ikey <real_key>
duocli get-app --ikey <real_key> --fields name,type
duocli get-app --ikey <real_key> --dry-run
```

- [ ] **Step 2: Verify info-summary**

```bash
duocli info-summary
duocli --human info-summary
```

- [ ] **Step 3: Verify list-policies + get-policy**

```bash
duocli list-policies
duocli list-policies --fields policy_key,name
duocli get-policy --id <policy_key_from_list>
```

- [ ] **Step 4: Verify update-app dry-run**

```bash
duocli update-app --ikey <real_key> --json '{"notes": "test"}' --dry-run
duocli update-app --ikey <real_key> --json '{"bogus": "x"}'  # should fail
```

- [ ] **Step 5: Verify activity-logs**

```bash
duocli activity-logs --since 7d
duocli activity-logs --since 7d --limit 5
duocli activity-logs --since 7d --fields timestamp,action,actor
```

- [ ] **Step 6: Verify trust-monitor**

```bash
duocli trust-monitor --since 7d
duocli trust-monitor --since 7d --limit 5
```

- [ ] **Step 7: Verify auth-stats**

```bash
duocli auth-stats --since 30d
duocli --human auth-stats --since 30d
```

- [ ] **Step 8: Verify schema auto-discovery**

```bash
duocli schema get-app
duocli schema update-app
duocli schema trust-monitor
```

- [ ] **Step 9: Run full test suite one final time**

```bash
uv run pytest tests/ -v
```
