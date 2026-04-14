# Response: "what did admins change in duo this week"

To look up what admins changed in Duo this week, I would need to query the Duo Admin API for administrator activity logs.

You can do this with the `auth-logs` or admin log commands if available in this CLI, but based on the current command set, here are your options:

## Using duocli

If there is an admin logs command available:

```bash
uv run duocli --human auth-logs
```

However, I don't see a dedicated "admin activity log" command in the current CLI. The Duo Admin API has a separate endpoint for administrator activity (`/admin/v1/logs/administrator`) that is distinct from authentication logs.

## What I'd need to help you

To answer this question fully, I would need to:

1. Know which commands are available — run `uv run duocli --help` to see the full list
2. If an admin log command exists, know what date range to query (this week = roughly the last 7 days)

## If the command doesn't exist yet

You could add it. The Duo Admin API endpoint for administrator activity logs is:

```
GET /admin/v1/logs/administrator
```

Parameters include `mintime` (Unix timestamp) to filter by date range.

To get this week's changes, you'd pass a `mintime` of 7 days ago as a Unix timestamp:

```python
import time
mintime = int(time.time()) - (7 * 24 * 60 * 60)
```

## Alternative: Duo Admin Panel

If you need this immediately without code changes, log into your Duo Admin Panel at `https://admin.duosecurity.com` and navigate to **Reports > Administrator Actions** to see a UI-based view of recent admin changes.

---

If you'd like, I can help you scaffold a new `admin-logs` command using the `/new-command` skill, or I can walk you through the API call manually.
