from __future__ import annotations

import re

import click


_IKEY_PATTERN = re.compile(r"^DI[A-Z0-9]{18,20}$")
_USER_ID_PATTERN = re.compile(r"^DU[A-Z0-9]{18,20}$")
_CONTROL_CHARS = re.compile(r"[\x00-\x1f]")
_DANGEROUS_CHARS = re.compile(r"[?#%]")


def validate_integration_key(value: str) -> str:
    """Validate a Duo integration key format.

    Must match ^DI[A-Z0-9]{18,20}$ and contain no injection characters.
    """
    if _CONTROL_CHARS.search(value) or _DANGEROUS_CHARS.search(value):
        raise click.BadParameter(
            f"Integration key contains invalid characters: {value!r}"
        )
    if not _IKEY_PATTERN.match(value):
        raise click.BadParameter(
            f"Integration key must match DI[A-Z0-9]{{18,20}}: {value!r}"
        )
    return value


def validate_name(value: str) -> str:
    """Validate an integration name.

    Rejects control characters, path traversal, and enforces max length.
    """
    if _CONTROL_CHARS.search(value):
        raise click.BadParameter(
            f"Name contains control characters: {value!r}"
        )
    if "../" in value:
        raise click.BadParameter(
            f"Name contains path traversal: {value!r}"
        )
    if len(value) > 256:
        raise click.BadParameter(
            f"Name exceeds 256 characters (got {len(value)})"
        )
    return value


def validate_username(value: str) -> str:
    """Validate a Duo username string.

    Rejects control characters, injection characters, and enforces max length.
    If the value looks like an email (contains '@'), the domain is stripped
    because Duo stores usernames as the local part only.
    """
    if _CONTROL_CHARS.search(value):
        raise click.BadParameter(
            f"Username contains control characters: {value!r}"
        )
    if _DANGEROUS_CHARS.search(value):
        raise click.BadParameter(
            f"Username contains invalid characters: {value!r}"
        )
    if "@" in value:
        value = value.split("@", 1)[0]
    if len(value) > 256:
        raise click.BadParameter(
            f"Username exceeds 256 characters (got {len(value)})"
        )
    return value


def validate_user_id(value: str) -> str:
    """Validate a Duo user ID format.

    Must match ^DU[A-Z0-9]{18,20}$ and contain no injection characters.
    """
    if _CONTROL_CHARS.search(value) or _DANGEROUS_CHARS.search(value):
        raise click.BadParameter(
            f"User ID contains invalid characters: {value!r}"
        )
    if not _USER_ID_PATTERN.match(value):
        raise click.BadParameter(
            f"User ID must match DU[A-Z0-9]{{18,20}}: {value!r}"
        )
    return value


def validate_email(value: str) -> str:
    """Validate that a value looks like an email address.

    Must contain exactly one '@' with non-empty local and domain parts.
    Rejects control characters and injection characters.
    """
    if _CONTROL_CHARS.search(value):
        raise click.BadParameter(
            f"Email contains control characters: {value!r}"
        )
    if _DANGEROUS_CHARS.search(value):
        raise click.BadParameter(
            f"Email contains invalid characters: {value!r}"
        )
    if "@" not in value or value.count("@") != 1:
        raise click.BadParameter(
            f"Email must contain exactly one '@': {value!r}"
        )
    local, domain = value.split("@", 1)
    if not local or not domain:
        raise click.BadParameter(
            f"Email must have non-empty local and domain parts: {value!r}"
        )
    if len(value) > 256:
        raise click.BadParameter(
            f"Email exceeds 256 characters (got {len(value)})"
        )
    return value


def validate_type(value: str) -> str:
    """Validate an integration type string.

    Rejects control characters and injection characters; passes through otherwise.
    """
    if _CONTROL_CHARS.search(value):
        raise click.BadParameter(
            f"Type contains control characters: {value!r}"
        )
    if _DANGEROUS_CHARS.search(value):
        raise click.BadParameter(
            f"Type contains invalid characters: {value!r}"
        )
    return value
