"""Shared best-effort redaction for credential-like text.

The patterns in this module intentionally combine the credential matchers used
by prompt generation, documentation calibration, OCI dispatch, and public
knowledge projection.  Pattern matching is a safety net, not proof that text is
free of secrets.
"""

from __future__ import annotations

import re
from collections.abc import Callable


REDACTED_CREDENTIAL = "[REDACTED:credential]"

SENSITIVE_KEYS = frozenset(
    {
        "access_token",
        "api_key",
        "apikey",
        "auth_token",
        "authorization",
        "client_secret",
        "cookie",
        "credentials",
        "docker_auth_config",
        "environment",
        "headers",
        "password",
        "provider_credentials",
        "registry_auth",
        "secret",
        "token",
    }
)
SENSITIVE_KEY_RE = re.compile(
    r"(?:password|passwd|secret|credential|authorization|api[-_]?key|"
    r"access[-_]?token|private[-_]?key|environment|env(?:iron)?\b|"
    r"(?:repository[-_])?remote(?:[-_](?:url|uri))?)",
    re.IGNORECASE,
)
PRIVATE_KEY_BLOCK_RE = re.compile(
    r"-----BEGIN (?P<label>(?:[A-Z0-9][A-Z0-9 -]* )?PRIVATE KEY(?: BLOCK)?)-----"
    r".*?"
    r"-----END (?P=label)-----",
    re.IGNORECASE | re.DOTALL,
)
SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"""
    (?P<prefix>
        (?<![A-Za-z0-9_])
        ["']?
        (?:[A-Za-z0-9]+[_-])*
        (?:
            api[_-]?key
            | access[_-]?token
            | auth(?:entication|orization)?[_-]?(?:key|token)?
            | bearer[_-]?token
            | client[_-]?secret
            | credentials?
            | password
            | passwd
            | private[_-]?key
            | pwd
            | secret(?:[_-]?key)?
            | token
        )
        ["']?
        \s*(?:=|:)\s*
    )
    (?!["']?\[REDACTED:)
    (?:
        "(?P<double_quoted>[^"\r\n]{1,4096})"
        |
        '(?P<single_quoted>[^'\r\n]{1,4096})'
        |
        (?P<bare>[^\s,;}\]\r\n]{1,4096})
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
SENSITIVE_NATURAL_LANGUAGE_RE = re.compile(
    r"""
    (?P<prefix>
        (?<![A-Za-z0-9_])
        (?:
            api[ _-]?key
            | access[ _-]?token
            | auth(?:entication|orization)?[ _-]?(?:key|token)?
            | bearer[ _-]?token
            | client[ _-]?secret
            | credentials?
            | password
            | passwd
            | private[ _-]?key
            | pwd
            | secret(?:[ _-]?key)?
            | token
        )
        \s+(?:is|equals?|was)\s+
    )
    (?!["']?\[REDACTED:)
    (?!
        (?:configured|invalid|missing|optional|required|redacted|sensitive|unset|valid)
        \b
    )
    (?:
        "(?P<double_quoted>[^"\r\n]{6,4096})"
        |
        '(?P<single_quoted>[^'\r\n]{6,4096})'
        |
        (?P<bare>[^\s,;}\]\r\n]{6,4096})
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
_REDACTION_SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"""
    (?P<prefix>
        (?<![A-Za-z0-9_])
        ["']?
        (?:[A-Za-z0-9]+[_-])*
        (?:
            api[_-]?key
            | access[_-]?token
            | auth(?:entication|orization)?[_-]?(?:key|token)?
            | bearer[_-]?token
            | client[_-]?secret
            | credentials?
            | password
            | passwd
            | private[_-]?key
            | pwd
            | secret(?:[_-]?key)?
            | token
        )
        ["']?
        \s*(?:=|:)\s*
    )
    (?:
        "(?P<double_quoted>[^"\r\n]{1,4096})"
        |
        '(?P<single_quoted>[^'\r\n]{1,4096})'
        |
        (?P<bare>[^\s,;}\r\n]{1,4096})
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
_REDACTION_SENSITIVE_NATURAL_LANGUAGE_RE = re.compile(
    r"""
    (?P<prefix>
        (?<![A-Za-z0-9_])
        (?:
            api[ _-]?key
            | access[ _-]?token
            | auth(?:entication|orization)?[ _-]?(?:key|token)?
            | bearer[ _-]?token
            | client[ _-]?secret
            | credentials?
            | password
            | passwd
            | private[ _-]?key
            | pwd
            | secret(?:[ _-]?key)?
            | token
        )
        \s+(?:is|equals?|was)\s+
    )
    (?!
        (?:configured|invalid|missing|optional|required|redacted|sensitive|unset|valid)
        \b
    )
    (?:
        "(?P<double_quoted>[^"\r\n]{6,4096})"
        |
        '(?P<single_quoted>[^'\r\n]{6,4096})'
        |
        (?P<bare>[^\s,;}\r\n]{6,4096})
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)
URI_USERINFO_RE = re.compile(
    r"(?P<scheme>\b[a-z][a-z0-9+.-]{1,31}://)"
    r"(?P<userinfo>[^/@\s:]+:[^/@\s]+)@",
    re.IGNORECASE,
)
PROJECTION_URI_USERINFO_RE = re.compile(
    r"[A-Za-z][A-Za-z0-9+.-]*://[^/\s@]+(?::[^/\s@]*)?@"
)
_REDACTABLE_URI_USERINFO_RE = re.compile(
    r"(?P<scheme>\b[a-z][a-z0-9+.-]{1,31}://)"
    r"(?!\[REDACTED:)(?P<userinfo>[^/@\s:]+:[^/@\s]+)@",
    re.IGNORECASE,
)
_REDACTABLE_PROJECTION_URI_USERINFO_RE = re.compile(
    r"(?P<scheme>[A-Za-z][A-Za-z0-9+.-]*://)"
    r"(?!\[REDACTED:)[^/\s@]+(?::[^/\s@]*)?@"
)
COMMON_TOKEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "bearer-token",
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    ),
    (
        "authorization-token",
        re.compile(r"(?i)\b(?:Basic|ApiKey|Token)\s+[A-Za-z0-9._~+/=-]{8,}"),
    ),
    (
        "github-token",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{20,255}"
            r"|github_pat_[A-Za-z0-9_]{22,255})\b"
        ),
    ),
    (
        "gitlab-token",
        re.compile(r"\bglpat-[A-Za-z0-9_-]{20,255}\b"),
    ),
    (
        "slack-token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,255}\b"),
    ),
    (
        "aws-access-key",
        re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    ),
    (
        "google-api-key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ),
    (
        "provider-token",
        re.compile(
            r"\b(?:sk-(?:proj-)?[A-Za-z0-9_-]{20,255}"
            r"|(?:sk|rk)_(?:live|test)_[A-Za-z0-9]{16,255}"
            r"|npm_[A-Za-z0-9]{32,255}"
            r"|pypi-[A-Za-z0-9_-]{32,255})\b"
        ),
    ),
    (
        "jwt",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{8,}\."
            r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
        ),
    ),
)
LIKELY_SECRET_RE = re.compile(
    r"(?:^|\s)(?:bearer\s+\S+|sk-[A-Za-z0-9_-]{12,}|"
    r"gh[pousr]_[A-Za-z0-9]{12,}|xox[baprs]-[A-Za-z0-9-]{12,}|"
    r"AIza[A-Za-z0-9_-]{12,})",
    re.IGNORECASE,
)
CREDENTIAL_VALUE_RE = re.compile(
    r"(?:\bBearer\s+[A-Za-z0-9._~+/=-]+|"
    r"\b(?:sk|ghp|github_pat)[-_][A-Za-z0-9_-]{8,}|"
    r"\bxox[a-z]-[A-Za-z0-9-]{8,}|"
    r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\."
    r"[A-Za-z0-9_-]{8,}|"
    r"\bAKIA[0-9A-Z]{12,})",
    re.IGNORECASE,
)
_AUTHORIZATION_VALUE_RE = re.compile(
    r"(?i)\b(?:Bearer|Basic|ApiKey|Token)\s+\S+"
)


def _assignment_replacement(match: re.Match[str]) -> str:
    sensitive_value = (
        match.group("double_quoted")
        or match.group("single_quoted")
        or match.group("bare")
    )
    if sensitive_value == REDACTED_CREDENTIAL:
        return match.group(0)
    quote = (
        '"'
        if match.group("double_quoted") is not None
        else "'"
        if match.group("single_quoted") is not None
        else ""
    )
    return str(match.group("prefix")) + quote + REDACTED_CREDENTIAL + quote


def _likely_secret_replacement(match: re.Match[str]) -> str:
    value = match.group(0)
    leading_length = len(value) - len(value.lstrip())
    return value[:leading_length] + REDACTED_CREDENTIAL


def redact_credentials(text: str) -> tuple[str, int]:
    """Replace credential-like values in *text* and return the match count.

    The count describes pattern matches, not a verified number of secrets.
    Replacements are idempotent and preserve assignment prefixes, quotes, URI
    schemes, and leading whitespace where the source matcher includes them.
    """

    redacted = text
    count = 0

    def apply(
        pattern: re.Pattern[str],
        replacement: str | Callable[[re.Match[str]], str],
    ) -> None:
        nonlocal redacted, count
        if isinstance(replacement, str):
            redacted, matches = pattern.subn(replacement, redacted)
        else:
            matches = 0

            def counted_replacement(match: re.Match[str]) -> str:
                nonlocal matches
                value = replacement(match)
                if value != match.group(0):
                    matches += 1
                return value

            redacted = pattern.sub(counted_replacement, redacted)
        count += matches

    apply(PRIVATE_KEY_BLOCK_RE, REDACTED_CREDENTIAL)
    for _kind, pattern in COMMON_TOKEN_PATTERNS:
        apply(pattern, REDACTED_CREDENTIAL)
    apply(_AUTHORIZATION_VALUE_RE, REDACTED_CREDENTIAL)
    apply(CREDENTIAL_VALUE_RE, REDACTED_CREDENTIAL)
    apply(LIKELY_SECRET_RE, _likely_secret_replacement)
    apply(_REDACTION_SENSITIVE_ASSIGNMENT_RE, _assignment_replacement)
    apply(_REDACTION_SENSITIVE_NATURAL_LANGUAGE_RE, _assignment_replacement)
    apply(
        _REDACTABLE_URI_USERINFO_RE,
        lambda match: str(match.group("scheme")) + REDACTED_CREDENTIAL + "@",
    )
    apply(
        _REDACTABLE_PROJECTION_URI_USERINFO_RE,
        lambda match: str(match.group("scheme")) + REDACTED_CREDENTIAL + "@",
    )
    return redacted, count


__all__ = ["redact_credentials"]
