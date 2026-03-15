# duocli

CLI tool for managing Duo Security integrations.

## Quick Start

```bash
# Set credentials
export DUO_IKEY=your_integration_key
export DUO_SKEY=your_secret_key
export DUO_HOST=api-XXXXXXXX.duosecurity.com

# Run with uv (no install needed)
uv run duocli.py list-apps
uv run duocli.py create-app --name "My App" --type websdk
uv run duocli.py delete-app --ikey DIXXXXXXXXXXXXXXXXXX
```

## Secret Management

Store Duo credentials in your cloud provider's secret store for auditable access. Each template includes IaC setup and a wrapper script that fetches creds at runtime.

![Secret Management Architecture](docs/secret-management-architecture.svg)

| Template | IaC | Audit Trail |
|----------|-----|-------------|
| [Azure Key Vault](templates/azure-keyvault/) | Bicep | Azure Monitor |
| [AWS Secrets Manager](templates/aws-secrets-manager/) | CDK (TypeScript) | CloudTrail |
| [GCP Secret Manager](templates/gcp-secret-manager/) | Terraform | Cloud Audit Logs |
| [1Password](templates/1password/) | op CLI | Activity Log |
