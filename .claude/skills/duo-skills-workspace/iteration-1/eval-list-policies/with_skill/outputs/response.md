Let me pull the list of configured policies from your Duo tenant.

First, let me check whether your credentials are already set:

```bash
echo "IKEY=${DUO_IKEY:-(not set)}  HOST=${DUO_HOST:-(not set)}"
```

**If credentials are set**, I'll run:

```bash
uv run duocli --human list-policies
```

This will return all Duo policies with their settings in a readable table. If you also want just the names and keys (useful for referencing a specific policy later):

```bash
uv run duocli list-policies --fields name,policy_key
```

---

**If credentials are not set**, where are your Duo Admin API credentials stored? Common options:

- **AWS Secrets Manager** — I'll need the AWS profile and secret name/ARN
- **1Password CLI** — I'll need the vault, item name, and field names
- **Environment / .env file** — set `DUO_IKEY`, `DUO_SKEY`, and `DUO_HOST` (see `.env.example`)

Once credentials are loaded, I'll run `list-policies` and show you what's configured. If you want to drill into a specific policy afterward, I can run:

```bash
uv run duocli --human get-policy --id <POLICY_KEY>
```
