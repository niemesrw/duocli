from __future__ import annotations

import json

from duocli.output import (
    format_error,
    format_human_list,
    format_human_single,
    format_json,
    warn_secret_key,
)


class TestFormatJson:
    def test_success_dict(self, capsys):
        format_json({"status": "ok", "name": "test"})
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "ok"
        assert data["name"] == "test"
        assert captured.err == ""

    def test_list(self, capsys):
        format_json([{"name": "a"}, {"name": "b"}])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert len(data) == 2


class TestFormatError:
    def test_error_json_on_stdout(self, capsys):
        format_error({"status": "error", "message": "not found", "code": 40401})
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "error"
        assert data["message"] == "not found"

    def test_error_diagnostic_on_stderr(self, capsys):
        format_error({"status": "error", "message": "not found", "code": 40401})
        captured = capsys.readouterr()
        assert "not found" in captured.err


class TestFormatHumanList:
    def test_empty_list(self, capsys):
        format_human_list([])
        captured = capsys.readouterr()
        assert "No integrations found" in captured.out

    def test_table_output(self, capsys):
        items = [
            {"integration_key": "DI123", "name": "App 1", "type": "websdk"},
            {"integration_key": "DI456", "name": "App 2", "type": "adminapi"},
        ]
        format_human_list(items)
        captured = capsys.readouterr()
        assert "DI123" in captured.out
        assert "App 1" in captured.out
        assert "KEY" in captured.out


class TestFormatHumanSingle:
    def test_single_result(self, capsys):
        format_human_single({"status": "ok", "integration_key": "DI123", "name": "Test"})
        captured = capsys.readouterr()
        assert "integration_key: DI123" in captured.out
        assert "name: Test" in captured.out
        assert "status" not in captured.out


class TestWarnSecretKey:
    def test_warning_on_stderr(self, capsys):
        warn_secret_key()
        captured = capsys.readouterr()
        assert "secret_key is sensitive" in captured.err
        assert captured.out == ""
