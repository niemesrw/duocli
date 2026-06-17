To check what policies are configured in your Duo account, you can use the `duocli` CLI with the appropriate command. Based on the project's architecture, you would need your Duo Admin API credentials set up first.

**Prerequisites**

Make sure your credentials are exported or in a `.env` file:

```bash
export DUO_IKEY=your_integration_key
export DUO_SKEY=your_secret_key
export DUO_HOST=api-XXXXXXXX.duosecurity.com
```

**Listing policies**

I don't see a dedicated `list-policies` command documented in the project's CLAUDE.md, which lists 14 commands in `cli.py`. You may want to check what commands are available:

```bash
uv run duocli --help
```

If a policy-related command exists, it would likely look something like:

```bash
# JSON output (default)
uv run duocli list-policies

# Human-readable table
uv run duocli --human list-policies
```

**If no policy command exists**

You could query policies directly via the Duo Admin API. The relevant endpoint is:

```
GET /admin/v1/policies
```

Or you could look at the source to confirm available commands:

```bash
grep -n "^@cli.command" src/duocli/cli.py
```

Would you like me to look at the current codebase to confirm whether a policy listing command is available, or help you add one if it's missing?
