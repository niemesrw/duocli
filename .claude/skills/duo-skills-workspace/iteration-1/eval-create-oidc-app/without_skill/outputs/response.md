# Response: Create a Duo OIDC App Called "Sales Dashboard"

To create a Duo OIDC application called "Sales Dashboard" with the redirect URI `https://sales.example.com/callback`, you can use the `create-oidc-app` command:

```bash
uv run duocli create-oidc-app \
  --name "Sales Dashboard" \
  --redirect-uri "https://sales.example.com/callback"
```

This will create an OIDC application in Duo with default settings. The output will include the integration key, secret key, and other application details in JSON format.

If you want human-readable output, add `--human` before the subcommand:

```bash
uv run duocli --human create-oidc-app \
  --name "Sales Dashboard" \
  --redirect-uri "https://sales.example.com/callback"
```

To preview what would be created without making any changes, use `--dry-run`:

```bash
uv run duocli create-oidc-app \
  --name "Sales Dashboard" \
  --redirect-uri "https://sales.example.com/callback" \
  --dry-run
```

Make sure your Duo credentials are set before running:

```bash
export DUO_IKEY=your_integration_key
export DUO_SKEY=your_secret_key
export DUO_HOST=api-XXXXXXXX.duosecurity.com
```

Or add them to a `.env` file in the project root (use `.env.example` as a template).
