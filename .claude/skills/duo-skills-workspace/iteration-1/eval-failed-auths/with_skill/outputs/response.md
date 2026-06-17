# Claude Response: Show Failed Duo Authentications (Last 7 Days)

## Credential Check

Before pulling logs, let me verify your Duo Admin API credentials are set:

```bash
echo "IKEY=${DUO_IKEY:-(not set)}  HOST=${DUO_HOST:-(not set)}"
```

If those are not set, where are your Duo Admin API credentials stored? Common options:
- **AWS Secrets Manager** — I'll need your AWS profile and secret name/ARN
- **1Password CLI** — I'll need vault, item name, and field names
- **Environment / .env file** — set `DUO_IKEY`, `DUO_SKEY`, and `DUO_HOST` per `.env.example`

---

Assuming credentials are already set, here is the command to pull all failed authentications from the last 7 days:

```bash
uv run duocli auth-logs --since 7d --fields timestamp,user,result,factor,ip | \
  python3 -c "import json,sys; [print(json.dumps(r)) for r in json.load(sys.stdin) if r.get('result')=='FAILURE']"
```

This fetches all auth log entries from the past 7 days and filters to only those where `result == FAILURE`.

**For a human-readable table of all auth events (then visually filter):**

```bash
uv run duocli --human auth-logs --since 7d
```

**To get a quick summary of auth counts by result (success vs. failure) for the week:**

```bash
uv run duocli --human auth-stats --since 7d
```

The `auth-stats` command is the fastest way to see the total failure count. The filtered `auth-logs` pipeline gives you the per-event detail (who failed, from which IP, using which factor, at what time).
