from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from duocli.cli import cli
from duocli.oauth import OAuthClient

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

    def test_auth_logs_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auth-logs", "--help"])
        assert result.exit_code == 0
        assert "--since" in result.output
        assert "--fields" in result.output

    def test_admin_logs_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["admin-logs", "--help"])
        assert result.exit_code == 0
        assert "--since" in result.output
        assert "--fields" in result.output

    def test_schema_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "--help"])
        assert result.exit_code == 0


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
        result = runner.invoke(cli, ["delete-app", "--ikey", "DIAAAAAAAAAAAAAAAAAAA"])
        assert result.exit_code == 1


class TestCliMissingArgs:
    def test_create_app_missing_both(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-app"])
        assert result.exit_code != 0

    def test_delete_app_missing_ikey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["delete-app"])
        assert result.exit_code != 0


class TestCliValidation:
    """Test that input validation rejects bad inputs."""

    def test_create_app_rejects_control_char_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-app", "--name", "test\x00app", "--type", "websdk"])
        assert result.exit_code != 0

    def test_create_app_rejects_injection_type(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-app", "--name", "test", "--type", "websdk?extra=1"])
        assert result.exit_code != 0

    def test_delete_app_rejects_bad_ikey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["delete-app", "--ikey", "DI123?fields=all"])
        assert result.exit_code != 0

    def test_delete_app_rejects_short_ikey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["delete-app", "--ikey", "DITOOSHORT"])
        assert result.exit_code != 0


class TestCliDryRun:
    """Test --dry-run mode does not call the API."""

    @patch("duocli.cli.load_dotenv")
    def test_create_app_dry_run(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-app", "--name", "Test App", "--type", "websdk", "--dry-run"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["action"] == "create_integration"
        assert data["params"]["name"] == "Test App"
        assert data["params"]["type"] == "websdk"

    @patch("duocli.cli.load_dotenv")
    def test_delete_app_dry_run(self, mock_dotenv):
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, [
            "delete-app", "--ikey", ikey, "--dry-run"
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["action"] == "delete_integration"
        assert data["params"]["integration_key"] == ikey

    @patch("duocli.cli.load_dotenv")
    def test_dry_run_validates_inputs(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-app", "--name", "test\x00bad", "--type", "websdk", "--dry-run"
        ])
        assert result.exit_code != 0


class TestCliSchema:
    def test_schema_create_app(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "create-app"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["command"] == "create-app"
        param_names = [p["name"] for p in data["params"]]
        assert "--name" in param_names
        assert "--type" in param_names

    def test_schema_delete_app(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "delete-app"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["command"] == "delete-app"
        param_names = [p["name"] for p in data["params"]]
        assert "--ikey" in param_names

    def test_schema_list_apps(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "list-apps"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["command"] == "list-apps"

    def test_schema_unknown_command(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["schema", "nonexistent"])
        assert result.exit_code != 0


class TestCliFields:
    """Test --fields filtering."""

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_list_apps_fields(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.list_integrations.return_value = [
            {"integration_key": "DIAAAAAAAAAAAAAAAAA", "name": "App 1", "type": "websdk"},
        ]
        mock_get_backend.return_value = mock_backend

        runner = CliRunner()
        result = runner.invoke(cli, ["list-apps", "--fields", "integration_key,name"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert set(data[0].keys()) == {"integration_key", "name"}
        assert "type" not in data[0]


class TestCliJsonPayload:
    """Test --json payload for create-app."""

    @patch("duocli.cli.load_dotenv")
    def test_json_dry_run(self, mock_dotenv):
        runner = CliRunner()
        payload = '{"name": "Test", "type": "websdk", "enroll_policy": "allow"}'
        result = runner.invoke(cli, ["create-app", "--json", payload, "--dry-run"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["params"]["name"] == "Test"
        assert data["params"]["type"] == "websdk"
        assert data["params"]["enroll_policy"] == "allow"

    def test_json_mutually_exclusive_with_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-app", "--json", '{"name": "X", "type": "y"}', "--name", "Conflict"
        ])
        assert result.exit_code != 0

    @patch("duocli.cli.load_dotenv")
    def test_json_invalid_json(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-app", "--json", "{bad json}"])
        assert result.exit_code == 1

    @patch("duocli.cli.load_dotenv")
    def test_json_missing_required_fields(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-app", "--json", '{"enroll_policy": "allow"}'])
        assert result.exit_code == 1

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_json_creates_integration(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.create_integration.return_value = {
            "status": "ok",
            "integration_key": "DIAAAAAAAAAAAAAAAAA",
            "secret_key": "secret",
            "name": "Test",
            "type": "websdk",
        }
        mock_get_backend.return_value = mock_backend

        runner = CliRunner()
        payload = '{"name": "Test", "type": "websdk"}'
        result = runner.invoke(cli, ["create-app", "--json", payload])
        assert result.exit_code == 0
        mock_backend.create_integration.assert_called_once_with(
            name="Test", integration_type="websdk"
        )


class TestCreateOidcApp:
    """Tests for the create-oidc-app command."""

    _IKEY = "DI" + "A" * 18
    _SUCCESS = {
        "status": "ok",
        "integration_key": "DI" + "A" * 18,
        "secret_key": "",
        "name": "My OIDC App",
        "type": "sso-oidc-generic",
    }

    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-oidc-app", "--help"])
        assert result.exit_code == 0
        assert "--name" in result.output
        assert "--redirect-uri" in result.output
        assert "--user-access" in result.output
        assert "--grant-type" in result.output

    def test_missing_name(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-oidc-app", "--redirect-uri", "https://app.example.com/cb"])
        assert result.exit_code != 0
        assert "--name" in result.output

    def test_missing_redirect_uri(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["create-oidc-app", "--name", "My App"])
        assert result.exit_code != 0
        assert "--redirect-uri" in result.output

    @patch("duocli.cli.load_dotenv")
    def test_invalid_grant_type(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-oidc-app",
            "--name", "My App",
            "--redirect-uri", "https://app.example.com/cb",
            "--grant-type", "password",
        ])
        assert result.exit_code == 1
        assert "Invalid grant type" in result.output

    @patch("duocli.cli.load_dotenv")
    def test_invalid_user_access(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-oidc-app",
            "--name", "My App",
            "--redirect-uri", "https://app.example.com/cb",
            "--user-access", "EVERYONE",
        ])
        assert result.exit_code == 1
        assert "Invalid user_access" in result.output

    @patch("duocli.cli.load_dotenv")
    def test_dry_run_defaults(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-oidc-app",
            "--name", "My App",
            "--redirect-uri", "https://app.example.com/cb",
            "--dry-run",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["action"] == "create_oidc_app"
        params = data["params"]
        assert params["name"] == "My App"
        assert params["type"] == "sso-oidc-generic"
        assert params["user_access"] == "ALL_USERS"
        assert params["enroll_policy"] == "allow"
        oidc = params["sso"]["oidc_config"]
        assert oidc["grant_types"] == {"authorization_code": True}
        assert "https://app.example.com/cb" in oidc["redirect_uris"]
        scope_names = [s["name"] for s in oidc["scopes"]]
        assert "openid" in scope_names
        assert "email" in scope_names
        assert "profile" in scope_names

    @patch("duocli.cli.load_dotenv")
    def test_dry_run_multiple_redirect_uris(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-oidc-app",
            "--name", "My App",
            "--redirect-uri", "https://app.example.com/cb",
            "--redirect-uri", "https://localhost:3000/cb",
            "--dry-run",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        uris = data["params"]["sso"]["oidc_config"]["redirect_uris"]
        assert "https://app.example.com/cb" in uris
        assert "https://localhost:3000/cb" in uris

    @patch("duocli.cli.load_dotenv")
    def test_dry_run_custom_user_access(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-oidc-app",
            "--name", "My App",
            "--redirect-uri", "https://app.example.com/cb",
            "--user-access", "PERMITTED_GROUPS",
            "--dry-run",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["params"]["user_access"] == "PERMITTED_GROUPS"

    @patch("duocli.cli.load_dotenv")
    def test_dry_run_multiple_grant_types(self, mock_dotenv):
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-oidc-app",
            "--name", "My App",
            "--redirect-uri", "https://app.example.com/cb",
            "--grant-type", "authorization_code",
            "--grant-type", "client_credentials",
            "--dry-run",
        ])
        assert result.exit_code == 0
        data = json.loads(result.output)
        grant_types = data["params"]["sso"]["oidc_config"]["grant_types"]
        assert grant_types == {"authorization_code": True, "client_credentials": True}

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.create_integration.return_value = self._SUCCESS
        mock_get_backend.return_value = mock_backend

        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-oidc-app",
            "--name", "My OIDC App",
            "--redirect-uri", "https://app.example.com/cb",
        ])
        assert result.exit_code == 0
        mock_backend.create_integration.assert_called_once_with(
            name="My OIDC App",
            integration_type="sso-oidc-generic",
            user_access="ALL_USERS",
            enroll_policy="allow",
            sso={
                "oidc_config": {
                    "grant_types": {"authorization_code": True},
                    "redirect_uris": ["https://app.example.com/cb"],
                    "scopes": [
                        {"name": "openid"},
                        {"name": "email", "idp_attribute_claim_mapping": [{"idp_attribute": "mail", "oidc_claim": "email"}]},
                        {"name": "profile", "idp_attribute_claim_mapping": [{"idp_attribute": "displayname", "oidc_claim": "name"}]},
                    ],
                }
            },
        )

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_api_error(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.create_integration.return_value = {
            "status": "error", "message": "Duo API error", "code": 50000
        }
        mock_get_backend.return_value = mock_backend

        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-oidc-app",
            "--name", "My App",
            "--redirect-uri", "https://app.example.com/cb",
        ])
        assert result.exit_code == 2

    @patch("duocli.cli.load_dotenv")
    def test_no_credentials(self, mock_dotenv, monkeypatch):
        for var in _DUO_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        runner = CliRunner()
        result = runner.invoke(cli, [
            "create-oidc-app",
            "--name", "My App",
            "--redirect-uri", "https://app.example.com/cb",
        ])
        assert result.exit_code == 1


class TestGetApp:
    def test_get_app_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-app", "--help"])
        assert result.exit_code == 0
        assert "--ikey" in result.output
        assert "--fields" in result.output

    def test_get_app_rejects_bad_ikey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-app", "--ikey", "BADKEY"])
        assert result.exit_code != 0

    @patch("duocli.cli.load_dotenv")
    def test_get_app_dry_run(self, mock_dotenv):
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["get-app", "--ikey", ikey, "--dry-run"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["params"]["integration_key"] == ikey

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_get_app_success(self, mock_get_backend, mock_dotenv):
        ikey = "DI" + "A" * 18
        mock_backend = MagicMock()
        mock_backend.get_integration.return_value = {
            "integration_key": ikey,
            "name": "Test App",
            "type": "websdk",
            "status": "active",
            "policy_key": "",
            "notes": "",
            "enroll_policy": "",
            "groups_allowed": [],
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["get-app", "--ikey", ikey])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Test App"

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_get_app_fields(self, mock_get_backend, mock_dotenv):
        ikey = "DI" + "A" * 18
        mock_backend = MagicMock()
        mock_backend.get_integration.return_value = {
            "integration_key": ikey,
            "name": "Test App",
            "type": "websdk",
            "status": "active",
            "policy_key": "",
            "notes": "",
            "enroll_policy": "",
            "groups_allowed": [],
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["get-app", "--ikey", ikey, "--fields", "name,type"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert set(data.keys()) == {"name", "type"}


class TestInfoSummary:
    def test_info_summary_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["info-summary", "--help"])
        assert result.exit_code == 0

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_info_summary_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_info_summary.return_value = {
            "integration_count": 5,
            "user_count": 10,
            "admin_count": 2,
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["info-summary"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["integration_count"] == 5

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_info_summary_error(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_info_summary.return_value = {
            "status": "error", "message": "API error", "code": 50000,
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["info-summary"])
        assert result.exit_code == 2


class TestAuthStats:
    def test_auth_stats_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["auth-stats", "--help"])
        assert result.exit_code == 0
        assert "--since" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_auth_stats_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_auth_stats.return_value = {
            "success": 100, "failure": 5, "fraud": 0, "error": 1,
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["auth-stats", "--since", "7d"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["success"] == 100
        assert "SUCCESS" not in data  # normalized to lowercase


class TestCliHumanErrors:
    """Errors should always be JSON even with --human flag."""

    @patch("duocli.cli.load_dotenv")
    def test_human_mode_error_still_json(self, mock_dotenv, monkeypatch):
        for var in _DUO_ENV_VARS:
            monkeypatch.delenv(var, raising=False)
        runner = CliRunner()
        result = runner.invoke(cli, ["--human", "list-apps"])
        assert result.exit_code == 1


class TestListPolicies:
    def test_list_policies_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["list-policies", "--help"])
        assert result.exit_code == 0
        assert "--fields" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_list_policies_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.list_policies.return_value = [
            {"policy_key": "PK001", "name": "Default", "enabled": True},
            {"policy_key": "PK002", "name": "Strict", "enabled": False},
        ]
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["list-policies"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_list_policies_fields(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.list_policies.return_value = [
            {"policy_key": "PK001", "name": "Default", "enabled": True},
        ]
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["list-policies", "--fields", "policy_key,name"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert set(data[0].keys()) == {"policy_key", "name"}


class TestGetPolicy:
    def test_get_policy_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-policy", "--help"])
        assert result.exit_code == 0
        assert "--id" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_get_policy_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_policy.return_value = {
            "policy_key": "PK001",
            "policy_name": "Default",
            "enabled": True,
            "sections": {},
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["get-policy", "--id", "PK001"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["policy_key"] == "PK001"

    def test_get_policy_missing_id(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["get-policy"])
        assert result.exit_code != 0


class TestUpdateApp:
    def test_update_app_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["update-app", "--help"])
        assert result.exit_code == 0
        assert "--ikey" in result.output
        assert "--json" in result.output

    def test_update_app_rejects_bad_ikey(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["update-app", "--ikey", "BADKEY", "--json", '{"notes": "x"}'])
        assert result.exit_code != 0

    @patch("duocli.cli.load_dotenv")
    def test_update_app_rejects_empty_payload(self, mock_dotenv):
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", "{}"])
        assert result.exit_code == 1

    @patch("duocli.cli.load_dotenv")
    def test_update_app_rejects_unknown_keys(self, mock_dotenv):
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", '{"bogus_field": "x"}'])
        assert result.exit_code == 1
        assert "bogus_field" in result.output

    @patch("duocli.cli.load_dotenv")
    def test_update_app_dry_run(self, mock_dotenv):
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", '{"notes": "test"}', "--dry-run"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["dry_run"] is True
        assert data["action"] == "update_integration"
        assert data["params"]["notes"] == "test"

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_update_app_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.update_integration.return_value = {
            "status": "ok",
            "integration_key": "DI" + "A" * 18,
            "name": "Updated",
            "type": "websdk",
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", '{"notes": "hello"}'])
        assert result.exit_code == 0
        mock_backend.update_integration.assert_called_once_with(
            integration_key=ikey, notes="hello"
        )

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_update_app_reset_secret_warns(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.update_integration.return_value = {
            "status": "ok",
            "integration_key": "DI" + "A" * 18,
            "name": "Test",
            "type": "websdk",
        }
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        ikey = "DI" + "A" * 18
        result = runner.invoke(cli, ["update-app", "--ikey", ikey, "--json", '{"reset_secret_key": true}'])
        assert result.exit_code == 0
        assert "secret_key is sensitive" in result.output


class TestActivityLogs:
    def test_activity_logs_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["activity-logs", "--help"])
        assert result.exit_code == 0
        assert "--since" in result.output
        assert "--limit" in result.output
        assert "--fields" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_activity_logs_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_activity_logs.return_value = [
            {"timestamp": "2026-03-14T00:00:00Z", "action": "create", "actor": "admin",
             "actor_type": "admin", "target": "app", "target_type": "integration",
             "application": "Test", "ip": "1.2.3.4"},
        ]
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["activity-logs", "--since", "1h"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["action"] == "create"

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_activity_logs_passes_limit(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_activity_logs.return_value = []
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["activity-logs", "--since", "1h", "--limit", "10"])
        assert result.exit_code == 0
        call_args = mock_backend.get_activity_logs.call_args
        assert call_args.kwargs.get("limit") == 10


class TestTrustMonitor:
    def test_trust_monitor_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["trust-monitor", "--help"])
        assert result.exit_code == 0
        assert "--since" in result.output
        assert "--limit" in result.output
        assert "--fields" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_trust_monitor_success(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_trust_monitor_events.return_value = [
            {"timestamp": "1710000000000", "type": "auth_anomaly",
             "priority": "high", "description": "https://duo.com/...",
             "from_common_netblock": False, "sekey": "SE123"},
        ]
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["trust-monitor", "--since", "7d"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 1
        assert data[0]["type"] == "auth_anomaly"

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.cli.get_backend")
    def test_trust_monitor_passes_limit(self, mock_get_backend, mock_dotenv):
        mock_backend = MagicMock()
        mock_backend.get_trust_monitor_events.return_value = []
        mock_get_backend.return_value = mock_backend
        runner = CliRunner()
        result = runner.invoke(cli, ["trust-monitor", "--since", "1h", "--limit", "10"])
        assert result.exit_code == 0
        call_args = mock_backend.get_trust_monitor_events.call_args
        assert call_args.kwargs.get("limit") == 10


# ─── OAuth commands ──────────────────────────────────────────────────

_SSO_ENV = {
    "DUO_OAUTH_BASE": "https://sso-test.sso.duosecurity.com/oauth2/TESTAPPID",
    "DUO_OAUTH_CLIENT_ID": "test-client-id",
    "DUO_OAUTH_CLIENT_SECRET": "test-client-secret",
}


class TestOAuthToken:
    def test_oauth_token_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-token", "--help"])
        assert result.exit_code == 0
        assert "--scope" in result.output
        assert "--client-id" in result.output

    @patch("duocli.cli.load_dotenv")
    def test_oauth_token_missing_oauth_base(self, mock_dotenv, monkeypatch):
        for var in (*_DUO_ENV_VARS, "DUO_OAUTH_BASE"):
            monkeypatch.delenv(var, raising=False)
        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-token"])
        assert result.exit_code == 1

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.oauth.requests.post")
    def test_oauth_token_success(self, mock_post, mock_dotenv, monkeypatch):
        for k, v in _SSO_ENV.items():
            monkeypatch.setenv(k, v)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "access_token": "eyJ...",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "agent:call",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-token"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["access_token"] == "eyJ..."
        assert data["token_type"] == "Bearer"

    @patch("duocli.cli.load_dotenv")
    def test_oauth_token_missing_client_creds(self, mock_dotenv, monkeypatch):
        monkeypatch.setenv("DUO_OAUTH_BASE", "https://sso-test.sso.duosecurity.com/oauth2/TESTAPPID")
        monkeypatch.delenv("DUO_OAUTH_CLIENT_ID", raising=False)
        monkeypatch.delenv("DUO_OAUTH_CLIENT_SECRET", raising=False)
        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-token"])
        assert result.exit_code == 1


class TestOAuthIntrospect:
    def test_oauth_introspect_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-introspect", "--help"])
        assert result.exit_code == 0
        assert "--token" in result.output

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.oauth.requests.post")
    def test_oauth_introspect_success(self, mock_post, mock_dotenv, monkeypatch):
        for k, v in _SSO_ENV.items():
            monkeypatch.setenv(k, v)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"active": True, "sub": "agent-alice", "scope": "agent:call"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-introspect", "--token", "eyJ..."])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["active"] is True


class TestOAuthJwks:
    def test_oauth_jwks_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-jwks", "--help"])
        assert result.exit_code == 0

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.oauth.requests.get")
    def test_oauth_jwks_success(self, mock_get, mock_dotenv, monkeypatch):
        for k, v in _SSO_ENV.items():
            monkeypatch.setenv(k, v)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"keys": [{"kty": "RSA", "kid": "abc123"}]}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-jwks"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "keys" in data


class TestOAuthDiscover:
    def test_oauth_discover_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-discover", "--help"])
        assert result.exit_code == 0

    @patch("duocli.cli.load_dotenv")
    @patch("duocli.oauth.requests.get")
    def test_oauth_discover_success(self, mock_get, mock_dotenv, monkeypatch):
        for k, v in _SSO_ENV.items():
            monkeypatch.setenv(k, v)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "issuer": "https://sso-test.sso.duosecurity.com/oauth/v1",
            "token_endpoint": "https://sso-test.sso.duosecurity.com/oauth/v1/token",
            "jwks_uri": "https://sso-test.sso.duosecurity.com/oauth/v1/keys",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        runner = CliRunner()
        result = runner.invoke(cli, ["oauth-discover"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "issuer" in data
        assert "token_endpoint" in data
