#!/usr/bin/env bash
set -euo pipefail

# Create a 1Password vault and item for Duo Admin API credentials.
#
# Prerequisites:
#   - op cli installed and signed in (op signin)
#   - 1Password Teams or Business account (for audit logs)
#
# Usage:
#   ./setup.sh
#
# You'll be prompted for each credential value.

VAULT_NAME="${DUOCLI_OP_VAULT:-duocli}"
ITEM_NAME="${DUOCLI_OP_ITEM:-Duo Admin API}"

if ! command -v op &>/dev/null; then
  echo "Error: op cli is required but not found in PATH" >&2
  echo "Install: https://developer.1password.com/docs/cli/get-started/" >&2
  exit 1
fi

# Check if signed in
if ! op account list &>/dev/null 2>&1; then
  echo "Error: not signed in to 1Password. Run: op signin" >&2
  exit 1
fi

# Create vault if it doesn't exist
if ! op vault get "$VAULT_NAME" &>/dev/null 2>&1; then
  echo "Creating vault: $VAULT_NAME"
  op vault create "$VAULT_NAME" --description "Duo Security CLI credentials"
else
  echo "Vault already exists: $VAULT_NAME"
fi

# Create the item
echo ""
echo "Enter Duo Admin API credentials:"
read -rp "  DUO_IKEY: " DUO_IKEY
read -rsp "  DUO_SKEY: " DUO_SKEY
echo ""
read -rp "  DUO_HOST: " DUO_HOST

op item create \
  --category=login \
  --title="$ITEM_NAME" \
  --vault="$VAULT_NAME" \
  "DUO_IKEY=$DUO_IKEY" \
  "DUO_SKEY[password]=$DUO_SKEY" \
  "DUO_HOST=$DUO_HOST"

echo ""
echo "Item created in vault '$VAULT_NAME'."
echo ""
echo "To use with duocli:"
echo "  export DUOCLI_OP_VAULT=$VAULT_NAME"
echo "  ./wrapper.sh list-apps --human"
