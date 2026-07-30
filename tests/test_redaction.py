"""Credential redaction contract tests."""

from __future__ import annotations

import pytest

from llm_wiki_cli.services.redaction import redact_credentials


@pytest.mark.parametrize(
    "value",
    [
        "Bearer bearer_value_123456",
        "Basic YWxhZGRpbjpvcGVuc2VzYW1l",
        "ghp_abcdefghijklmnopqrstuvwxyz",
        "github_pat_abcdefghijklmnopqrstuvwxyz",
        "glpat-abcdefghijklmnopqrstuvwxyz",
        "xoxb-1234567890-abcdefghijkl",
        "AKIA1234567890ABCDEF",
        "AIza1234567890abcdefghijklmnopqrstuv",
        "sk-abcdefghijklmnopqrstuvwxyz",
        "sk_live_abcdefghijklmnop",
        "npm_abcdefghijklmnopqrstuvwxyz123456",
        "pypi-abcdefghijklmnopqrstuvwxyz123456",
        "eyJabcdefgh.eyJijklmnop.qrstuvwxyz",
        "https://user:password@example.invalid/private",
        "https://opaque-userinfo@example.invalid/private",
        "API_KEY=unstructured-but-sensitive",
        "password is unstructured-but-sensitive",
        (
            "-----BEGIN PRIVATE KEY-----\n"
            "private-material\n"
            "-----END PRIVATE KEY-----"
        ),
    ],
)
def test_redact_credentials_covers_shared_matcher_union(value: str):
    redacted, count = redact_credentials(f"before {value} after")

    assert value not in redacted
    assert "[REDACTED:credential]" in redacted
    assert count == 1


def test_redact_credentials_counts_values_and_is_idempotent():
    source = (
        "Authorization: Bearer bearer_value_123456\n"
        "GITHUB_TOKEN=ghp_abcdefghijklmnopqrstuvwxyz\n"
        "url=https://user:password@example.invalid/private\n"
    )

    redacted, count = redact_credentials(source)
    second_pass, second_count = redact_credentials(redacted)

    assert count == 3
    assert second_count == 0
    assert second_pass == redacted


@pytest.mark.parametrize(
    ("source", "secret"),
    [
        ("+Authorization: Bearer abc", "Bearer abc"),
        ("+Authorization is Bearer a.b-c", "Bearer a.b-c"),
        ("+Authorization: Basic x:y", "Basic x:y"),
    ],
)
def test_authorization_scheme_is_redacted_before_assignment_matcher(
    source: str, secret: str
):
    redacted, count = redact_credentials(source)

    assert secret not in redacted
    assert redacted.count("[REDACTED:credential]") == 1
    assert count == 1


@pytest.mark.parametrize(
    "source",
    [
        "password=https://alice:hunter2@example.invalid/repo",
        "password is https://alice:hunter2@example.invalid/repo",
    ],
)
def test_credential_uri_inside_sensitive_phrase_is_counted_once(source: str):
    redacted, count = redact_credentials(source)

    expected_prefix = "password=" if "=" in source else "password is "
    assert redacted == expected_prefix + "[REDACTED:credential]"
    assert "alice" not in redacted
    assert "hunter2" not in redacted
    assert count == 1
    assert redact_credentials(redacted) == (redacted, 0)


@pytest.mark.parametrize(
    "source",
    [
        "password=before[REDACTED:fake]hunter2",
        "password=[REDACTED:credential]hunter2",
        "password is before[REDACTED:fake]hunter2",
        "password is [REDACTED:credential]hunter2",
    ],
)
def test_marker_text_cannot_disable_sensitive_phrase_redaction(source: str):
    assert redact_credentials(source) == (
        source.split("password", 1)[0]
        + ("password is " if "password is " in source else "password=")
        + "[REDACTED:credential]",
        1,
    )


@pytest.mark.parametrize(
    "source",
    [
        "password=[REDACTED:credential]",
        "password is [REDACTED:credential]",
    ],
)
def test_exact_generated_sensitive_value_marker_is_idempotent(source: str):
    assert redact_credentials(source) == (source, 0)


def test_redact_credentials_does_not_claim_ordinary_status_text_is_secret():
    source = "The API key is configured but unavailable to this process."

    assert redact_credentials(source) == (source, 0)
