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
uv run duo --human auth-logs --since 24h
```

### "Show failed authentications this week"
```bash
uv run duo auth-logs --since 7d --fields timestamp,user,result,factor,ip | \
  python3 -c "import json,sys; [print(json.dumps(r)) for r in json.load(sys.stdin) if r.get('result')=='FAILURE']"
```

### "What did admins change recently?"
```bash
uv run duo --human admin-logs --since 7d
```

### "Any trust monitor alerts?"
```bash
uv run duo --human trust-monitor --since 7d
```

### "Auth success rate this month"
```bash
uv run duo --human auth-stats --since 30d
```

### "Activity for a specific time window"
```bash
uv run duo --human activity-logs --since 48h --limit 100
```

## Time Windows

The `--since` flag accepts: `30m`, `1h`, `6h`, `24h`, `7d`, `30d`

## Output Tips

- Add `--human` before the subcommand for readable tables: `uv run duo --human auth-logs`
- Use `--fields col1,col2` to narrow output columns
- Default JSON output pipes well into `jq` for filtering
- Auth logs default columns: timestamp, user, result, factor, application, ip
