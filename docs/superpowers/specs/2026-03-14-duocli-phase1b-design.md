# duocli Phase 1b — Provisioning + Security Ops Commands

## Context

Phase 1 delivered core integration CRUD (`create-app`, `delete-app`, `list-apps`) plus `auth-logs`, `admin-logs`, and agent DX features (validation, `--dry-run`, `schema`, `--fields`, `--json`). This phase adds commands needed for two use cases:

1. **Agent automation** — an LLM agent provisioning Duo integrations end-to-end (create → inspect → configure → verify)
2. **Security operations** — querying activity, anomaly detection, and auth statistics

Output standard for this phase remains **agent-friendly normalized JSON**, not raw API passthrough by default. Existing commands already return stable, flattened shapes where that improves usability for shell automation and LLM agents. New commands should follow that pattern unless there is a strong reason to preserve the raw Duo object unchanged.

## Implementation Order

Approach B: interleave by complexity. Easy reads first, then mutations, then complex log streams.

---

## New Commands

### Read-only: `get-app`

```bash
duocli get-app --ikey DIXXXXXXXXXXXXXXXXXX
duocli get-app --ikey DIXXXXXXXXXXXXXXXXXX --fields name,type,policy_key
```

- Calls `admin.get_integration(integration_key)`
- Returns a normalized single integration object with stable top-level keys for common fields; may include additional pass-through fields where useful, but should not expose a purely raw Duo response shape
- Input validation: `validate_integration_key()` on ikey
- Supports `--fields`, `--dry-run`, `--human`
- `--human` uses `format_human_single()`

Backend:
```python
# base.py
@abstractmethod
def get_integration(self, integration_key: str) -> dict: ...
```

### Read-only: `info-summary`

```bash
duocli info-summary
```

- Calls `admin.get_info_summary()`
- Returns a stable normalized summary object (keys like `integration_count`, `user_count`, `admin_count`, etc.); if the Duo API already matches the desired shape, it can be forwarded unchanged
- No arguments. No `--fields` (fixed small output).
- `--human` uses `format_human_single()`

Backend:
```python
@abstractmethod
def get_info_summary(self) -> dict: ...
```

### Read-only: `list-policies`

```bash
duocli list-policies
duocli list-policies --fields policy_key,name
```

- Calls `admin.get_policies_v2()`
- Returns a normalized list of policy objects with stable top-level keys appropriate for filtering and human output
- Supports `--fields`, `--human`
- Uses `_output_list()` helper

Backend:
```python
@abstractmethod
def list_policies(self) -> list[dict]: ...
```

### Read-only: `get-policy`

```bash
duocli get-policy --id POLICY_KEY
```

- Calls `admin.get_policy_v2(policy_key)`
- Returns a normalized single policy object. Preserve useful policy detail, but shape it for agent readability instead of treating the raw response as the contract
- No client-side validation on policy ID format (API rejects bad values)
- Supports `--fields`, `--human`
- `--human` uses `format_human_single()`

Backend:
```python
@abstractmethod
def get_policy(self, policy_key: str) -> dict: ...
```

### Mutation: `update-app`

```bash
duocli update-app --ikey DIXXXXXXXXXXXXXXXXXX --json '{"notes": "Managed by automation"}'
duocli update-app --ikey DIXXXXXXXXXXXXXXXXXX --json '{"policy_key": "PK..."}' --dry-run
```

- Calls `admin.update_integration(integration_key, **params)`
- `--json` is required (no individual flags — too many optional properties)
- Input validation: `validate_integration_key()` on ikey, JSON parsing on payload, payload must be a non-empty object
- Validate update keys against the supported `duo_client.Admin.update_integration()` parameter set before calling the API. Unknown keys should fail as user input errors rather than surfacing raw `TypeError` traces.
- Supports `--dry-run` — validates inputs, prints `{"dry_run": true, "action": "update_integration", "params": {...}}`
- Returns the updated integration object on success
- If `reset_secret_key` is present, treat the response as sensitive output: emit the same stderr warning used by `create-app`
- `--human` uses `format_human_single()`

Backend:
```python
@abstractmethod
def update_integration(self, integration_key: str, **kwargs) -> dict: ...
```

### Security ops: `activity-logs`

```bash
duocli activity-logs --since 24h
duocli activity-logs --since 7d --fields timestamp,action,actor
```

- Calls `admin.get_activity_logs(mintime, maxtime)`
- Times are in **milliseconds** (same as `auth-logs`; note: `admin-logs` uses seconds per Duo API convention)
- Same `--since` pattern as `auth-logs`
- API returns `{"items": [...], "metadata": {...}}`; backend must page through `metadata.next_offset` until the configured cap is reached or results are exhausted
- Default cap: 500 events
- Add `--limit` to override the cap explicitly when needed
- Backend returns normalized flat event records rather than nested raw API items
- Supports `--fields`, `--human`
- Uses `_output_list()` helper
- Default human columns: `timestamp`, `action`, `actor`, `target`, `application`, `ip`

Backend:
```python
@abstractmethod
def get_activity_logs(self, mintime: int, maxtime: int) -> list[dict]: ...
```

### Security ops: `trust-monitor`

```bash
duocli trust-monitor --since 1h
duocli trust-monitor --since 7d --fields type,priority,description
```

- The Duo API uses cursor-based pagination (`get_trust_monitor_events_iterator`)
- Times are in **milliseconds** (same as `auth-logs` and `activity-logs`)
- CLI abstracts cursor away: accepts `--since`, converts to mintime, iterates cursor internally, and returns a normalized flat list
- Default cap: 500 events
- Add `--limit` to override the cap explicitly when needed
- Supports `--fields`, `--human`
- Default human columns: `timestamp`, `type`, `priority`, `description`
- Uses `_output_list()` helper

Backend:
```python
@abstractmethod
def get_trust_monitor_events(self, mintime: int, maxtime: int) -> list[dict]: ...
```

DirectBackend iterates `get_trust_monitor_events_iterator()` internally and collects all events.

### Security ops: `auth-stats`

```bash
duocli auth-stats --since 24h
```

- Calls `admin.get_authentication_attempts(mintime, maxtime)`
- API returns uppercase keys (`SUCCESS`, `FAILURE`, `FRAUD`, `ERROR`); backend normalizes to lowercase: `{"success": N, "failure": N, "fraud": N, "error": N}`
- No `--fields` (only 4 fixed fields)
- `--human` uses `format_human_single()`
- Same `--since` pattern

Backend:
```python
@abstractmethod
def get_auth_stats(self, mintime: int, maxtime: int) -> dict: ...
```

---

## Implementation Details

### Backend changes

All new methods added to `DuoBackend` ABC in `base.py`, implemented in `direct.py`, stubbed with `NotImplementedError` in `broker.py`.

Error handling follows existing pattern: catch `RuntimeError` from `duo_client`, return `{"status": "error", "message": ..., "code": 50000}`.
For client-side validation failures and unsupported `update-app` keys, return the existing user/input error shape and exit with code `1`.

### CLI changes

All new commands in `cli.py`. Follow existing patterns:
- List commands use `_output_list()` helper
- Single-item commands use `format_human_single()` for `--human`
- Error checking uses `_is_error_list()` for list returns, `.get("status") == "error"` for dict returns
- `--dry-run` on `update-app` follows same pattern as `create-app`/`delete-app`
- `schema` command auto-discovers new commands (no changes needed)
- Add a small single-item field filtering helper for commands like `get-app` and `get-policy`; existing list-only field filtering is not sufficient on its own

### Validation

- `get-app`, `update-app`, `delete-app` all validate ikey via `validate_integration_key()`
- `get-policy` does not validate policy key format (pass-through to API)
- `update-app --json` validates JSON is a non-empty dict and rejects unsupported keys before calling the backend

### Output

- Existing `output.py` formatters are mostly sufficient, but single-item field filtering support is needed in the CLI layer
- `info-summary` and `auth-stats` use `format_human_single()` which skips the `status` key
- For new log-style commands, normalized flat keys are the contract so `--fields` and `--human` remain predictable for agent callers

---

## Testing

For each new command:
- `--help` shows correct flags
- Missing required args fail with exit code != 0
- `schema <command>` returns correct param descriptions
- Mock backend tests for success and error paths
- `--dry-run` tests where applicable (update-app)
- `--fields` tests where applicable (get-app, get-policy, list-policies, activity-logs, trust-monitor)
- Input validation tests (get-app, update-app reject bad ikeys)
- `update-app` rejects empty payloads and unsupported keys with exit code `1`
- `update-app --json '{"reset_secret_key": true}'` emits the sensitive output warning on stderr
- `activity-logs` and `trust-monitor` enforce the default cap and honor explicit `--limit`

---

## Verification

1. `duocli get-app --ikey <real_key>` → full integration JSON
2. `duocli info-summary` → counts
3. `duocli list-policies` → policy list
4. `duocli get-policy --id <policy_key>` → policy config
5. `duocli update-app --ikey <key> --json '{"notes": "test"}' --dry-run` → dry-run JSON
6. `duocli activity-logs --since 7d` → normalized activity events up to the default cap
7. `duocli trust-monitor --since 7d` → normalized trust monitor events up to the default cap
8. `duocli auth-stats --since 30d` → aggregate counts

---

## Out of Scope

- Policy CRUD mutations (create, update, delete) — high blast radius
- User management (CRUD, enrollment, bypass codes) — separate use case
- Telephony/offline logs — not prioritized
- Raw cursor / next_offset exposure — add later if needed
- Broker mode implementations — Phase 2
