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
uv run duo --human info-summary

# Auth success/failure rates this week
uv run duo --human auth-stats --since 7d

# All policies
uv run duo --human list-policies

# Any trust monitor alerts
uv run duo --human trust-monitor --since 7d
```

## Common Tasks

### "How many users do we have?"
```bash
uv run duo --human info-summary
```
Returns: admin_count, user_count, integration_count, edition, telephony_credits_remaining

### "What policies are configured?"
```bash
uv run duo --human list-policies
uv run duo list-policies --fields name,policy_key
```

### "Show me a specific policy"
```bash
uv run duo --human get-policy --id POLICYKEY123
```

### "Are auth attempts healthy?"
```bash
uv run duo --human auth-stats --since 30d
```

## Interpreting Results

- **edition**: Duo MFA, Duo Access, Duo Beyond, Duo Advantage — determines available features
- **telephony_credits_remaining**: If low, SMS/phone call 2FA may stop working
- **user_pending_deletion_count**: Users scheduled for removal
- **auth-stats**: Compare success vs failure counts — a spike in failures may indicate an attack or misconfiguration
