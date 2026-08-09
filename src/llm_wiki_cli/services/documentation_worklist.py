"""Deterministic semantic worklists for standalone documentation runs.

This module deliberately has no dependency on the documentation-run lifecycle.
It turns an already-materialized canonical wiki plus bounded deterministic
evidence into a portable, stable worklist that a later packet renderer can
consume.  It performs no source extraction, agent invocation, or file writes.

Imported semantic-page classification is intentionally separate from grounding:
``candidate_reuse`` describes reusable, compatible prose whose grounding was
confirmed; ``needs_grounding`` remains reuse-eligible but is not publishable
evidence yet.  Callers must never infer grounding from reuse eligibility alone.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

from .io import read_md
from .markdown_sections import GENERATED_INDEX_INTROS
from .validation import (
    nonnegative_int_or_none,
    normalize_legacy_portable_relative_path,
    require_nonnegative_int,
    require_positive_int,
)
from .wiki_surface import (
    PageKind,
    WikiSurfacePage,
    collect_wiki_pages,
    is_safe_page_id,
)
from .wiki_surface_index import SURFACE_INDEX_FILENAME


DOCUMENTATION_WORKLIST_SCHEMA_VERSION = "llm-wiki-documentation-worklist/v1"
IMPORTED_PAGE_CLASSIFICATIONS = frozenset(
    {
        "candidate_reuse",
        "needs_grounding",
        "needs_enhancement",
        "incompatible",
    }
)
GROUNDING_STATUSES = frozenset({"grounded", "ungrounded", "unknown"})
WORK_ITEM_STATUSES = frozenset({"open", "reused", "deferred"})
WORK_ITEM_PRIORITIES = ("P0", "P1", "P2")

_PRIORITY_ORDER = {
    priority: index for index, priority in enumerate(WORK_ITEM_PRIORITIES)
}
_CATEGORY_ORDER = {
    "landing_context": 0,
    "flow_behavior": 1,
    "architecture_notes": 2,
    "user_profile": 3,
    "semantic_page": 4,
    "imported_semantic_page": 5,
    "unsupported_source": 6,
}
_CORE_ARCHITECTURE_PAGES = {
    "api-contracts.md": "API contract notes",
    "dependencies.md": "Dependency architecture notes",
    "load-order.md": "Load-order architecture notes",
}
_PLACEHOLDER_PHRASES = (
    "_Auto-generated from `",
    "Replace this placeholder",
    "Describe what this flow does",
)
_USER_PROFILE_DEFERRED_CATEGORIES = frozenset(
    {
        "generated_reference_placeholder",
        "user_docs_missing_examples",
    }
)
_USER_PROFILE_INDEX_CATEGORIES = frozenset(
    {
        "default_site_name",
        "missing_user_index",
        "raw_generated_inventory",
        "user_index_too_large",
    }
)
_IMPORT_CLASSIFICATION_ORDER = {
    "candidate_reuse": 0,
    "needs_grounding": 1,
    "needs_enhancement": 2,
    "incompatible": 3,
}
_GROUNDING_STATUS_ORDER = {"grounded": 0, "unknown": 1, "ungrounded": 2}
_PRIMARY_FLOW_CATEGORIES = frozenset(
    {
        "cli",
        "command",
        "consumer",
        "endpoint",
        "event",
        "grpc",
        "handler",
        "http",
        "job",
        "mcp",
        "message",
        "process",
        "producer",
        "route",
        "rpc",
        "task",
        "websocket",
        "worker",
    }
)
_KNOWN_PAGE_DIRS = (
    "guides",
    "flows",
    "workflows",
    "modules",
    "entities",
    "infrastructure",
)
_MARKDOWN_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_MARKDOWN_LINK_RE = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_SOURCE_PATH_RE = re.compile(r"\*\*Path:\*\*\s+`([^`]+)`")


class DocumentationWorklistError(ValueError):
    """Raised when deterministic worklist inputs are invalid."""


@dataclass(frozen=True)
class DocumentationWorkItem:
    """One stable semantic-work unit or explicitly accounted reuse/deferral."""

    work_id: str
    priority: str
    category: str
    title: str
    canonical_path: str | None
    source_path: str | None
    status: str
    signals: tuple[str, ...]
    suggested_context: tuple[str, ...]
    acceptance_checks: tuple[str, ...]
    rank_score: int = 0
    imported_classification: str | None = None
    reuse_eligible: bool = False
    grounding_status: str = "unknown"
    deferred: bool = False
    deferral_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return {
            "id": self.work_id,
            "priority": self.priority,
            "category": self.category,
            "title": self.title,
            "canonical_path": self.canonical_path,
            "source_path": self.source_path,
            "status": self.status,
            "signals": list(self.signals),
            "suggested_context": list(self.suggested_context),
            "acceptance_checks": list(self.acceptance_checks),
            "rank_score": self.rank_score,
            "imported_classification": self.imported_classification,
            "reuse_eligible": self.reuse_eligible,
            "grounding_status": self.grounding_status,
            "deferred": self.deferred,
            "deferral_reason": self.deferral_reason,
        }


@dataclass(frozen=True)
class DocumentationWorklist:
    """Stable semantic worklist and deterministic coverage summary."""

    items: tuple[DocumentationWorkItem, ...]
    p1_budget: int
    max_context_entries: int
    max_acceptance_checks: int
    schema_version: str = DOCUMENTATION_WORKLIST_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        """Return the portable worklist contract."""
        counts = {
            "total": len(self.items),
            "by_priority": {
                priority: sum(item.priority == priority for item in self.items)
                for priority in WORK_ITEM_PRIORITIES
            },
            "by_status": {
                status: sum(item.status == status for item in self.items)
                for status in sorted(WORK_ITEM_STATUSES)
            },
            "deferred": sum(item.deferred for item in self.items),
        }
        return {
            "schema_version": self.schema_version,
            "policy": {
                "p1_budget": self.p1_budget,
                "max_context_entries": self.max_context_entries,
                "max_acceptance_checks": self.max_acceptance_checks,
            },
            "counts": counts,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass
class _Candidate:
    identity: str
    category: str
    title: str
    canonical_path: str | None
    source_path: str | None
    priority: str
    rank_score: int = 0
    budget_candidate: bool = False
    signals: set[str] = field(default_factory=set)
    suggested_context: set[str] = field(default_factory=set)
    acceptance_checks: set[str] = field(default_factory=set)
    imported_classification: str | None = None
    reuse_eligible: bool = False
    grounding_status: str = "unknown"
    requested_defer: bool = False
    deferral_reason: str | None = None


def build_documentation_worklist(
    wiki_dir: str | Path,
    *,
    imported_pages: Iterable[Mapping[str, Any]] | None = None,
    unsupported_sources: Mapping[str, Mapping[str, Any]] | None = None,
    user_profile_findings: Iterable[Mapping[str, Any]] | None = None,
    dependency_metrics: Mapping[str, Any] | None = None,
    entrypoint_evidence: Iterable[Mapping[str, Any]] | None = None,
    source_inventory: Mapping[str, Mapping[str, Any]] | None = None,
    surface_index: Mapping[str, Any] | None = None,
    p1_budget: int = 30,
    max_context_entries: int = 5,
    max_acceptance_checks: int = 5,
) -> DocumentationWorklist:
    """Build a deterministic semantic worklist from bounded evidence.

    ``dependency_metrics`` accepts either the direct
    ``dependency_metrics(...)`` result or a containing analysis mapping.
    ``entrypoint_evidence`` accepts surface-index flow records or extractor
    entry-point records.  Both are optional: their absence lowers ranking
    confidence but never turns an unknown into a completion claim.
    """
    _require_non_negative_int(p1_budget, "p1_budget")
    _require_positive_int(max_context_entries, "max_context_entries")
    _require_positive_int(max_acceptance_checks, "max_acceptance_checks")

    wiki = Path(wiki_dir).expanduser()
    if not wiki.is_dir():
        raise DocumentationWorklistError(f"Wiki directory does not exist: {wiki}")

    pages = collect_wiki_pages(wiki)
    pages_by_path = {page.relative_path: page for page in pages}
    contents = {page.relative_path: read_md(page.path) for page in pages}
    effective_surface_index = dict(surface_index or _read_surface_index(wiki))
    surface_pages = _surface_page_map(effective_surface_index)
    source_by_page = {
        path: _normalise_relative_path(record.get("source_path"))
        for path, record in surface_pages.items()
    }
    for page in pages:
        if source_by_page.get(page.relative_path) is None:
            source_by_page[page.relative_path] = _source_path_from_page(
                contents[page.relative_path]
            )

    metric_map, ranked_sources = _normalise_dependency_metrics(dependency_metrics)
    entrypoints = _normalise_entrypoints(
        list(effective_surface_index.get("flows") or [])
        + list(entrypoint_evidence or [])
    )
    entrypoint_sources = {
        evidence["source_path"]
        for evidence in entrypoints.values()
        if evidence.get("source_path")
    }
    rank_index = {path: index for index, path in enumerate(ranked_sources)}

    candidates: dict[str, _Candidate] = {}
    for page in pages:
        content = contents[page.relative_path]
        source_path = source_by_page.get(page.relative_path)
        score = _centrality_score(
            source_path,
            metric_map,
            rank_index,
            entrypoint_related=source_path in entrypoint_sources,
        )
        if page.kind is PageKind.INDEX and _index_needs_context(content):
            _add_page_candidate(
                candidates,
                page,
                source_path=source_path,
                category="landing_context",
                priority="P0",
                title="Explain the project and provide a purposeful landing path",
                signal="generic_landing_context",
                acceptance="Replace generic landing prose with grounded project purpose and reading paths.",
                rank_score=score,
            )
        elif page.kind is PageKind.FLOWS and _section_needs_semantics(
            content, "Behavior"
        ):
            flow_evidence = entrypoints.get(page.page_id, {})
            flow_priority = _flow_priority(page.page_id, flow_evidence)
            candidate = _add_page_candidate(
                candidates,
                page,
                source_path=source_path,
                category="flow_behavior",
                priority=flow_priority,
                title=f"Document behavior for {page.page_id}",
                signal="missing_or_placeholder_flow_behavior",
                acceptance="Write evidence-backed trigger, behavior, side effects, outputs, and explicit unknowns in ## Behavior.",
                rank_score=score,
                context=_flow_context(page.page_id, source_path, entrypoints),
            )
            if flow_priority == "P2":
                candidate.requested_defer = True
                candidate.deferral_reason = (
                    "The extracted flow is an ordinary reference/API symbol without "
                    "boundary-workflow evidence; retain it as explicit remainder."
                )
        elif (
            page.relative_path in _CORE_ARCHITECTURE_PAGES
            and _section_needs_semantics(content, "Notes")
        ):
            _add_page_candidate(
                candidates,
                page,
                source_path=source_path,
                category="architecture_notes",
                priority="P0",
                title=f"Complete {_CORE_ARCHITECTURE_PAGES[page.relative_path]}",
                signal="missing_or_placeholder_architecture_notes",
                acceptance="Replace the ## Notes placeholder with source-backed rationale, caveats, or an explicit evidence limitation.",
                rank_score=score,
            )

        if page.kind in {PageKind.MODULES, PageKind.ENTITIES}:
            description = _section_body(content, "Description")
            weak_signal = None
            if _is_placeholder_text(description):
                weak_signal = "placeholder_semantic_prose"
            elif _is_copied_docstring_only(
                page,
                description,
                source_path=source_path,
                source_inventory=source_inventory or {},
            ):
                weak_signal = "copied_docstring_only_prose"
            if weak_signal:
                candidate = _add_page_candidate(
                    candidates,
                    page,
                    source_path=source_path,
                    category="semantic_page",
                    priority="P1",
                    title=f"Explain the role of {page.page_id}",
                    signal=weak_signal,
                    acceptance="Replace weak description prose with a grounded responsibility, collaborators, and relevant runtime role.",
                    rank_score=score,
                )
                candidate.budget_candidate = True
                candidate.suggested_context.update(
                    _semantic_page_context(page.relative_path, source_path)
                )

    _add_missing_flow_candidates(candidates, pages_by_path, entrypoints)
    _add_imported_page_candidates(
        candidates,
        wiki,
        pages_by_path,
        imported_pages or (),
        source_by_page=source_by_page,
        metric_map=metric_map,
        rank_index=rank_index,
        entrypoint_sources=entrypoint_sources,
    )
    _add_user_profile_candidates(
        candidates,
        user_profile_findings or (),
        pages_by_path=pages_by_path,
    )
    _add_unsupported_source_candidates(candidates, unsupported_sources or {})
    _apply_p1_budget(candidates.values(), p1_budget)

    items = tuple(
        _candidate_to_item(
            candidate,
            max_context_entries=max_context_entries,
            max_acceptance_checks=max_acceptance_checks,
        )
        for candidate in sorted(candidates.values(), key=_candidate_sort_key)
    )
    return DocumentationWorklist(
        items=items,
        p1_budget=p1_budget,
        max_context_entries=max_context_entries,
        max_acceptance_checks=max_acceptance_checks,
    )


def classify_imported_semantic_page(
    wiki_dir: str | Path,
    record: Mapping[str, Any],
) -> tuple[str, bool, str]:
    """Return ``(classification, reuse_eligible, grounding_status)``.

    This helper is public so snapshot-adoption and packet tests can share the
    exact classifier without reconstructing the full worklist.
    """
    wiki = Path(wiki_dir).expanduser()
    canonical_pages = {page.relative_path for page in collect_wiki_pages(wiki)}
    return _classify_imported_semantic_page(wiki, record, canonical_pages)


def _classify_imported_semantic_page(
    wiki: Path,
    record: Mapping[str, Any],
    canonical_pages: set[str],
) -> tuple[str, bool, str]:
    canonical_path = _canonical_import_path(record)
    grounding_status = _grounding_status(record)
    if not _import_record_compatible(record) or canonical_path is None:
        return "incompatible", False, grounding_status
    if canonical_path not in canonical_pages:
        return "incompatible", False, grounding_status
    page_path = wiki / PurePosixPath(canonical_path)
    try:
        page_path.resolve().relative_to(wiki.resolve())
    except (OSError, ValueError):
        return "incompatible", False, grounding_status
    if not page_path.is_file():
        return "incompatible", False, grounding_status

    content = read_md(page_path)
    if _imported_page_needs_enhancement(canonical_path, content):
        return "needs_enhancement", False, grounding_status
    if grounding_status != "grounded":
        return "needs_grounding", True, grounding_status
    return "candidate_reuse", True, grounding_status


def _require_non_negative_int(value: object, field_name: str) -> None:
    require_nonnegative_int(
        value,
        error=DocumentationWorklistError(
            f"{field_name} must be a non-negative integer."
        ),
    )


def _require_positive_int(value: object, field_name: str) -> None:
    require_positive_int(
        value,
        invalid_error=DocumentationWorklistError(
            f"{field_name} must be a positive integer."
        ),
    )


def _read_surface_index(wiki: Path) -> Mapping[str, Any]:
    path = wiki / SURFACE_INDEX_FILENAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _surface_page_map(surface_index: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for raw in surface_index.get("pages") or []:
        if not isinstance(raw, Mapping):
            continue
        canonical_path = _normalise_relative_path(raw.get("canonical_path"))
        if canonical_path:
            result[canonical_path] = raw
    return result


def _normalise_relative_path(value: object) -> str | None:
    return normalize_legacy_portable_relative_path(
        value,
        reject_dot_prefixed_absolute=True,
    )


def _source_path_from_page(content: str) -> str | None:
    match = _SOURCE_PATH_RE.search(content)
    return _normalise_relative_path(match.group(1)) if match else None


def _normalise_dependency_metrics(
    evidence: Mapping[str, Any] | None,
) -> tuple[dict[str, dict[str, int]], list[str]]:
    if not isinstance(evidence, Mapping):
        return {}, []
    payload: Mapping[str, Any] = evidence
    nested = payload.get("metrics")
    if isinstance(nested, Mapping) and "most_depended_on" in nested:
        payload = nested
    raw_metrics = payload.get("metrics")
    metrics: dict[str, dict[str, int]] = {}
    if isinstance(raw_metrics, Mapping):
        for raw_path, raw_counts in raw_metrics.items():
            path = _normalise_relative_path(str(raw_path))
            if path is None or not isinstance(raw_counts, Mapping):
                continue
            metrics[path] = {
                "fan_in": _safe_non_negative_int(raw_counts.get("fan_in")),
                "fan_out": _safe_non_negative_int(raw_counts.get("fan_out")),
                "cycle": int(bool(raw_counts.get("cycle"))),
            }
    ranking = []
    for raw_path in payload.get("most_depended_on") or []:
        path = _normalise_relative_path(raw_path)
        if path and path not in ranking:
            ranking.append(path)
    return metrics, ranking


def _safe_non_negative_int(value: object) -> int:
    parsed = nonnegative_int_or_none(value)
    return 0 if parsed is None else parsed


def _normalise_entrypoints(
    evidence: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for raw in evidence:
        if not isinstance(raw, Mapping):
            continue
        flow_id = raw.get("id") or raw.get("flow_id")
        if not isinstance(flow_id, str) or not flow_id.strip():
            continue
        entry = raw.get("entry_point")
        entry_mapping = entry if isinstance(entry, Mapping) else {}
        source_path = _normalise_relative_path(
            raw.get("source_path")
            or raw.get("file")
            or entry_mapping.get("source_path")
            or entry_mapping.get("file")
        )
        boundary_count = raw.get("boundary_effect_count")
        boundary_effects = raw.get("boundary_effects")
        if (
            boundary_count is None
            and isinstance(boundary_effects, Sequence)
            and not isinstance(boundary_effects, (str, bytes))
        ):
            boundary_count = len(boundary_effects)
        normalized = {
            "id": flow_id.strip(),
            "category": str(raw.get("category") or flow_id.split("-", 1)[0]),
            "source_path": source_path,
            "symbol": raw.get("symbol") or entry_mapping.get("symbol"),
            "boundary_effect_count": _safe_non_negative_int(boundary_count),
        }
        previous = result.get(flow_id.strip())
        if previous is None or _entrypoint_completeness(
            normalized
        ) > _entrypoint_completeness(previous):
            result[flow_id.strip()] = normalized
    return result


def _entrypoint_completeness(record: Mapping[str, Any]) -> tuple[int, int]:
    return (
        sum(bool(record.get(key)) for key in ("source_path", "symbol", "category")),
        _safe_non_negative_int(record.get("boundary_effect_count")),
    )


def _centrality_score(
    source_path: str | None,
    metrics: Mapping[str, Mapping[str, int]],
    rank_index: Mapping[str, int],
    *,
    entrypoint_related: bool,
) -> int:
    if source_path is None:
        return 20 if entrypoint_related else 0
    counts = metrics.get(source_path, {})
    score = (
        _safe_non_negative_int(counts.get("fan_in")) * 100
        + int(bool(counts.get("cycle"))) * 25
        + _safe_non_negative_int(counts.get("fan_out")) * 5
        + int(entrypoint_related) * 20
    )
    if not counts and source_path in rank_index:
        score += max(1, 10_000 - rank_index[source_path])
    return score


def _section_body(content: str, heading: str) -> str:
    pattern = re.compile(
        rf"(?ms)^##[ \t]+{re.escape(heading)}[ \t]*\r?\n(.*?)(?=^##[ \t]+|\Z)"
    )
    match = pattern.search(content)
    return match.group(1).strip() if match else ""


def _section_needs_semantics(content: str, heading: str) -> bool:
    return _is_placeholder_text(_section_body(content, heading))


def _is_placeholder_text(text: str) -> bool:
    stripped = _MARKDOWN_COMMENT_RE.sub("", text).strip()
    if not stripped or stripped in {"—", "-", "_—_", "_-_"}:
        return True
    return any(phrase in stripped for phrase in _PLACEHOLDER_PHRASES)


def _index_needs_context(content: str) -> bool:
    return (
        "# LLM Wiki Index" in content
        and any(intro in content for intro in GENERATED_INDEX_INTROS)
    )


def _normalise_prose(text: str) -> str:
    text = _MARKDOWN_COMMENT_RE.sub("", text)
    text = _MARKDOWN_LINK_RE.sub(lambda match: match.group(1), text)
    text = _HEADING_RE.sub("", text)
    return " ".join(text.replace("`", "").split()).casefold()


def _is_copied_docstring_only(
    page: WikiSurfacePage,
    description: str,
    *,
    source_path: str | None,
    source_inventory: Mapping[str, Mapping[str, Any]],
) -> bool:
    if not description or source_path is None:
        return False
    source_data = source_inventory.get(source_path)
    if not isinstance(source_data, Mapping):
        return False
    candidates: list[str] = []
    if page.kind is PageKind.MODULES:
        module_docstring = source_data.get("module_docstring")
        if isinstance(module_docstring, str) and module_docstring.strip():
            candidates.append(module_docstring)
    elif page.kind is PageKind.ENTITIES:
        heading = _first_heading(read_md(page.path))
        for class_info in source_data.get("classes") or []:
            if not isinstance(class_info, Mapping):
                continue
            name = str(class_info.get("name") or "")
            docstring = class_info.get("docstring")
            if (
                isinstance(docstring, str)
                and docstring.strip()
                and (
                    name == heading
                    or page.page_id == name
                    or page.page_id.endswith(f"_{name}")
                )
            ):
                candidates.append(docstring)
    normalized = _normalise_prose(description)
    return bool(normalized) and any(
        normalized == _normalise_prose(value) for value in candidates
    )


def _first_heading(content: str) -> str:
    match = re.search(r"(?m)^#\s+(.+?)\s*$", content)
    return match.group(1).strip().strip('"') if match else ""


def _add_page_candidate(
    candidates: dict[str, _Candidate],
    page: WikiSurfacePage,
    *,
    source_path: str | None,
    category: str,
    priority: str,
    title: str,
    signal: str,
    acceptance: str,
    rank_score: int,
    context: Iterable[str] = (),
) -> _Candidate:
    identity = f"page:{page.relative_path}"
    candidate = candidates.get(identity)
    if candidate is None:
        candidate = _Candidate(
            identity=identity,
            category=category,
            title=title,
            canonical_path=page.relative_path,
            source_path=source_path,
            priority=priority,
            rank_score=rank_score,
        )
        candidates[identity] = candidate
    else:
        _merge_candidate_priority(candidate, priority, category, title)
        candidate.rank_score = max(candidate.rank_score, rank_score)
        candidate.source_path = candidate.source_path or source_path
    candidate.signals.add(signal)
    candidate.suggested_context.add(f"wiki:{page.relative_path}")
    if source_path:
        candidate.suggested_context.add(f"source:{source_path}")
    candidate.suggested_context.update(context)
    candidate.acceptance_checks.add(acceptance)
    candidate.acceptance_checks.add("Preserve CLI-owned generated blocks and tables.")
    return candidate


def _merge_candidate_priority(
    candidate: _Candidate, priority: str, category: str, title: str
) -> None:
    if _PRIORITY_ORDER[priority] < _PRIORITY_ORDER[candidate.priority]:
        candidate.priority = priority
    if _CATEGORY_ORDER.get(category, 99) < _CATEGORY_ORDER.get(candidate.category, 99):
        candidate.category = category
        candidate.title = title


def _semantic_page_context(canonical_path: str, source_path: str | None) -> set[str]:
    result = {f"wiki:{canonical_path}"}
    if source_path:
        result.update(
            {
                f"source:{source_path}",
                f"query:dependency_neighborhood({json.dumps(source_path)})",
            }
        )
    return result


def _flow_context(
    flow_id: str,
    source_path: str | None,
    entrypoints: Mapping[str, Mapping[str, Any]],
) -> set[str]:
    result = {f"query:flow_for_entrypoint({json.dumps(flow_id)})"}
    if source_path:
        result.add(f"source:{source_path}")
    if flow_id in entrypoints:
        result.add(f"evidence:entrypoint:{flow_id}")
    return result


def _add_missing_flow_candidates(
    candidates: dict[str, _Candidate],
    pages_by_path: Mapping[str, WikiSurfacePage],
    entrypoints: Mapping[str, Mapping[str, Any]],
) -> None:
    for flow_id, evidence in sorted(entrypoints.items()):
        if not is_safe_page_id(flow_id):
            identity = f"entrypoint-invalid:{_stable_digest(flow_id)}"
            candidates[identity] = _Candidate(
                identity=identity,
                category="flow_behavior",
                title="Resolve an entrypoint whose id cannot map to a flow page",
                canonical_path=None,
                source_path=evidence.get("source_path"),
                priority="P2",
                signals={"incompatible_entrypoint_id"},
                suggested_context={f"evidence:entrypoint:{flow_id}"},
                acceptance_checks={
                    "Provide a safe stable entrypoint id or retain the missing flow as an explicit limitation."
                },
                requested_defer=True,
                deferral_reason=(
                    "Entrypoint id is not safe for a canonical flow-page path; no output path was inferred."
                ),
            )
            continue
        canonical_path = f"flows/{flow_id}.md"
        if canonical_path in pages_by_path:
            continue
        identity = f"page:{canonical_path}"
        source_path = evidence.get("source_path")
        priority = _flow_priority(flow_id, evidence)
        candidate = _Candidate(
            identity=identity,
            category="flow_behavior",
            title=f"Create and explain the missing flow {flow_id}",
            canonical_path=canonical_path,
            source_path=source_path,
            priority=priority,
            rank_score=20
            + _safe_non_negative_int(evidence.get("boundary_effect_count")),
            signals={"missing_flow_page"},
            suggested_context=_flow_context(flow_id, source_path, entrypoints),
            acceptance_checks={
                "Materialize the deterministic flow page and add evidence-backed ## Behavior prose.",
                "Preserve CLI-owned generated blocks and tables.",
            },
        )
        if priority == "P2":
            candidate.requested_defer = True
            candidate.deferral_reason = (
                "The extracted flow is an ordinary reference/API symbol without "
                "boundary-workflow evidence; retain it as explicit remainder."
            )
        candidates[identity] = candidate


def _flow_priority(flow_id: str, evidence: Mapping[str, Any]) -> str:
    """Classify only externally meaningful boundaries as required work."""

    category = str(evidence.get("category") or flow_id.split("-", 1)[0]).casefold()
    boundary_effect_count = _safe_non_negative_int(
        evidence.get("boundary_effect_count")
    )
    if category in _PRIMARY_FLOW_CATEGORIES or boundary_effect_count > 0:
        return "P0"
    return "P2"


def _canonical_import_path(record: Mapping[str, Any]) -> str | None:
    return _normalise_relative_path(
        record.get("canonical_path") or record.get("path") or record.get("page")
    )


def _grounding_status(record: Mapping[str, Any]) -> str:
    raw = record.get("grounding_status")
    if isinstance(raw, str) and raw in GROUNDING_STATUSES:
        return raw
    grounded = record.get("grounded")
    if grounded is True:
        return "grounded"
    if grounded is False:
        return "ungrounded"
    return "unknown"


def _import_record_compatible(record: Mapping[str, Any]) -> bool:
    if record.get("compatible") is False:
        return False
    raw = record.get("compatibility")
    if isinstance(raw, str) and raw.casefold() in {
        "incompatible",
        "unsupported",
        "corrupt",
        "invalid",
    }:
        return False
    return True


def _imported_page_needs_enhancement(canonical_path: str, content: str) -> bool:
    if canonical_path == "index.md":
        return _index_needs_context(content) or len(_normalise_prose(content)) < 80
    if canonical_path.startswith("flows/"):
        return _section_needs_semantics(content, "Behavior")
    if canonical_path in _CORE_ARCHITECTURE_PAGES:
        return _section_needs_semantics(content, "Notes")
    if canonical_path.startswith(("modules/", "entities/")):
        return _section_needs_semantics(content, "Description")
    return _is_placeholder_text(content) or len(_normalise_prose(content)) < 40


def _import_priority(
    canonical_path: str | None, classification: str
) -> tuple[str, bool]:
    if classification == "incompatible" or canonical_path is None:
        return "P2", False
    if canonical_path == "index.md" or canonical_path.startswith(("flows/", "guides/")):
        return "P0", False
    if canonical_path in _CORE_ARCHITECTURE_PAGES:
        return "P0", False
    return "P1", True


def _add_imported_page_candidates(
    candidates: dict[str, _Candidate],
    wiki: Path,
    pages_by_path: Mapping[str, WikiSurfacePage],
    records: Iterable[Mapping[str, Any]],
    *,
    source_by_page: Mapping[str, str | None],
    metric_map: Mapping[str, Mapping[str, int]],
    rank_index: Mapping[str, int],
    entrypoint_sources: set[str],
) -> None:
    canonical_pages = set(pages_by_path)
    normalized_records = sorted(
        (record for record in records if isinstance(record, Mapping)),
        key=lambda record: (
            _canonical_import_path(record) or "",
            json.dumps(dict(record), sort_keys=True, default=str),
        ),
    )
    for record in normalized_records:
        canonical_path = _canonical_import_path(record)
        classification, reuse_eligible, grounding_status = (
            _classify_imported_semantic_page(wiki, record, canonical_pages)
        )
        if classification not in IMPORTED_PAGE_CLASSIFICATIONS:  # defensive invariant
            raise DocumentationWorklistError(
                f"Unknown imported page classification: {classification}"
            )
        identity = (
            f"page:{canonical_path}"
            if canonical_path is not None
            else f"imported-invalid:{_stable_digest(json.dumps(dict(record), sort_keys=True, default=str))}"
        )
        source_path = source_by_page.get(
            canonical_path or ""
        ) or _normalise_relative_path(record.get("source_path"))
        priority, budget_candidate = _import_priority(canonical_path, classification)
        score = _centrality_score(
            source_path,
            metric_map,
            rank_index,
            entrypoint_related=source_path in entrypoint_sources,
        )
        candidate = candidates.get(identity)
        if candidate is None:
            candidate = _Candidate(
                identity=identity,
                category="imported_semantic_page",
                title=f"Account for imported semantic page {canonical_path or '<invalid path>'}",
                canonical_path=canonical_path,
                source_path=source_path,
                priority=priority,
                rank_score=score,
                budget_candidate=budget_candidate,
            )
            candidates[identity] = candidate
        else:
            _merge_candidate_priority(
                candidate,
                priority,
                "imported_semantic_page",
                candidate.title,
            )
            candidate.budget_candidate = candidate.budget_candidate or budget_candidate
        previous_classification = candidate.imported_classification
        candidate.imported_classification = _stronger_import_classification(
            previous_classification, classification
        )
        candidate.reuse_eligible = candidate.imported_classification in {
            "candidate_reuse",
            "needs_grounding",
        }
        candidate.grounding_status = (
            grounding_status
            if previous_classification is None
            else max(
                (candidate.grounding_status, grounding_status),
                key=lambda value: _GROUNDING_STATUS_ORDER[value],
            )
        )
        candidate.signals.add(f"imported:{classification}")
        if canonical_path:
            candidate.suggested_context.add(f"wiki:{canonical_path}")
        candidate.suggested_context.add("evidence:wiki-input.json")
        if source_path:
            candidate.suggested_context.add(f"source:{source_path}")
        if classification == "candidate_reuse":
            candidate.acceptance_checks.add(
                "Record the grounded imported enrichment as reused without stylistic rewriting."
            )
        elif classification == "needs_grounding":
            candidate.acceptance_checks.add(
                "Ground important imported claims against available source/wiki evidence or defer them explicitly."
            )
        elif classification == "needs_enhancement":
            candidate.acceptance_checks.add(
                "Replace weak imported prose only in the workspace snapshot and cite supporting evidence."
            )
        else:
            candidate.requested_defer = True
            candidate.deferral_reason = "Imported page is missing, unsafe, or incompatible; it cannot be reused automatically."
            candidate.acceptance_checks.add(
                "Resolve the imported-page compatibility problem or preserve it as an explicit limitation."
            )


def _canonical_finding_path(raw_path: object) -> str | None:
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    normalized = raw_path.replace("\\", "/").rstrip("/")
    basename = normalized.rsplit("/", 1)[-1]
    if basename in {"index.md", "api-contracts.md", "dependencies.md", "load-order.md"}:
        return basename
    for directory in _KNOWN_PAGE_DIRS:
        marker = f"/{directory}/"
        if marker in normalized:
            suffix = normalized.rsplit(marker, 1)[1]
            candidate = _normalise_relative_path(f"{directory}/{suffix}")
            if candidate and candidate.endswith(".md"):
                return candidate
    return None


def _add_user_profile_candidates(
    candidates: dict[str, _Candidate],
    findings: Iterable[Mapping[str, Any]],
    *,
    pages_by_path: Mapping[str, WikiSurfacePage],
) -> None:
    normalized = sorted(
        (finding for finding in findings if isinstance(finding, Mapping)),
        key=lambda finding: (
            str(finding.get("category") or ""),
            _canonical_finding_path(
                finding.get("canonical_path") or finding.get("path")
            )
            or "",
            str(finding.get("target") or ""),
        ),
    )
    for finding in normalized:
        category = str(finding.get("category") or "user_profile_finding")
        canonical_path = _canonical_finding_path(
            finding.get("canonical_path") or finding.get("path")
        )
        if category in _USER_PROFILE_INDEX_CATEGORIES:
            canonical_path = "index.md"
        if category == "missing_user_guides":
            canonical_path = None
        priority = "P2" if category in _USER_PROFILE_DEFERRED_CATEGORIES else "P0"
        identity = (
            f"page:{canonical_path}"
            if canonical_path in pages_by_path
            else f"user:{category}:{canonical_path or 'workspace'}"
        )
        candidate = candidates.get(identity)
        if candidate is None:
            candidate = _Candidate(
                identity=identity,
                category="user_profile",
                title=f"Resolve user-profile finding {category}",
                canonical_path=canonical_path,
                source_path=None,
                priority=priority,
            )
            candidates[identity] = candidate
        else:
            _merge_candidate_priority(
                candidate, priority, "user_profile", candidate.title
            )
        candidate.signals.add(f"user_profile:{category}")
        candidate.suggested_context.add(f"evidence:user-profile:{category}")
        if canonical_path:
            candidate.suggested_context.add(f"wiki:{canonical_path}")
        candidate.acceptance_checks.add(
            f"Re-run the user-profile site check and confirm {category} is absent or explicitly deferred."
        )
        if priority == "P2":
            candidate.requested_defer = True
            candidate.deferral_reason = "Non-blocking user-profile coverage remains explicit until evidence or capture capability is available."


def _add_unsupported_source_candidates(
    candidates: dict[str, _Candidate],
    unsupported_sources: Mapping[str, Mapping[str, Any]],
) -> None:
    for language, raw in sorted(
        unsupported_sources.items(), key=lambda item: str(item[0])
    ):
        if not isinstance(raw, Mapping):
            continue
        raw_paths = raw.get("paths") or []
        if isinstance(raw_paths, str):
            raw_paths = [raw_paths]
        paths = [
            path
            for path in (_normalise_relative_path(value) for value in raw_paths)
            if path
        ]
        if not paths:
            paths = [None]
        for source_path in sorted(set(paths), key=lambda value: value or ""):
            identity = f"unsupported:{language}:{source_path or '<unknown>'}"
            candidate = _Candidate(
                identity=identity,
                category="unsupported_source",
                title=f"Resolve unsupported {language} source coverage",
                canonical_path=None,
                source_path=source_path,
                priority="P2",
                signals={f"unsupported_source:{language}"},
                suggested_context={
                    "evidence:unsupported-sources",
                    *(set() if source_path is None else {f"source:{source_path}"}),
                },
                acceptance_checks={
                    "Prepare supported extraction evidence or retain an explicit unverified coverage limitation."
                },
                requested_defer=True,
                deferral_reason=(
                    "No supported deterministic source evidence is available; safety and completeness remain unknown."
                ),
            )
            candidates[identity] = candidate


def _apply_p1_budget(candidates: Iterable[_Candidate], p1_budget: int) -> None:
    ranked = sorted(
        (
            candidate
            for candidate in candidates
            if candidate.budget_candidate
            and candidate.priority == "P1"
            and candidate.imported_classification != "candidate_reuse"
        ),
        key=lambda candidate: (
            -candidate.rank_score,
            candidate.canonical_path or candidate.identity,
        ),
    )
    for candidate in ranked[p1_budget:]:
        candidate.priority = "P2"
        candidate.requested_defer = True
        candidate.deferral_reason = "Outside the configured central semantic P1 budget; retained as explicit long-tail work."
        candidate.signals.add("long_tail_deferred")
        candidate.acceptance_checks.add(
            "Promote with an explicit budget decision, then complete the evidence-backed semantic edit."
        )


def _candidate_sort_key(candidate: _Candidate) -> tuple[Any, ...]:
    return (
        _PRIORITY_ORDER[candidate.priority],
        _CATEGORY_ORDER.get(candidate.category, 99),
        -candidate.rank_score,
        candidate.canonical_path or "",
        candidate.source_path or "",
        candidate.identity,
    )


def _context_sort_key(value: str) -> tuple[int, str]:
    prefix = value.split(":", 1)[0]
    return ({"wiki": 0, "source": 1, "query": 2, "evidence": 3}.get(prefix, 9), value)


def _candidate_to_item(
    candidate: _Candidate,
    *,
    max_context_entries: int,
    max_acceptance_checks: int,
) -> DocumentationWorkItem:
    only_reuse_signal = candidate.signals <= {"imported:candidate_reuse"}
    reused = (
        candidate.imported_classification == "candidate_reuse"
        and candidate.grounding_status == "grounded"
        and only_reuse_signal
    )
    deferred = candidate.requested_defer or (candidate.priority == "P2" and not reused)
    status = "reused" if reused else "deferred" if deferred else "open"
    deferral_reason = candidate.deferral_reason
    if deferred and deferral_reason is None:
        deferral_reason = (
            "Explicit P2 work is deferred until a later bounded semantic pass."
        )
    context = tuple(
        sorted(candidate.suggested_context, key=_context_sort_key)[:max_context_entries]
    )
    acceptance = tuple(sorted(candidate.acceptance_checks)[:max_acceptance_checks])
    return DocumentationWorkItem(
        work_id=f"DW-{_stable_digest(candidate.identity).upper()}",
        priority=candidate.priority,
        category=candidate.category,
        title=candidate.title,
        canonical_path=candidate.canonical_path,
        source_path=candidate.source_path,
        status=status,
        signals=tuple(sorted(candidate.signals)),
        suggested_context=context,
        acceptance_checks=acceptance,
        rank_score=candidate.rank_score,
        imported_classification=candidate.imported_classification,
        reuse_eligible=candidate.reuse_eligible,
        grounding_status=candidate.grounding_status,
        deferred=deferred,
        deferral_reason=deferral_reason,
    )


def _stable_digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


def _stronger_import_classification(current: str | None, candidate: str) -> str:
    if current is None:
        return candidate
    return max(
        (current, candidate),
        key=lambda value: _IMPORT_CLASSIFICATION_ORDER[value],
    )
