---
name: new-command
description: |
  Scaffold a new duocli CLI command end-to-end. Use when the user wants to
  add a new Duo API command, create a new CLI subcommand, or extend duocli
  with a new operation. Covers the full cycle: ABC method, backend
  implementations, CLI handler, and tests.
---

# Add a New duocli Command

Follow these steps in order. Each step builds on the previous one.

## Step 1: Define the backend method

Add an abstract method to `src/duocli/backends/base.py`:

```python
@abstractmethod
def your_method(self, param: str) -> dict:
    """Brief description."""
    ...
```

## Step 2: Implement in DirectBackend

In `src/duocli/backends/direct.py`, implement the method. Follow the existing pattern:

- Call `self._admin.some_duo_sdk_method(...)`
- Wrap in `try/except RuntimeError`
- On error: return `{"status": "error", "message": str(exc), "code": 50000}`
- On success: return a normalized flat dict with `"status": "ok"` and extracted fields
- Use `.get()` with safe defaults (`""`, `[]`, `{}`) for all fields

## Step 3: Stub in BrokerBackend

In `src/duocli/backends/broker.py`, add:

```python
def your_method(self, param: str) -> dict:
    raise NotImplementedError("Broker mode not yet implemented")
```

## Step 4: Add the CLI command

In `src/duocli/cli.py`, add a Click command following this pattern:

```python
@cli.command()
@click.option("--your-option", required=True, help="Description")
@click.option("--fields", default=None, help="Comma-separated columns")
@click.option("--dry-run", is_flag=True, help="Show what would be sent")
@click.pass_context
def your_command(ctx, your_option, fields, dry_run):
    """One-line description."""
    # 1. Validate inputs (raises click.BadParameter on failure)
    your_option = validate_something(your_option)

    # 2. Dry-run check
    if dry_run:
        format_json({"dry_run": True, "your_option": your_option})
        return

    # 3. Get backend (may exit 1 if no credentials)
    backend = get_backend()

    # 4. Call backend
    result = backend.your_method(your_option)

    # 5. Check for error
    if result.get("status") == "error":
        format_error(result)
        sys.exit(2)

    # 6. Format output
    if ctx.obj["human"]:
        format_human_single(result)  # or format_human_list(result, columns)
    else:
        format_json(result)
```

**Key conventions:**
- Validate before dry-run, dry-run before backend
- Errors always JSON (even with `--human`)
- Exit 1 for input errors, exit 2 for API errors
- `--fields` for list commands, `--dry-run` for mutating commands

## Step 5: Write tests

In `tests/test_cli.py`, add a test class following this order:

1. **Help**: `runner.invoke(cli, ["your-command", "--help"])` → exit 0, contains description
2. **Missing args**: invoke without required options → exit non-zero
3. **Validation**: invalid inputs → exit non-zero, error message
4. **Dry-run**: `--dry-run` → exit 0, JSON payload, no backend call
5. **Success**: mock backend returns ok → exit 0, correct output
6. **Error**: mock backend returns error → exit 2, error JSON
7. **Fields** (if applicable): `--fields` filters output columns

**Mocking pattern:**
```python
@patch("duocli.cli.load_dotenv")
@patch("duocli.cli.get_backend")
def test_success(self, mock_backend, mock_dotenv):
    backend = MagicMock()
    mock_backend.return_value = backend
    backend.your_method.return_value = {"status": "ok", "key": "value"}
    result = runner.invoke(cli, ["your-command", "--your-option", "value"])
    assert result.exit_code == 0
```

## Step 6: Verify

```bash
uv run pytest tests/ -v -x
```

All tests must pass before committing.
