# 1Password — duocli secret template

Store Duo Admin API credentials in 1Password. Every secret access triggers biometric/password authentication, and Teams/Business plans log all item access in the activity feed.

## Prerequisites

- [1Password CLI](https://developer.1password.com/docs/cli/get-started/) (`op`) installed
- 1Password account (Teams or Business plan recommended for audit logs)
- Signed in: `op signin` or biometric unlock enabled

## Setup

```bash
chmod +x setup.sh
./setup.sh
```

This creates a `duocli` vault with a "Duo Admin API" item containing your three credentials. You'll be prompted for each value.

## Usage

```bash
chmod +x wrapper.sh

./wrapper.sh list-apps
./wrapper.sh --human info-summary
./wrapper.sh create-app --name "My App" --type websdk
```

The wrapper reads credentials from 1Password via `op read`, exports them as env vars, and execs duocli. If biometric unlock is enabled, you'll authenticate with Touch ID.

## What gets audited

On 1Password Teams/Business plans, the activity log records:

- **Who** — the team member
- **When** — timestamp
- **What** — item title and vault
- **Action** — "used item" / "accessed item"

View activity: 1Password web app → Activity Log, or via the Events API.

## Vault access

Control who can access the duocli vault through 1Password's vault sharing:

1. Open the `duocli` vault in 1Password
2. Share with specific team members or groups
3. Set permissions (view items, edit items, manage vault)

## Rotating credentials

Update the item in 1Password (GUI or CLI):

```bash
op item edit "Duo Admin API" \
  --vault duocli \
  "DUO_SKEY[password]=new-secret-key"
```

Previous versions are retained in 1Password's item history.

## Alternative: op run

Instead of the wrapper, you can use `op run` directly with an env file:

```bash
# duocli.env
DUO_IKEY=op://duocli/Duo Admin API/DUO_IKEY
DUO_SKEY=op://duocli/Duo Admin API/DUO_SKEY
DUO_HOST=op://duocli/Duo Admin API/DUO_HOST
```

```bash
op run --env-file=duocli.env -- duocli list-apps
```
