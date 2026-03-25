---
name: duo-apps
description: |
  Manage Duo integrations (applications) using duocli. Use when the user wants
  to create, list, inspect, update, or delete Duo apps/integrations. Trigger on:
  "create an app", "list integrations", "delete app", "update app settings",
  "what apps do we have", "add a new Duo integration", "change app name".
---

# Duo App Management

Use duocli to manage Duo integrations (applications).

## Commands

| Command | Purpose | Key options |
|---------|---------|-------------|
| `list-apps` | List all integrations | `--fields` |
| `get-app` | Get details of one app | `--ikey`, `--fields` |
| `create-app` | Create a new integration | `--name`, `--type`, `--json`, `--dry-run` |
| `create-oidc-app` | Create an OIDC/SSO app with defaults | `--name`, `--redirect-uri`, `--grant-type`, `--user-access`, `--dry-run` |
| `update-app` | Update an integration | `--ikey`, `--json`, `--dry-run` |
| `delete-app` | Delete an integration | `--ikey`, `--dry-run` |

## Common Tasks

### List all apps
```bash
uv run duo --human list-apps
uv run duo list-apps --fields name,type,integration_key
```

### Inspect a specific app
```bash
uv run duo --human get-app --ikey DIXXXXXXXXXXXXXXXXXX
```

### Create a new app

**Simple types** (websdk, adminapi):
```bash
uv run duo create-app --name "My App" --type websdk
uv run duo create-app --name "My App" --type websdk --dry-run
```

**OIDC / SSO apps** — use the dedicated `create-oidc-app` command:

```bash
# Basic — authorization_code grant with openid/email/profile scopes
uv run duo create-oidc-app --name "My App" --redirect-uri https://myapp.example.com/callback

# M2M + interactive — multiple grant types, restricted access
uv run duo create-oidc-app --name "Agent App" --redirect-uri https://agent.example.com/cb \
    --grant-type authorization_code --grant-type client_credentials \
    --user-access PERMITTED_GROUPS

# Dry-run first
uv run duo create-oidc-app --name "My App" --redirect-uri https://myapp.example.com/callback --dry-run
```

Defaults: `authorization_code` grant, `openid`/`email`/`profile` scopes with common IdP→claim mappings (`mail`→`email`, `displayname`→`name`), `ALL_USERS` access, JIT provisioning. PKCE is enforced by Duo at the policy level.

**Advanced: raw JSON via `create-app --json`** — for full control over the `sso.oidc_config` payload. Note Duo API quirks: `grant_types` is a dict, `scopes` is a list of objects, and `email`/`profile` scopes require `idp_attribute_claim_mapping`.

**OAuth 2.1 / OIDC** (`sso-oauth-server`) and **MCP** (`sso-oauth-server-mcp`) are newer app types with mandatory PKCE, custom scopes, and M2M support. Create the shell via `create-app --type sso-oauth-server`, then configure grant types, redirect URIs, and scopes in the Duo Admin Panel (not yet API-manageable).

**After creation** — derive the issuer URL from the integration key:
```
duo_issuer_url = https://<sso-host>/oidc/<integration_key>
# e.g. https://sso-e8704f1a.sso.duosecurity.com/oidc/DI6PKF2255QAV2PQEM3A
```
(The SSO host is account-wide — check an existing app or the Duo Admin Panel to find yours.)

### Update an app
```bash
# Change name
uv run duo update-app --ikey DIXXXXXXXXXXXXXXXXXX --json '{"name": "New Name"}'

# Multiple fields
uv run duo update-app --ikey DIXXXXXXXXXXXXXXXXXX --json '{"name": "New Name", "notes": "Updated"}'

# Dry-run to see what would change
uv run duo update-app --ikey DIXXXXXXXXXXXXXXXXXX --json '{"name": "New Name"}' --dry-run
```

### Delete an app
```bash
# Always dry-run first for destructive operations
uv run duo delete-app --ikey DIXXXXXXXXXXXXXXXXXX --dry-run
uv run duo delete-app --ikey DIXXXXXXXXXXXXXXXXXX
```

## Allowed Update Keys

Only these fields can be passed to `update-app`:
name, visual_style, greeting, notes, enroll_policy, username_normalization_policy,
adminapi_admins, adminapi_info, adminapi_integrations, adminapi_read_log,
adminapi_read_resource, adminapi_settings, adminapi_write_resource,
reset_secret_key, trusted_device_days, ip_whitelist, ip_whitelist_enroll_policy,
groups_allowed, self_service_allowed, sso, user_access

## Safety

- Use `--dry-run` before any create/update/delete to preview the action
- Integration keys match format `DI` + 18-20 alphanumeric characters
- `delete-app` is irreversible — verify the ikey first with `get-app`
