# Azure Key Vault — duocli secret template

Store Duo Admin API credentials in Azure Key Vault with RBAC-based access control. Every secret access is logged in Azure Monitor, giving you an audit trail of who ran duocli and when.

## Prerequisites

- Azure subscription with a resource group
- [az CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) installed and authenticated (`az login`)
- [jq](https://jqlang.github.io/jq/) installed
- Entra ID object IDs for the admin and any users who need read access

## Setup

1. Copy and edit the parameters file:

   ```bash
   cp parameters.example.json parameters.json
   ```

   Fill in:
   - `vaultName` — globally unique vault name
   - `secretAdminPrincipalId` — Entra ID object ID of the vault admin
   - `secretReaderPrincipalIds` — object IDs of users who will run duocli
   - `duoSecretValue` — JSON string with your Duo credentials

   To find your object ID: `az ad signed-in-user show --query id -o tsv`

2. Deploy:

   ```bash
   chmod +x setup.sh
   ./setup.sh <resource-group> parameters.json
   ```

## Usage

```bash
export DUOCLI_VAULT_NAME=duocli-secrets
chmod +x wrapper.sh

./wrapper.sh list-apps
./wrapper.sh create-app --name "My App" --type websdk --human
./wrapper.sh auth-logs --since 24h --human
```

The wrapper fetches credentials from Key Vault, exports them as env vars, and execs duocli. Your `az login` identity is recorded in the audit log.

## What gets audited

Azure Monitor logs a `SecretGet` event for every `az keyvault secret show` call, including:

- **Who** — the Entra ID principal (user, service principal, managed identity)
- **When** — timestamp
- **What** — vault name and secret name
- **Where** — caller IP address

View audit logs:

```bash
# Recent secret access events
az monitor activity-log list \
  --resource-group <resource-group> \
  --query "[?contains(resourceId, 'Microsoft.KeyVault')]" \
  --output table
```

Or use the Azure Portal: Key Vault → Monitoring → Diagnostic settings → enable logging to a Log Analytics workspace.

## RBAC roles used

| Role | Assigned to | Allows |
|------|------------|--------|
| Key Vault Secrets User | Reader principals | Read secret values |
| Key Vault Secrets Officer | Admin principal | Create, update, delete secrets |

## Rotating credentials

Update the secret value:

```bash
az keyvault secret set \
  --vault-name duocli-secrets \
  --name duo-admin-api \
  --value '{"DUO_IKEY":"...","DUO_SKEY":"...","DUO_HOST":"..."}'
```

Soft delete is enabled (90-day retention) with purge protection, so previous versions are recoverable.

## Security notes

- Never commit `parameters.json` with real credentials — it's listed in `.gitignore` guidance below
- The wrapper exports secrets as env vars only for the lifetime of the duocli process (`exec` replaces the shell)
- Purge protection prevents permanent secret deletion for 90 days
