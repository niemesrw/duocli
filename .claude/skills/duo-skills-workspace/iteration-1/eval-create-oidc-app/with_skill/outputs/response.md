# Response: Create a Duo OIDC App Called "Sales Dashboard"

## Step 1: Check credentials

Before running the command, let me verify your Duo Admin API credentials are set:

```bash
echo "IKEY=${DUO_IKEY:-(not set)}  HOST=${DUO_HOST:-(not set)}"
```

If those show `(not set)`, I'll need to know where your credentials are stored. Common options:

- **1Password CLI** — tell me the vault and item name
- **AWS Secrets Manager** — tell me the AWS profile and secret name/ARN
- **`.env` file** — set `DUO_IKEY`, `DUO_SKEY`, and `DUO_HOST` per `.env.example`, then source it

Once credentials are confirmed (you should see a real host like `api-XXXXXXXX.duosecurity.com`), proceed below.

---

## Step 2: Dry-run first

Always preview before creating:

```bash
uv run duocli create-oidc-app \
    --name "Sales Dashboard" \
    --redirect-uri https://sales.example.com/callback \
    --dry-run
```

This validates your inputs and shows exactly what would be sent to the Duo API — no changes are made.

---

## Step 3: Create the app

Once the dry-run looks correct:

```bash
uv run duocli create-oidc-app \
    --name "Sales Dashboard" \
    --redirect-uri https://sales.example.com/callback
```

**What this creates (defaults applied):**

| Setting | Value |
|---|---|
| Grant type | `authorization_code` |
| Scopes | `openid`, `email`, `profile` |
| IdP claim mappings | `mail` → `email`, `displayname` → `name` |
| User access | `ALL_USERS` |
| Provisioning | JIT enabled |
| PKCE | Enforced by Duo policy |

---

## Step 4: Note the integration key and issuer URL

After creation, the output will include an `integration_key` (format: `DI` + 18–20 alphanumeric characters). Use it to derive the OIDC issuer URL for your Sales Dashboard app configuration:

```
https://<sso-host>/oidc/<integration_key>
# e.g. https://sso-XXXXXXXX.sso.duosecurity.com/oidc/DIXXXXXXXXXXXXXXXXXX
```

The SSO host is account-wide — check the Duo Admin Panel or an existing SSO app if you don't know yours.

---

## Optional: Restrict access or add M2M grant

If you want to limit who can access Sales Dashboard or add a `client_credentials` grant for service accounts:

```bash
uv run duocli create-oidc-app \
    --name "Sales Dashboard" \
    --redirect-uri https://sales.example.com/callback \
    --user-access PERMITTED_GROUPS \
    --grant-type authorization_code \
    --grant-type client_credentials
```

Let me know once the dry-run output looks good and I'll confirm you're ready to create.
