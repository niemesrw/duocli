---
name: duo-investigate
description: |
  Investigate why a Duo user is blocked, denied, or failing authentication.
  Use when the user wants to troubleshoot a blocked user, understand which
  policy is denying access, check enrollment status, or trace the effective
  policy for a user+app combination. Trigger on: "user is blocked",
  "why is this user denied", "can't authenticate", "policy is blocking",
  "locked out", "which policy", "investigate user", "troubleshoot auth".
---

# Duo User Investigation

Investigate why a user is blocked, denied, or failing Duo authentication. Walks through user status, auth log analysis, group membership, device enrollment, and effective policy resolution.

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

## Investigation Steps

**Ask the user for the username or user ID before starting.** If they mention an application name, ask for its integration key too (needed for policy resolution).

### Step 1: Look up the user

Check user status, enrollment, and last login. A locked-out, disabled, or not-enrolled user is the most common cause.

```bash
uv run duocli --human get-user --username <username>
# or by ID:
uv run duocli --human get-user --user-id <DUXXXXXXXXXXXXXXXXXX>
```

**Key fields to check:**
- `status`: `active`, `bypass`, `disabled`, `locked out` — if not `active`, this is likely the cause
- `is_enrolled`: `false` means the user has no 2FA devices — they'll be blocked unless the app's enroll_policy is `allow`
- `last_login`: a very old or empty timestamp may indicate a stale account
- `phones_count` / `groups_count`: zero phones = no push/SMS capability

**Save the `user_id` from the output — you'll need it for subsequent steps.**

### Step 2: Check recent auth denials

Pull auth logs filtered to this user and look at the `result` and `reason` fields.

```bash
uv run duocli auth-logs --since 7d --user <username>
```

For JSON output piped through jq to show only failures:
```bash
uv run duocli auth-logs --since 7d --user <username> | \
  jq '[.[] | select(.result != "SUCCESS")]'
```

**Common `reason` values and what they mean:**
| Reason | Meaning |
|--------|---------|
| `user_disabled` | User account is disabled in Duo |
| `locked_out` | Too many failed attempts — account locked |
| `user_not_in_permitted_group` | App restricts access to specific groups and user isn't in one |
| `invalid_device` | Device used doesn't meet policy requirements |
| `no_keys_pressed` | User didn't respond to push/phone call |
| `user_marked_fraud` | User reported the auth as fraudulent |
| `no_activated_device` | User has a phone but hasn't activated Duo Mobile |
| `bypass_user` | User is in bypass status (not blocked, but suspicious if unexpected) |
| `anomalous_push` | Trust Monitor flagged the push as anomalous |

### Step 3: Check group membership

Groups determine which group-level policies apply. A restrictive group policy can block access even if the global policy would allow it.

```bash
uv run duocli --human get-user-groups --user-id <DUXXXXXXXXXXXXXXXXXX>
```

Note the group names — compare them against the app's `groups_allowed` setting (from `get-app`) if the app uses `PERMITTED_GROUPS` access.

### Step 4: Check enrolled devices

If the policy requires a specific factor (e.g., WebAuthn only, push only), but the user doesn't have that device type enrolled, they'll be blocked.

```bash
uv run duocli --human get-user-devices --user-id <DUXXXXXXXXXXXXXXXXXX>
```

**What to look for:**
- `total_devices: 0` — user has nothing enrolled; they can't authenticate
- `phones` with `activated: false` — phone exists but Duo Mobile isn't activated (no push)
- No `webauthn` entries — if policy requires security keys, this is the gap
- Only `tokens` (hardware) — if policy requires push, hardware tokens won't satisfy it

### Step 5: Resolve the effective policy

If you have the application's integration key, calculate what policy Duo actually applies for this user + app combination.

```bash
uv run duocli --human explain-policy --ikey <DIXXXXXXXXXXXXXXXXXX> --user-id <DUXXXXXXXXXXXXXXXXXX>
```

This returns the **resolved policy** — the merged result of global, group, and app-level policy sections. Check:
- `authentication_methods.allowed_auth_list` — which factors are allowed
- `browsers.blocked_browsers_list` — browser restrictions
- Any location or network restrictions

### Step 6 (optional): Check the app configuration

If the denial is app-specific, inspect the app itself:

```bash
uv run duocli --human get-app --ikey <DIXXXXXXXXXXXXXXXXXX>
```

Check `groups_allowed` (is it restricted?), `enroll_policy` (does it allow JIT enrollment?), and `policy_key` (which policy is assigned?).

## Quick Diagnosis Flowchart

```
User blocked?
├── status != active? → Account issue (disabled/locked out)
├── is_enrolled == false? → No 2FA devices enrolled
│   └── enroll_policy != allow? → User can't self-enroll
├── auth-logs show specific reason? → Follow the reason (see table above)
├── user not in groups_allowed? → Group access restriction
├── user has no matching device for policy? → Factor mismatch
│   └── Policy requires webauthn but user has only phone
└── explain-policy shows unexpected restrictions? → Policy misconfiguration
```

## Commands Reference

| Command | Purpose | Key options |
|---------|---------|-------------|
| `get-user` | Look up user status and enrollment | `--username`, `--user-id`, `--fields` |
| `auth-logs` | Auth events filtered by user | `--since`, `--user`, `--fields` |
| `get-user-groups` | Groups a user belongs to | `--user-id`, `--fields` |
| `get-user-devices` | Phones, tokens, WebAuthn credentials | `--user-id` |
| `explain-policy` | Effective policy for user + app | `--ikey`, `--user-id` |
| `get-app` | App configuration and policy assignment | `--ikey`, `--fields` |
| `get-policy` | Full policy details by key | `--id`, `--fields` |
| `list-policies` | All policies in the tenant | `--fields` |

## Output Tips

- Add `--human` before the subcommand for readable tables: `uv run duocli --human get-user ...`
- Use `--fields col1,col2` to narrow output columns
- Default JSON output pipes well into `jq` for filtering
- Chain commands: get user_id from `get-user`, then use it in subsequent commands
