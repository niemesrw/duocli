from __future__ import annotations

import pytest
import click

from duocli.validate import validate_email, validate_integration_key, validate_name, validate_type, validate_user_id, validate_username


class TestValidateIntegrationKey:
    def test_valid_key_18_chars(self):
        assert validate_integration_key("DI" + "A" * 18) == "DI" + "A" * 18

    def test_valid_key_20_chars(self):
        assert validate_integration_key("DI" + "B1C2D3E4F5G6H7I8J9K0") == "DI" + "B1C2D3E4F5G6H7I8J9K0"

    def test_rejects_too_short(self):
        with pytest.raises(click.BadParameter, match="must match"):
            validate_integration_key("DI" + "A" * 17)

    def test_rejects_too_long(self):
        with pytest.raises(click.BadParameter, match="must match"):
            validate_integration_key("DI" + "A" * 21)

    def test_rejects_wrong_prefix(self):
        with pytest.raises(click.BadParameter, match="must match"):
            validate_integration_key("XX" + "A" * 18)

    def test_rejects_lowercase(self):
        with pytest.raises(click.BadParameter, match="must match"):
            validate_integration_key("DI" + "a" * 18)

    def test_rejects_question_mark(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_integration_key("DI123?fields=all")

    def test_rejects_hash(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_integration_key("DI123#fragment")

    def test_rejects_percent(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_integration_key("DI123%00encoded")

    def test_rejects_control_chars(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_integration_key("DI123\x00AAAAAAAAAAAAAAA")


class TestValidateUsername:
    def test_email_strips_domain(self):
        assert validate_username("alice@example.com") == "alice"

    def test_email_strips_domain_with_dots(self):
        assert validate_username("jane.doe@example.com") == "jane.doe"

    def test_valid_plain_username(self):
        assert validate_username("alice.smith") == "alice.smith"

    def test_rejects_control_chars(self):
        with pytest.raises(click.BadParameter, match="control characters"):
            validate_username("alice\x00@example.com")

    def test_rejects_question_mark(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_username("alice?admin=true")

    def test_rejects_too_long(self):
        with pytest.raises(click.BadParameter, match="256 characters"):
            validate_username("a" * 257)


class TestValidateUserId:
    def test_valid_user_id_18_chars(self):
        assert validate_user_id("DU" + "A" * 18) == "DU" + "A" * 18

    def test_valid_user_id_20_chars(self):
        assert validate_user_id("DU" + "B1C2D3E4F5G6H7I8J9K0") == "DU" + "B1C2D3E4F5G6H7I8J9K0"

    def test_rejects_too_short(self):
        with pytest.raises(click.BadParameter, match="must match"):
            validate_user_id("DU" + "A" * 17)

    def test_rejects_too_long(self):
        with pytest.raises(click.BadParameter, match="must match"):
            validate_user_id("DU" + "A" * 21)

    def test_rejects_wrong_prefix(self):
        with pytest.raises(click.BadParameter, match="must match"):
            validate_user_id("XX" + "A" * 18)

    def test_rejects_di_prefix(self):
        with pytest.raises(click.BadParameter, match="must match"):
            validate_user_id("DI" + "A" * 18)

    def test_rejects_lowercase(self):
        with pytest.raises(click.BadParameter, match="must match"):
            validate_user_id("DU" + "a" * 18)

    def test_rejects_question_mark(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_user_id("DU123?fields=all")

    def test_rejects_control_chars(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_user_id("DU123\x00AAAAAAAAAAAAAAA")


class TestValidateEmail:
    def test_valid_email(self):
        assert validate_email("alice@example.com") == "alice@example.com"

    def test_valid_email_with_dots(self):
        assert validate_email("jane.doe@example.com") == "jane.doe@example.com"

    def test_rejects_no_at(self):
        with pytest.raises(click.BadParameter, match="exactly one '@'"):
            validate_email("not-an-email")

    def test_rejects_multiple_at(self):
        with pytest.raises(click.BadParameter, match="exactly one '@'"):
            validate_email("a@@b.com")

    def test_rejects_empty_local(self):
        with pytest.raises(click.BadParameter, match="non-empty"):
            validate_email("@example.com")

    def test_rejects_empty_domain(self):
        with pytest.raises(click.BadParameter, match="non-empty"):
            validate_email("alice@")

    def test_rejects_control_chars(self):
        with pytest.raises(click.BadParameter, match="control characters"):
            validate_email("alice\x00@example.com")

    def test_rejects_question_mark(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_email("alice?@example.com")

    def test_rejects_too_long(self):
        with pytest.raises(click.BadParameter, match="256 characters"):
            validate_email("a" * 250 + "@example.com")


class TestValidateName:
    def test_valid_name(self):
        assert validate_name("My Test App") == "My Test App"

    def test_valid_name_with_special_chars(self):
        assert validate_name("App (Production) - v2.0") == "App (Production) - v2.0"

    def test_rejects_control_chars(self):
        with pytest.raises(click.BadParameter, match="control characters"):
            validate_name("test\x00app")

    def test_rejects_newline(self):
        with pytest.raises(click.BadParameter, match="control characters"):
            validate_name("test\napp")

    def test_rejects_tab(self):
        with pytest.raises(click.BadParameter, match="control characters"):
            validate_name("test\tapp")

    def test_rejects_path_traversal(self):
        with pytest.raises(click.BadParameter, match="path traversal"):
            validate_name("../../etc/passwd")

    def test_rejects_too_long(self):
        with pytest.raises(click.BadParameter, match="256 characters"):
            validate_name("A" * 257)

    def test_allows_max_length(self):
        name = "A" * 256
        assert validate_name(name) == name

    def test_rejects_script_with_control_chars(self):
        # The <script> tag itself is fine — no control chars
        assert validate_name("test<script>alert(1)</script>") == "test<script>alert(1)</script>"


class TestValidateType:
    def test_valid_type(self):
        assert validate_type("websdk") == "websdk"

    def test_valid_type_adminapi(self):
        assert validate_type("adminapi") == "adminapi"

    def test_rejects_control_chars(self):
        with pytest.raises(click.BadParameter, match="control characters"):
            validate_type("web\x00sdk")

    def test_rejects_question_mark(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_type("websdk?extra=1")

    def test_rejects_hash(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_type("websdk#frag")

    def test_rejects_percent(self):
        with pytest.raises(click.BadParameter, match="invalid characters"):
            validate_type("websdk%00")
