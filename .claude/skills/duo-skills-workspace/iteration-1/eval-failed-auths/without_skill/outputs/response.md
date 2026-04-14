# Response: Show Failed Duo Authentications from Last 7 Days

To retrieve failed Duo authentications from the last 7 days, you can use the `auth-logs` command in duocli. Here's how:

## Using duocli

```bash
uv run duocli auth-logs --days 7 --result deny
```

Or with human-readable output:

```bash
uv run duocli --human auth-logs --days 7 --result deny
```

## What to expect

The command will query the Duo Admin API for authentication logs and filter for denied/failed authentications. The output will include fields like:

- `timestamp` — when the authentication attempt occurred
- `user` — the username that attempted authentication
- `result` — the result (e.g., `DENY`, `FRAUD`)
- `reason` — why it failed (e.g., `user_disabled`, `user_cancelled`, `deny_unenrolled_user`)
- `application` — which application was being accessed
- `factor` — the authentication factor used (or attempted)
- `ip` — the IP address of the request

## If you need more filtering

To see only specific failure reasons:

```bash
uv run duocli auth-logs --days 7 --result deny --reason user_cancelled
```

## Prerequisites

Make sure your credentials are set:

```bash
export DUO_IKEY=your_integration_key
export DUO_SKEY=your_secret_key
export DUO_HOST=api-XXXXXXXX.duosecurity.com
```

Or place them in a `.env` file (use `.env.example` as a template — never edit `.env` directly).

## Notes

- The Duo Admin API returns logs in pages; duocli handles pagination automatically.
- Log retention in Duo is typically 180 days, so 7 days is well within range.
- If you see exit code `2`, there was an API error — check your credentials and host.
