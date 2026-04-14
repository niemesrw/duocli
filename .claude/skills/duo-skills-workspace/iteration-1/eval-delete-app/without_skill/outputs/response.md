# Claude Response: Delete Duo App (No Skill Loaded)

**User prompt:** "delete the duo app with key DI1234567890ABCDEF"

---

To delete the Duo application with integration key `DI1234567890ABCDEF`, you can use the `delete-app` command:

```bash
uv run duocli delete-app --ikey DI1234567890ABCDEF
```

If the command requires confirmation, you may also need to add a `--confirm` or `--yes` flag to bypass the prompt:

```bash
uv run duocli delete-app --ikey DI1234567890ABCDEF --yes
```

Make sure your Duo Admin API credentials are set in your environment before running:

```bash
export DUO_IKEY=your_integration_key
export DUO_SKEY=your_secret_key
export DUO_HOST=api-XXXXXXXX.duosecurity.com
```

If the app is not found or deletion fails, the CLI will return a JSON error response with a non-zero exit code.

> **Note:** This action is irreversible. Deleting an app will immediately revoke all authentications associated with it. Make sure you have the correct integration key before proceeding.
