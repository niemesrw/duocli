# GCP Secret Manager — duocli secret template

Store Duo Admin API credentials in GCP Secret Manager using Terraform. Every secret access is logged in Cloud Audit Logs, giving you an audit trail of who ran duocli and when.

## Prerequisites

- GCP project with billing enabled
- [Terraform](https://developer.hashicorp.com/terraform/install) (>= 1.5)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- Application Default Credentials: `gcloud auth application-default login`

## Setup

1. Copy and edit the variables file:

   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

   Fill in `project_id`, `secret_admin_member`, and `secret_reader_members`.

2. Set Duo credentials (avoid putting secrets in tfvars):

   ```bash
   export TF_VAR_duo_secret_json='{"DUO_IKEY":"...","DUO_SKEY":"...","DUO_HOST":"..."}'
   ```

3. Deploy:

   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

## Usage

```bash
export DUOCLI_GCP_PROJECT=your-project-id
chmod +x wrapper.sh

./wrapper.sh list-apps
./wrapper.sh --human info-summary
./wrapper.sh create-app --name "My App" --type websdk
```

The wrapper fetches credentials from Secret Manager, exports them as env vars, and execs duocli. Your `gcloud auth` identity is recorded in audit logs.

## What gets audited

Cloud Audit Logs record a `SecretVersionAccess` data access event for every secret read, including:

- **Who** — the IAM principal (user, service account, group member)
- **When** — timestamp
- **What** — secret name and version
- **Where** — caller IP address

View audit logs:

```bash
gcloud logging read \
  'resource.type="secretmanager.googleapis.com/Secret" AND
   protoPayload.methodName="google.cloud.secretmanager.v1.SecretManagerService.AccessSecretVersion"' \
  --project=your-project-id \
  --limit=10 \
  --format="table(timestamp,protoPayload.authenticationInfo.principalEmail,protoPayload.resourceName)"
```

**Note:** Data Access audit logs for Secret Manager must be enabled. Go to: IAM & Admin → Audit Logs → Secret Manager API → enable "Data Read".

## IAM roles used

| Role | Assigned to | Allows |
|------|------------|--------|
| Secret Manager Secret Accessor | Reader members | Read secret versions |
| Secret Manager Admin | Admin member | Create, update, delete secrets |

## Rotating credentials

```bash
echo '{"DUO_IKEY":"...","DUO_SKEY":"...","DUO_HOST":"..."}' | \
  gcloud secrets versions add duocli-duo-admin-api \
    --data-file=- \
    --project=your-project-id
```

Previous versions remain accessible until explicitly disabled or destroyed.

## Cleanup

```bash
terraform destroy
```
