I can help you list your Duo integrations and display just the name and type fields.

Based on the project's CLI, you can use the `list-apps` command. To show only name and type, you can filter the JSON output with a tool like `jq`:

```bash
uv run duocli list-apps | jq '[.[] | {name, type}]'
```

Or if you prefer a human-readable format, run with the `--human` flag (though that shows all fields):

```bash
uv run duocli --human list-apps
```

If the JSON output is an array of integration objects, the `jq` command above will extract just `name` and `type` from each entry.

**Example output (JSON)**:
```json
[
  { "name": "My Web App", "type": "websdk" },
  { "name": "VPN Integration", "type": "radius" },
  { "name": "Admin Panel", "type": "adminapi" }
]
```

Make sure your credentials are set before running:

```bash
export DUO_IKEY=your_integration_key
export DUO_SKEY=your_secret_key
export DUO_HOST=api-XXXXXXXX.duosecurity.com
```

Or place them in a `.env` file in the project root.
