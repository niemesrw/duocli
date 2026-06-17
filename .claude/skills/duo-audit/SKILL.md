---
name: duo-audit
description: |
  Investigate Duo authentication and admin activity using duocli log commands.
  Use when the user wants to check who logged in, review failed authentications,
  investigate admin changes, check trust monitor alerts, or audit Duo activity
  over a time period. Trigger on: "who logged in", "failed auths", "admin activity",
  "trust monitor", "what happened in Duo", "audit logs", "suspicious activity".
---

# Duo Audit & Investigation

Use duocli's log commands to investigate authentication activity, admin actions, and security events.

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

## Available Log Commands

| Command | What it shows | Time flag | Default window |
|---------|--------------|-----------|----------------|
| `auth-logs` | Every auth attempt (user, result, factor, app, IP) | `--since` | 24h |
| `admin-logs` | Admin actions (who changed what in Duo console) | `--since` | 24h |
| `activity-logs` | Detailed activity events with pagination | `--since`, `--limit` | 24h |
| `trust-monitor` | Trust Monitor security alerts | `--since`, `--limit` | 24h |
| `auth-stats` | Aggregate auth attempt counts by result | `--since` | 24h |

## Common Investigations

### "Who logged in today?"
```bash
uv run duocli --human auth-logs --since 24h
```

### "Show failed authentications this week"
```bash
uv run duocli auth-logs --since 7d --fields timestamp,user,result,factor,ip | \
  python3 -c "import json,sys; [print(json.dumps(r)) for r in json.load(sys.stdin) if r.get('result')=='FAILURE']"
```

### "What did admins change recently?"
```bash
uv run duocli --human admin-logs --since 7d
```

### "Any trust monitor alerts?"
```bash
uv run duocli --human trust-monitor --since 7d
```

### "Auth success rate this month"
```bash
uv run duocli --human auth-stats --since 30d
```

### "Activity for a specific time window"
```bash
uv run duocli --human activity-logs --since 48h --limit 100
```

## Time Windows

The `--since` flag accepts: `30m`, `1h`, `6h`, `24h`, `7d`, `30d`

## Output Tips

- Add `--human` before the subcommand for readable tables: `uv run duocli --human auth-logs`
- Use `--fields col1,col2` to narrow output columns
- Default JSON output pipes well into `jq` for filtering
- Auth logs default columns: timestamp, user, result, factor, application, ip
