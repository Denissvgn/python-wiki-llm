"""Supported Python API for source-adapter extraction and context payloads."""

from __future__ import annotations

from typing import Any

from .commands import context_cmd, extract_cmd
from .config import PathValidationError
from .services.contracts import (
    BOOTSTRAP_SUMMARY_SCHEMA_VERSION,
    EXTRACT_SCHEMA_VERSION,
)


class LlmWikiApiError(RuntimeError):
    """Base exception raised by the supported Python API."""


class PathPolicyError(LlmWikiApiError):
    """Raised when a source path violates the configured path policy."""


class ExtractionError(LlmWikiApiError):
    """Raised when source extraction fails."""


def extract_source(
    src_dir: str = ".",
    *,
    changed: bool = False,
    summary: bool = False,
    deep: bool = False,
    paths: list[str] | None = None,
    package: str | None = None,
    include_empty: bool = False,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> dict[str, Any]:
    """Return the stable ``llm-wiki extract`` JSON payload as a dict."""
    try:
        result = extract_cmd.build_extract_payload(
            src_dir,
            changed=changed,
            summary=summary,
            deep=deep,
            paths=paths,
            package_filter=package,
            include_empty=include_empty,
            allow_external_src=allow_external_src,
            read_only=read_only,
        )
    except PathValidationError as exc:
        raise PathPolicyError(str(exc)) from exc
    except extract_cmd.ExtractorFailureError as exc:
        raise ExtractionError(str(exc)) from exc
    except ValueError as exc:
        raise LlmWikiApiError(str(exc)) from exc
    return result.payload


def build_context(
    src_dir: str = ".",
    *,
    budget: int = 32000,
    format: str = "json",
    focus: str | list[str] = "changed",
    filters: dict | None = None,
    allow_external_src: bool = False,
    read_only: bool = True,
) -> dict[str, Any]:
    """Return a supported context payload without depending on CLI internals."""
    focus_values = _normalise_focus(focus)
    request = {
        "protocol": context_cmd.PROTOCOL_VERSION,
        "budget_tokens": budget,
        "focus": focus_values,
        "format": format,
        "filters": filters or {},
    }
    try:
        validated = context_cmd._validate_protocol_request(request)
        payload, warnings = context_cmd._build_context(
            src_dir,
            validated["budget_tokens"],
            validated["format"],
            validated["focus"],
            validated["filters"],
            emit_warnings=False,
            allow_external_src=allow_external_src,
            read_only=read_only,
        )
    except PathValidationError as exc:
        raise PathPolicyError(str(exc)) from exc
    except context_cmd.ProtocolRequestError as exc:
        if exc.field == "src_dir":
            raise ExtractionError(str(exc)) from exc
        raise LlmWikiApiError(str(exc)) from exc

    if validated["format"] == "markdown":
        return {
            "content": context_cmd._render_markdown(payload),
            "payload": payload,
            "warnings": warnings,
        }

    result = dict(payload)
    if warnings:
        result["warnings"] = warnings
    return result


def _normalise_focus(focus: str | list[str]) -> list[str]:
    if isinstance(focus, str):
        if focus == "all":
            return ["all"]
        if focus == "changed":
            return ["changed", "neighbors"]
        return [focus]
    return list(focus)


__all__ = [
    "BOOTSTRAP_SUMMARY_SCHEMA_VERSION",
    "EXTRACT_SCHEMA_VERSION",
    "ExtractionError",
    "LlmWikiApiError",
    "PathPolicyError",
    "build_context",
    "extract_source",
]
