"""Explicit workflow settings constrained by immutable host read ceilings."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

from .request_json import load_request

PROFILE_SCHEMA = "llm-wiki-workflow-profile/v1"
SCOPES = ("snapshot", "selected", "full-inventory")
DEFAULTS = {
    "knowledge_mode": "auto", "prefer_fresh": True, "read_scope": "selected",
    "budget_mode": "estimated", "budget_tokens": 32000, "counter_id": None,
    "max_files": 64, "max_source_bytes": 8_388_608, "max_wiki_bytes": 8_388_608,
    "max_read_rounds": 4, "max_graph_items": 100, "max_followups": 4, "max_retries": 1,
}
HARD_LIMITS = {"budget_tokens": 1_048_576, "max_files": 1000,
               "max_source_bytes": 67_108_864, "max_wiki_bytes": 67_108_864,
               "max_read_rounds": 32, "max_graph_items": 100,
               "max_followups": 32, "max_retries": 2}


class WorkflowRequestError(ValueError):
    """A workflow request is invalid before any workspace access."""

    def __init__(self, field: str, message: str):
        self.field = field
        super().__init__(f"{field}: {message}")


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def content_id(domain: str, value: Any) -> str:
    return "sha256:" + hashlib.sha256(domain.encode("ascii") + b"\0" + canonical_json(value)).hexdigest()


def bounded_int(value: object, field: str, maximum: int, *, minimum: int = 1) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise WorkflowRequestError(field, f"must be an integer from {minimum} to {maximum}")
    return value


def bounded_text(value: object, field: str, maximum: int = 4096, *, empty: bool = False) -> str:
    if not isinstance(value, str) or (not empty and not value.strip()):
        raise WorkflowRequestError(field, "must be text" if empty else "must be nonempty text")
    try:
        length = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise WorkflowRequestError(field, "must be valid UTF-8") from exc
    if length > maximum or "\x00" in value:
        raise WorkflowRequestError(field, f"must not exceed {maximum} UTF-8 bytes or contain NUL")
    return value


def exact_fields(value: object, allowed: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise WorkflowRequestError(field, "must be an object with string keys")
    if set(value) - allowed:
        raise WorkflowRequestError(field, "contains an unknown field")
    return dict(value)


def _settings(value: object) -> dict[str, Any]:
    result = exact_fields(value, set(DEFAULTS), "profile")
    choices = {"knowledge_mode": ("off", "auto", "required"),
               "read_scope": SCOPES, "budget_mode": ("exact", "estimated")}
    for field, selected in result.items():
        if field in choices:
            if not isinstance(selected, str) or selected not in choices[field]:
                raise WorkflowRequestError(field, "has an unsupported value")
        elif field == "prefer_fresh":
            if type(selected) is not bool:
                raise WorkflowRequestError(field, "must be a boolean")
        elif field == "counter_id":
            if selected is not None:
                bounded_text(selected, field, 512)
        else:
            bounded_int(selected, field, HARD_LIMITS[field],
                        minimum=0 if field in {"max_followups", "max_retries"} else 1)
    return result


@dataclass(frozen=True)
class WorkflowPolicy:
    """Trusted host ceilings; profiles and task data can only narrow these."""

    read_scope: str = "selected"
    budget_tokens: int = 32000
    max_files: int = 128
    max_source_bytes: int = 16_777_216
    max_wiki_bytes: int = 16_777_216
    max_read_rounds: int = 8
    max_graph_items: int = 100
    max_followups: int = 8
    max_retries: int = 1

    def __post_init__(self):
        _settings(self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        return {field.name: getattr(self, field.name) for field in fields(self)}


@dataclass(frozen=True)
class WorkflowProfile:
    """Immutable explicit settings; each payload access returns detached data."""

    _bytes: bytes

    def __post_init__(self):
        try:
            payload = json.loads(self._bytes)
            raw = exact_fields(payload, {"schema_version", "settings"}, "profile")
            if set(raw) != {"schema_version", "settings"} or raw["schema_version"] != PROFILE_SCHEMA:
                raise ValueError("unsupported profile schema")
            if set(_settings(raw["settings"])) != set(DEFAULTS):
                raise ValueError("profile must contain normalized settings")
            if canonical_json(payload) != self._bytes:
                raise ValueError("profile must be canonical")
        except (ValueError, TypeError, KeyError) as exc:
            raise WorkflowRequestError("profile", "must contain normalized canonical settings") from exc

    @property
    def profile_id(self) -> str:
        return content_id(PROFILE_SCHEMA, self.to_payload())

    def to_payload(self) -> dict[str, Any]:
        return json.loads(self._bytes)

    @property
    def settings(self) -> dict[str, Any]:
        return self.to_payload()["settings"]


def normalize_profile(
    profile: WorkflowProfile | Mapping[str, Any] | None = None, *,
    policy: WorkflowPolicy | None = None, overrides: Mapping[str, Any] | None = None,
) -> WorkflowProfile:
    if policy is None:
        policy = WorkflowPolicy()
    if not isinstance(policy, WorkflowPolicy):
        raise WorkflowRequestError("policy", "must be a trusted WorkflowPolicy")
    if isinstance(profile, WorkflowProfile):
        raw = profile.to_payload()
    elif profile is None:
        raw = {"schema_version": PROFILE_SCHEMA, "settings": {}}
    else:
        raw = exact_fields(profile, {"schema_version", "settings"}, "profile")
    if raw.get("schema_version") != PROFILE_SCHEMA:
        raise WorkflowRequestError("schema_version", "unsupported profile schema")
    explicit = _settings(raw.get("settings", {}))
    requested = _settings({} if overrides is None else overrides)
    settings = {**DEFAULTS, **explicit, **requested}
    # Omitted defaults shrink to host maxima; explicit attempts to widen fail.
    for key, ceiling in policy.to_payload().items():
        if key == "read_scope":
            too_large = SCOPES.index(settings[key]) > SCOPES.index(ceiling)
        else:
            too_large = settings[key] > ceiling
        if too_large:
            if key in explicit or key in requested:
                raise WorkflowRequestError(key, "exceeds the host policy")
            settings[key] = ceiling
    return WorkflowProfile(canonical_json({"schema_version": PROFILE_SCHEMA, "settings": settings}))


def load_profile(path: str | Path, *, policy: WorkflowPolicy | None = None) -> WorkflowProfile:
    """Load only the explicitly named profile file; no ambient discovery."""
    return normalize_profile(load_request(str(path)), policy=policy)
