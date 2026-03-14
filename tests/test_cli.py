from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from duocli.cli import cli

# All env vars that could affect backend selection
_DUO_ENV_VARS = (
    "DUO_IKEY", "DUO_SKEY", "DUO_HOST",
    "DUOCLI_BROKER_URL", "DUOCLI_BROKER_TOKEN",
)


class TestCliHelp:
    def test_main_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "create-app" in result.output
        assert "delete-app" in result.output
        assert "list-apps" in result.output

    def test_create_app_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-app", "--help"])
        assert result.exit_code == 0
        assert "--name" in result.output
        assert "--type" in result.output

    def test_delete_app_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["delete-app", "--help"])
        assert result.exit_code == 0
        assert "--ikey" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestCliMissingCredentials:
    """Tests with no Duo credentials — dotenv mocked out, env vars cleared."""

    @patch("duocli.cli.load_dotenv")
    def test_create_app_no_credentials(self, mock_dotenv, monkeypatch):
        for var in _DUO_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        runner = CliRunner()
        result = runner.invoke(cli, ["create-app", "--name", "test", "--type", "websdk"])
        assert result.exit_code == 1

    @patch("duocli.cli.load_dotenv")
    def test_list_apps_no_credentials(self, mock_dotenv, monkeypatch):
        for var in _DUO_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        runner = CliRunner()
        result = runner.invoke(cli, ["list-apps"])
        assert result.exit_code == 1

    @patch("duocli.cli.load_dotenv")
    def test_delete_app_no_credentials(self, mock_dotenv, monkeypatch):
        for var in _DUO_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        runner = CliRunner()
        result = runner.invoke(cli, ["delete-app", "--ikey", "DI123"])
        assert result.exit_code == 1


class TestCliMissingArgs:
    def test_create_app_missing_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-app", "--type", "websdk"])
        assert result.exit_code != 0

    def test_create_app_missing_type(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-app", "--name", "test"])
        assert result.exit_code != 0

    def test_delete_app_missing_ikey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["delete-app"])
        assert result.exit_code != 0
