#!/usr/bin/env bash
set -euo pipefail

# Fetch Duo credentials from AWS Secrets Manager and run duocli.
#
# Prerequisites:
#   - aws cli installed and authenticated (aws sso login, etc.)
#   - Permission to call secretsmanager:GetSecretValue
#   - jq installed
#
# Configuration (env vars):
#   DUOCLI_SECRET_ID  - Secret name or ARN (default: duocli/duo-admin-api)
#   AWS_PROFILE       - AWS CLI profile to use (optional)
#   AWS_REGION        - AWS region (optional, defaults to CLI config)
#
# Usage:
#   export AWS_PROFILE=my-profile
#   ./wrapper.sh list-apps --human
#   ./wrapper.sh create-app --name "My App" --type websdk

SECRET_ID="${DUOCLI_SECRET_ID:-duocli/duo-admin-api}"

for cmd in aws jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: $cmd is required but not found in PATH" >&2
    exit 1
  fi
done

secret_json=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_ID" \
  --query SecretString \
  --output text)

export DUO_IKEY
export DUO_SKEY
export DUO_HOST
DUO_IKEY=$(echo "$secret_json" | jq -re '.DUO_IKEY')
DUO_SKEY=$(echo "$secret_json" | jq -re '.DUO_SKEY')
DUO_HOST=$(echo "$secret_json" | jq -re '.DUO_HOST')

exec duocli "$@"
