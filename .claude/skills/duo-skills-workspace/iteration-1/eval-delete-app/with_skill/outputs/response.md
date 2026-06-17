# Simulated Claude Response: Delete Duo App DI1234567890ABCDEF

---

Before deleting, let me verify credentials are available and confirm the app details.

**Step 1: Check credentials**

```bash
echo "IKEY=${DUO_IKEY:-(not set)}  HOST=${DUO_HOST:-(not set)}"
```

If credentials are not set, I'll need to know where they're stored (AWS Secrets Manager, 1Password, or .env file) before proceeding.

---

Assuming credentials are set, **Step 2: Inspect the app before deleting** (best practice for irreversible operations):

```bash
uv run duocli --human get-app --ikey DI1234567890ABCDEF
```

This confirms the app name and type so you know exactly what will be deleted.

---

**Step 3: Dry-run the delete** (the skill recommends this before any destructive operation):

```bash
uv run duocli delete-app --ikey DI1234567890ABCDEF --dry-run
```

---

**Step 4: Execute the delete** (only after confirming the above):

```bash
uv run duocli delete-app --ikey DI1234567890ABCDEF
```

---

**Warning:** `delete-app` is irreversible. Once deleted, the integration key, secret key, and all associated configuration are permanently removed. Any applications or services authenticating via this integration will immediately lose access.

Do you want me to proceed with the dry-run first, or do you need to load credentials?
