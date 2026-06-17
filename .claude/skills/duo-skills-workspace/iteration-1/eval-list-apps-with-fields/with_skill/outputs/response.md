First, let me check whether your Duo credentials are already set:

```bash
echo "IKEY=${DUO_IKEY:-(not set)}  HOST=${DUO_HOST:-(not set)}"
```

If those are set, I'll run the following to list all integrations showing only the name and type fields:

```bash
uv run duocli list-apps --fields name,type
```

This will return JSON output scoped to just those two fields for every integration in your account. If you'd prefer a human-readable table instead, use:

```bash
uv run duocli --human list-apps --fields name,type
```

If your credentials are not set yet — let me know where they're stored (AWS Secrets Manager, 1Password, or a `.env` file) and I'll help you load them first.
