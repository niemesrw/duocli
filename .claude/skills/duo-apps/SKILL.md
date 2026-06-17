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

## Credentials

**Credentials first — do not show any runnable duocli commands until this step is complete.**

Check whether the required env vars are already set:

```bash
echo "IKEY=${DUO_IKEY:+(set)}${DUO_IKEY:-(not set)}  SKEY=${DUO_SKEY:+(set)}${DUO_SKEY:-(not set)}  HOST=${DUO_HOST:-(not set)}"
```

If any value is `(not set)`, stop and ask the user: **"Where are your Duo Admin API credentials stored?"** Do not proceed to the task or show commands until credentials are loaded. Common options:

### AWS Secrets Manager

Ask for the AWS profile and secret name/ARN, then load:

```bash
SECRET=$(aws secretsmanager get-secret-value \
  --secret-id <secret-name-or-arn> \
  --profile <aws-profile> \
  --query SecretString --output text)
export DUO_IKEY=$(echo "$SECRET" | jq -r '.DUO_IKEY // .ikey')
export DUO_SKEY=$(echo "$SECRET" | jq -r '.DUO_SKEY // .skey')
export DUO_HOST=$(echo "$SECRET" | jq -r '.DUO_HOST // .host')
```

### 1Password CLI

Ask for the vault, item name, and field names, then load:

```bash
export DUO_IKEY=$(op read "op://<vault>/<item>/DUO_IKEY")
export DUO_SKEY=$(op read "op://<vault>/<item>/DUO_SKEY")
export DUO_HOST=$(op read "op://<vault>/<item>/DUO_HOST")
```

### Environment / .env file

Remind the user to set `DUO_IKEY`, `DUO_SKEY`, and `DUO_HOST` — see `.env.example` for the expected format. Never edit `.env` directly through Claude (the hook blocks it).

After loading, confirm with a quick `echo $DUO_HOST` before proceeding.

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
uv run duocli --human list-apps
uv run duocli list-apps --fields name,type,integration_key
```

### Inspect a specific app
```bash
uv run duocli --human get-app --ikey DIXXXXXXXXXXXXXXXXXX
```

### Create a new app

**Simple types** (websdk, adminapi):
```bash
uv run duocli create-app --name "My App" --type websdk
uv run duocli create-app --name "My App" --type websdk --dry-run
```

**OIDC / SSO apps** — use the dedicated `create-oidc-app` command:

```bash
# Basic — authorization_code grant with openid/email/profile scopes
uv run duocli create-oidc-app --name "My App" --redirect-uri https://myapp.example.com/callback

# M2M + interactive — multiple grant types, restricted access
uv run duocli create-oidc-app --name "Agent App" --redirect-uri https://agent.example.com/cb \
    --grant-type authorization_code --grant-type client_credentials \
    --user-access PERMITTED_GROUPS

# Dry-run first
uv run duocli create-oidc-app --name "My App" --redirect-uri https://myapp.example.com/callback --dry-run
```

Defaults: `authorization_code` grant, `openid`/`email`/`profile` scopes with common IdP→claim mappings (`mail`→`email`, `displayname`→`name`), `ALL_USERS` access, JIT provisioning. PKCE is enforced by Duo at the policy level.

**Advanced: raw JSON via `create-app --json`** — for full control over the `sso.oidc_config` payload. Note Duo API quirks: `grant_types` is a dict, `scopes` is a list of objects, and `email`/`profile` scopes require `idp_attribute_claim_mapping`.

**OAuth 2.1 / OIDC** (`sso-oauth-server`) and **MCP** (`sso-oauth-server-mcp`) are newer app types with mandatory PKCE, custom scopes, and M2M support. Create the shell via `create-app --type sso-oauth-server`, then configure grant types, redirect URIs, and scopes in the Duo Admin Panel (not yet API-manageable).

**After creation** — derive the issuer URL from the integration key:
```
duo_issuer_url = https://<sso-host>/oidc/<integration_key>
# e.g. https://sso-XXXXXXXX.sso.duosecurity.com/oidc/DIXXXXXXXXXXXXXXXXXX
```
(The SSO host is account-wide — check an existing app or the Duo Admin Panel to find yours.)

### Update an app
```bash
# Change name
uv run duocli update-app --ikey DIXXXXXXXXXXXXXXXXXX --json '{"name": "New Name"}'

# Multiple fields
uv run duocli update-app --ikey DIXXXXXXXXXXXXXXXXXX --json '{"name": "New Name", "notes": "Updated"}'

# Dry-run to see what would change
uv run duocli update-app --ikey DIXXXXXXXXXXXXXXXXXX --json '{"name": "New Name"}' --dry-run
```

### Delete an app
```bash
# Always dry-run first for destructive operations
uv run duocli delete-app --ikey DIXXXXXXXXXXXXXXXXXX --dry-run
uv run duocli delete-app --ikey DIXXXXXXXXXXXXXXXXXX
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
