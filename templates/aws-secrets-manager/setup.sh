#!/usr/bin/env bash
set -euo pipefail

# Deploy the duocli Secrets Manager stack using CDK.
#
# Prerequisites:
#   - aws cli installed and authenticated
#   - Node.js and npm installed
#   - CDK bootstrapped in the target account/region
#
# Usage:
#   ./setup.sh                                           # deploy with defaults
#   ./setup.sh --profile management-admin                # specify AWS profile
#   ./setup.sh -c readerArns='["arn:aws:iam::123:user/alice"]'  # grant read access

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CDK_DIR="$SCRIPT_DIR/cdk"

cd "$CDK_DIR"

if [ ! -d "node_modules" ]; then
  echo "Installing CDK dependencies..."
  npm install
fi

echo "Deploying DuocliSecretsStack..."
npx cdk deploy --require-approval never "$@"

echo ""
echo "Deployment complete."
echo ""
echo "To store your Duo credentials:"
echo "  aws secretsmanager put-secret-value \\"
echo "    --secret-id duocli/duo-admin-api \\"
echo "    --secret-string '{\"DUO_IKEY\":\"...\",\"DUO_SKEY\":\"...\",\"DUO_HOST\":\"...\"}'"
