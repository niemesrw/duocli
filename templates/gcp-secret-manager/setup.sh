#!/usr/bin/env bash
set -euo pipefail

# Deploy the duocli GCP Secret Manager resources using Terraform.
#
# Prerequisites:
#   - terraform installed
#   - gcloud cli installed and authenticated (gcloud auth application-default login)
#   - A GCP project with billing enabled
#
# Usage:
#   cp terraform.tfvars.example terraform.tfvars  # edit with real values
#   export TF_VAR_duo_secret_json='{"DUO_IKEY":"...","DUO_SKEY":"...","DUO_HOST":"..."}'
#   ./setup.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "terraform.tfvars" ]; then
  echo "Error: terraform.tfvars not found. Copy terraform.tfvars.example and edit it." >&2
  exit 1
fi

terraform init
terraform apply

echo ""
echo "Deployment complete."
