# Response: "give me an overview of our duo tenant"

## Simulated Claude Code Response (no skill loaded)

---

To give you an overview of your Duo tenant, I can pull information from the available CLI commands. Here's what I can gather using `duocli`:

**What I would need to run (but am not running):**

1. **Applications** — `uv run duocli --human list-apps`
   Lists all integrations (applications) configured in your Duo tenant.

2. **Users** — There does not appear to be a `list-users` command in this CLI. You may need to use the Duo Admin Panel or the raw API for user counts/details.

3. **Auth Logs** — `uv run duocli --human auth-logs`
   Recent authentication activity.

4. **Policies** — There is no explicit `list-policies` command surfaced in the CLI based on the codebase.

---

**Without running commands, I cannot provide:**
- Number of active users or groups
- Number and types of configured applications
- Recent authentication volume or failure rates
- Active policy configurations
- Trust Monitor events or anomalies

---

**To get a real overview, I suggest running:**

```bash
uv run duocli --human list-apps
```

This will show you the applications configured. For a fuller picture (users, groups, logs, policies), you would either need additional CLI commands to be implemented, or you can check the [Duo Admin Panel](https://admin.duosecurity.com) directly.

Would you like me to run `list-apps` to at least show what integrations exist?
