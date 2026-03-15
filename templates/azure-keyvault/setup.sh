#!/usr/bin/env bash
set -euo pipefail

# Deploy the Key Vault and Duo secret using Bicep.
#
# Prerequisites:
#   - az cli installed and logged in (az login)
#   - A resource group already exists
#
# Usage:
#   ./setup.sh <resource-group> <parameters-file>
#
# Example:
#   cp parameters.example.json parameters.json  # edit with real values
#   ./setup.sh rg-duocli parameters.json

RESOURCE_GROUP="${1:?Usage: ./setup.sh <resource-group> <parameters-file>}"
PARAMETERS_FILE="${2:?Usage: ./setup.sh <resource-group> <parameters-file>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$PARAMETERS_FILE" ]; then
  echo "Error: parameters file not found: $PARAMETERS_FILE" >&2
  exit 1
fi

echo "Deploying Key Vault to resource group: $RESOURCE_GROUP"

az deployment group create \
  --resource-group "$RESOURCE_GROUP" \
  --template-file "$SCRIPT_DIR/main.bicep" \
  --parameters "@$PARAMETERS_FILE" \
  --name "duocli-keyvault-$(date +%Y%m%d%H%M%S)"

echo ""
echo "Deployment complete. Verify with:"
echo "  az keyvault show --name <vault-name> --resource-group $RESOURCE_GROUP"
