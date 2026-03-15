#!/usr/bin/env bash
set -euo pipefail

# Fetch Duo credentials from GCP Secret Manager and run duocli.
#
# Prerequisites:
#   - gcloud cli installed and authenticated (gcloud auth login)
#   - Secret Manager Secret Accessor role on the secret
#   - jq installed
#
# Configuration (env vars):
#   DUOCLI_GCP_PROJECT  - GCP project ID (required)
#   DUOCLI_SECRET_ID    - Secret ID (default: duocli-duo-admin-api)
#
# Usage:
#   export DUOCLI_GCP_PROJECT=my-project
#   ./wrapper.sh list-apps --human
#   ./wrapper.sh create-app --name "My App" --type websdk

GCP_PROJECT="${DUOCLI_GCP_PROJECT:?Set DUOCLI_GCP_PROJECT to your GCP project ID}"
SECRET_ID="${DUOCLI_SECRET_ID:-duocli-duo-admin-api}"

for cmd in gcloud jq; do
  if ! command -v "$cmd" &>/dev/null; then
    echo "Error: $cmd is required but not found in PATH" >&2
    exit 1
  fi
done

secret_json=$(gcloud secrets versions access latest \
  --secret="$SECRET_ID" \
  --project="$GCP_PROJECT")

export DUO_IKEY
export DUO_SKEY
export DUO_HOST
DUO_IKEY=$(echo "$secret_json" | jq -re '.DUO_IKEY')
DUO_SKEY=$(echo "$secret_json" | jq -re '.DUO_SKEY')
DUO_HOST=$(echo "$secret_json" | jq -re '.DUO_HOST')

exec duocli "$@"
