#!/usr/bin/env bash
set -euo pipefail

# Fetch Duo credentials from Azure Key Vault and run duocli.
#
# Prerequisites:
#   - az cli installed and logged in (az login)
#   - Key Vault Secrets User role on the vault
#   - jq installed
#
# Configuration (env vars):
#   DUOCLI_VAULT_NAME   - Name of the Key Vault (required)
#   DUOCLI_SECRET_NAME  - Name of the secret (default: duo-admin-api)
#
# Usage:
#   export DUOCLI_VAULT_NAME=duocli-secrets
#   ./wrapper.sh list-apps --human
#   ./wrapper.sh create-app --name "My App" --type websdk

VAULT_NAME="${DUOCLI_VAULT_NAME:?Set DUOCLI_VAULT_NAME to your Key Vault name}"
SECRET_NAME="${DUOCLI_SECRET_NAME:-duo-admin-api}"

for cmd in az jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: $cmd is required but not found in PATH" >&2
    exit 1
  fi
done

secret_json=$(az keyvault secret show \
  --vault-name "$VAULT_NAME" \
  --name "$SECRET_NAME" \
  --query value \
  --output tsv)

export DUO_IKEY
export DUO_SKEY
export DUO_HOST
DUO_IKEY=$(echo "$secret_json" | jq -re '.DUO_IKEY')
DUO_SKEY=$(echo "$secret_json" | jq -re '.DUO_SKEY')
DUO_HOST=$(echo "$secret_json" | jq -re '.DUO_HOST')

exec duocli "$@"
