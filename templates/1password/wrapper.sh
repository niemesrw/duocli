#!/usr/bin/env bash
set -euo pipefail

# Fetch Duo credentials from 1Password and run duocli.
#
# Prerequisites:
#   - op cli installed and signed in (or biometric unlock enabled)
#   - Access to the duocli vault
#
# Configuration (env vars):
#   DUOCLI_OP_VAULT  - 1Password vault name (default: duocli)
#   DUOCLI_OP_ITEM   - Item title (default: Duo Admin API)
#
# Usage:
#   export DUOCLI_OP_VAULT=duocli
#   ./wrapper.sh list-apps --human
#   ./wrapper.sh create-app --name "My App" --type websdk

VAULT="${DUOCLI_OP_VAULT:-duocli}"
ITEM="${DUOCLI_OP_ITEM:-Duo Admin API}"

if ! command -v op &>/dev/null; then
  echo "Error: op cli is required but not found in PATH" >&2
  exit 1
fi

export DUO_IKEY
export DUO_SKEY
export DUO_HOST
DUO_IKEY=$(op read "op://$VAULT/$ITEM/DUO_IKEY")
DUO_SKEY=$(op read "op://$VAULT/$ITEM/DUO_SKEY")
DUO_HOST=$(op read "op://$VAULT/$ITEM/DUO_HOST")

exec duocli "$@"
