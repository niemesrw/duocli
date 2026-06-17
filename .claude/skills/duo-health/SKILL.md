---
name: duo-health
description: |
  Check Duo account health, policies, and statistics using duocli. Use when the
  user wants an overview of their Duo tenant, check policy configuration, see
  account stats, or get a quick health check. Trigger on: "Duo status", "account
  summary", "how many users", "list policies", "check policy", "tenant overview",
  "Duo health check".
---

# Duo Account Health & Policies

Use duocli to check account status, policies, and aggregate statistics.

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

| Command | What it shows |
|---------|--------------|
| `info-summary` | User count, admin count, integration count, edition, telephony credits |
| `list-policies` | All Duo policies with their settings |
| `get-policy` | Details of a specific policy |
| `auth-stats` | Aggregate authentication attempt counts |

## Quick Health Check

Run these in sequence for a full tenant overview:

```bash
# Account overview
uv run duocli --human info-summary

# Auth success/failure rates this week
uv run duocli --human auth-stats --since 7d

# All policies
uv run duocli --human list-policies

# Any trust monitor alerts
uv run duocli --human trust-monitor --since 7d
```

## Common Tasks

### "How many users do we have?"
```bash
uv run duocli --human info-summary
```
Returns: admin_count, user_count, integration_count, edition, telephony_credits_remaining

### "What policies are configured?"
```bash
uv run duocli --human list-policies
uv run duocli list-policies --fields name,policy_key
```

### "Show me a specific policy"
```bash
uv run duocli --human get-policy --id POLICYKEY123
```

### "Are auth attempts healthy?"
```bash
uv run duocli --human auth-stats --since 30d
```

## Interpreting Results

- **edition**: Duo MFA, Duo Access, Duo Beyond, Duo Advantage — determines available features
- **telephony_credits_remaining**: If low, SMS/phone call 2FA may stop working
- **user_pending_deletion_count**: Users scheduled for removal
- **auth-stats**: Compare success vs failure counts — a spike in failures may indicate an attack or misconfiguration
