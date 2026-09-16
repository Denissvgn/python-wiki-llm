"""Versioned task requests, exact coordinates and immutable result envelopes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from types import MappingProxyType

from .change_selection import validate_changes
from .documentation_query_builder import normalize_concept_coordinate, normalize_supplied_paths
from .workflow_profile import (
    WorkflowPolicy, WorkflowProfile, WorkflowRequestError, bounded_text,
    canonical_json, content_id, exact_fields, normalize_profile,
)

TASK_REQUEST_SCHEMA = "llm-wiki-task-request/v1"
TASK_RESULT_SCHEMA = "llm-wiki-task-context/v1"
FACETS = frozenset({"source-contract", "callers", "callees", "concept", "semantic-section",
                    "typed-relationships", "entrypoint", "dependency", "behavior"})
ANCHOR_KINDS = frozenset({"source", "symbol", "concept", "wiki"})
TASK_KINDS = frozenset({"orientation", "bug-diagnosis", "contract-change", "refactor"})
MAX_SELECTORS = 100


def coordinate(kind: str, value: object) -> str:
    text = bounded_text(value, "selector")
    if kind == "source":
        return normalize_supplied_paths([text])[0]
    if kind in {"concept", "wiki"}:
        return normalize_concept_coordinate(text)
    # File-qualified symbols preserve exact lexical owner and occurrence text.
    if ":" in text:
        path, _, symbol = text.partition(":")
        normalize_supplied_paths([path])
        bounded_text(symbol, "symbol")
    return text


def _array(value: object, field: str) -> list:
    if not isinstance(value, (list, tuple)) or len(value) > MAX_SELECTORS:
        raise WorkflowRequestError(field, f"must be an array of at most {MAX_SELECTORS} entries")
    return list(value)


def normalize_task_request(
    request: Mapping[str, Any], *, profile: WorkflowProfile | Mapping[str, Any] | None = None,
    policy: WorkflowPolicy | None = None,
) -> tuple[dict[str, Any], WorkflowProfile]:
    raw = exact_fields(request, {"schema_version", "text", "kind", "task_ref", "anchors",
                                "requirements", "changes", "options"}, "request")
    if raw.get("schema_version") != TASK_REQUEST_SCHEMA:
        raise WorkflowRequestError("schema_version", "unsupported task request schema")
    text = bounded_text(raw.get("text", ""), "text", 16384, empty=True)
    kind = raw.get("kind", "orientation")
    if not isinstance(kind, str) or kind not in TASK_KINDS:
        raise WorkflowRequestError("kind", "unsupported task kind")
    task_ref = raw.get("task_ref")
    if task_ref is not None:
        bounded_text(task_ref, "task_ref", 256)
    anchors = []
    for item in _array(raw.get("anchors", []), "anchors"):
        anchor = exact_fields(item, {"kind", "value"}, "anchor")
        anchor_kind = anchor.get("kind")
        if not isinstance(anchor_kind, str) or anchor_kind not in ANCHOR_KINDS:
            raise WorkflowRequestError("anchors", "unsupported coordinate kind")
        anchors.append({"kind": anchor_kind, "value": coordinate(anchor_kind, anchor.get("value"))})
    anchors = sorted({canonical_json(a): a for a in anchors}.values(), key=canonical_json)
    requirements, ids = [], set()
    for item in _array(raw.get("requirements", []), "requirements"):
        requirement = exact_fields(item, {"id", "facet", "selector", "criterion"}, "requirement")
        identity = bounded_text(requirement.get("id"), "requirement.id", 128)
        if identity in ids:
            raise WorkflowRequestError("requirements", "duplicate requirement ID")
        ids.add(identity)
        facet = requirement.get("facet")
        if not isinstance(facet, str) or facet not in FACETS:
            raise WorkflowRequestError("facet", "unsupported evidence facet")
        selector_kind = ("concept" if facet in {"concept", "semantic-section", "typed-relationships"}
                         else "source" if facet == "dependency" else "symbol")
        selector = coordinate(selector_kind, requirement.get("selector"))
        criterion = requirement.get("criterion", "present")
        if not isinstance(criterion, str) or criterion not in {"present", "complete"}:
            raise WorkflowRequestError("criterion", "must be present or complete")
        requirements.append({"id": identity, "facet": facet, "selector": selector, "criterion": criterion})
    requirements.sort(key=lambda item: item["id"])
    changes = validate_changes(raw["changes"]) if "changes" in raw else None
    if changes is not None and changes["mode"] == "paths":
        if len(changes["paths"]) > MAX_SELECTORS:
            raise WorkflowRequestError("changes", "too many supplied paths")
        changes["paths"] = list(normalize_supplied_paths(changes["paths"]))
    effective = normalize_profile(profile, policy=policy, overrides=raw.get("options"))
    normalized = {"schema_version": TASK_REQUEST_SCHEMA, "text": text, "kind": kind,
                  "task_ref": task_ref, "anchors": anchors, "requirements": requirements,
                  "changes": changes, "profile": effective.to_payload()}
    # The host label is attribution, not provider content identity.
    normalized["task_id"] = content_id("llm-wiki-task-intent/v1", {
        key: value for key, value in normalized.items() if key not in {"task_ref", "profile"}})
    normalized["request_id"] = content_id(TASK_REQUEST_SCHEMA, {
        key: value for key, value in normalized.items() if key != "task_ref"})
    return normalized, effective


@dataclass(frozen=True)
class TaskContext:
    """Detached canonical task output; unsuccessful budgets contain no context."""

    ok: bool
    rendered: str
    accounting: Mapping[str, Any]
    error: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "accounting", MappingProxyType(dict(self.accounting)))

    def to_payload(self) -> dict[str, Any]:
        if not self.ok:
            return {"schema_version": TASK_RESULT_SCHEMA, "ok": False,
                    "error": self.error, "accounting": dict(self.accounting)}
        return json.loads(self.rendered)

    @property
    def result_id(self) -> str | None:
        return self.to_payload().get("result_id")
