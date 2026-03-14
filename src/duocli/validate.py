from __future__ import annotations

import re

import click


_IKEY_PATTERN = re.compile(r"^DI[A-Z0-9]{18,20}$")
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
