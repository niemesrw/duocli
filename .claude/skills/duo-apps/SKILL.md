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
```bash
# Simple
uv run duo create-app --name "My App" --type websdk

# With extra params via JSON
uv run duo create-app --json '{"name": "My App", "type": "websdk", "notes": "Production SSO"}'

# Dry-run first
uv run duo create-app --name "My App" --type websdk --dry-run
```

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
