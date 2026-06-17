Before I pull the tenant overview, let me confirm your credentials are loaded:

```bash
echo "IKEY=${DUO_IKEY:-(not set)}  HOST=${DUO_HOST:-(not set)}"
```

If those are not set, let me know where your Duo Admin API credentials are stored — AWS Secrets Manager, 1Password, or a local `.env` file — and I'll load them.

Once credentials are confirmed, I'll run the full health check sequence:

```bash
# Account overview — user/admin/integration counts, edition, telephony credits
uv run duocli --human info-summary

# Auth success/failure rates for the past 7 days
uv run duocli --human auth-stats --since 7d

# All configured policies
uv run duocli --human list-policies

# Trust monitor alerts from the past 7 days
uv run duocli --human trust-monitor --since 7d
```

Here's what each result will tell us:

- **info-summary** — total users, admins, and integrations; your Duo edition (determines available features); telephony credits remaining (if low, SMS/phone-call 2FA may stop working)
- **auth-stats** — aggregate authentication counts; a spike in failures can indicate an attack or misconfiguration
- **list-policies** — all Duo policies and their settings, so we can spot gaps or overly permissive rules
- **trust-monitor** — any anomalous authentication events flagged by Duo in the last week

Are your credentials already set, or do you need help loading them first?
