"""Advisory managed-page selection from existing freshness and worklist evidence."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from .context_packet import (
    capture_context_read,
    _assert_source_unchanged,
    _assert_wiki_unchanged,
    _assert_selection_unchanged,
)
from .documentation_worklist import build_documentation_worklist
from .inventory_cache import InventoryCacheOptions
from .lint_service import build_report

QUEUE_SCHEMA = "llm-wiki-maintenance-queue/v1"
MIN_QUEUE_LIMIT = 1
MAX_QUEUE_LIMIT = 1000
DEFAULT_QUEUE_LIMIT = 30
_FRESHNESS_WEIGHT = {
    "source-missing": 90,
    "source-changed": 70,
    "basis-incompatible": 25,
    "unknown": 5,
    "nonsemantic-source-change": 0,
    "current": 0,
}
_EDITABLE = {
    "entities": "Description",
    "modules": "Description",
    "flows": "Behavior",
    "api-contracts": "Notes",
    "infrastructure": "Notes",
    "dependencies": "Notes",
    "load-order": "Notes",
    "index": "introductory prose",
    "guides": "semantic prose",
}
_AUTHORING_HINTS = frozenset(
    {
        "generic_landing_context",
        "missing_or_placeholder_architecture_notes",
        "missing_or_placeholder_flow_behavior",
        "placeholder_semantic_prose",
        "copied_docstring_only_prose",
    }
)


def validate_queue_limit(limit: object) -> int:
    """Validate the shared CLI and service bound before reading queue inputs."""
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not MIN_QUEUE_LIMIT <= limit <= MAX_QUEUE_LIMIT
    ):
        raise ValueError(
            f"Queue limit must be between {MIN_QUEUE_LIMIT} and {MAX_QUEUE_LIMIT}"
        )
    return limit


def _ordinary_review_custody(maintenance_report, manifest_basis):
    """Qualify existing captured authority without another read or adoption."""
    if maintenance_report is not None:
        payload = maintenance_report.payload
        availability = payload["availability"]
        coverage = payload["coverage"]
        partial = bool(
            payload["requires_sync"]
            or not payload["live_evaluation_performed"]
            or coverage.get("issues")
            or coverage.get("untracked_semantic_total", 0)
            or any(not row["basis_available"] for row in maintenance_report.by_record.values())
        )
        if availability == "ready" and partial:
            availability = "partial"
        evidence = "captured-maintenance-status"
        owner = payload["adoption_id"] is not None
        live = payload["live_evaluation_performed"]
    else:
        owner = bool(manifest_basis is not None and manifest_basis.maintenance_state is not None)
        availability = "partial" if owner else "unadopted" if manifest_basis is not None else "unavailable"
        evidence = "validated-native-manifest" if manifest_basis is not None else "no-validated-native-manifest"
        live = False
    return {
        "availability": availability,
        "durable_owner_available": owner,
        "evidence": evidence,
        "live_evaluation_performed": live,
        "source_prose_correctness": "not-established",
        "review_route": {
            "interface": "inspect_concept",
            "instruction": "Inspect the affected target and compare its semantic prose with source; explicit review is required",
        },
        "limitation": "An empty queue does not establish source/prose correctness or completion of ordinary review",
    }


def compose_queue(
    pages,
    work_items,
    freshness,
    issues,
    metrics,
    *,
    limit=DEFAULT_QUEUE_LIMIT,
    maintenance_report=None,
    manifest_basis=None,
):
    """Rank captured evidence; unknown provenance never becomes confirmed drift."""
    limit = validate_queue_limit(limit)
    page_map = {page["canonical_path"]: page for page in pages}
    work_map = {item.canonical_path: item for item in work_items if item.canonical_path}
    reachable = set()
    pending = ["index.md"] if "index.md" in page_map else []
    while pending:
        path = pending.pop()
        if path in reachable or path not in page_map:
            continue
        reachable.add(path)
        pending.extend(page_map[path].get("outgoing_internal_links", ()))
    items = []
    qualification_states = Counter()
    authoring_hint_pages = 0
    for path, page in sorted(page_map.items()):
        if page["kind"] == "log":
            continue
        reasons = []

        def reason(code, message, weight):
            reasons.append({"code": code, "message": message, "weight": weight})

        observation = freshness.get(path)
        state = observation.state.value if observation else "unknown"
        fresh = {
            "state": state,
            "reason": observation.reason_code
            if observation
            else "provenance-unavailable",
            "description": observation.description
            if observation
            else "No validated live freshness comparison is available",
            "live_comparison_performed": observation.live_comparison_performed
            if observation
            else False,
        }
        if state not in {"current", "unknown", "nonsemantic-source-change"}:
            reason(
                "freshness:" + state,
                fresh["description"],
                _FRESHNESS_WEIGHT.get(state, 5),
            )
        work = work_map.get(path)
        editable = _EDITABLE.get(page["kind"])
        source_path = getattr(work, "source_path", None)
        context = set(getattr(work, "suggested_context", ()))
        boundary_flow = bool(
            work
            and page["kind"] == "flows"
            and getattr(work, "category", None) == "flow_behavior"
            and getattr(work, "priority", None) == "P0"
            and source_path
            and "source:" + source_path in context
            and any(value.startswith("evidence:entrypoint:") for value in context)
        )
        concrete_work = bool(
            work and (set(work.signals) - _AUTHORING_HINTS or boundary_flow)
        )
        if concrete_work:
            assert work is not None
            reason(
                "semantic-work",
                work.title + ": " + ", ".join(work.signals),
                40 if work.status == "open" else 10,
            )
        page_issues = sorted(
            issues.get(path, ()), key=lambda i: (i.severity, i.category, i.message)
        )
        for issue in page_issues:
            reason(
                "lint:" + issue.category,
                issue.message,
                {"error": 100, "warning": 30}.get(issue.severity, 5),
            )
        is_reachable = path in reachable if "index.md" in page_map else None
        if is_reachable is False:
            reason("unreachable", "No internal-link path from index.md", 10)
        qualification_states[state] += 1
        authoring_hint_pages += bool(work and not concrete_work)
        if not reasons:
            continue
        if state in {"unknown", "nonsemantic-source-change"}:
            reason("freshness:" + state, fresh["description"], _FRESHNESS_WEIGHT[state])
        source = page.get("source_path")
        fan_in = metrics.get(source, {}).get("fan_in") if source else None
        if fan_in is not None and fan_in > 0:
            reason(
                "fan-in",
                f"{fan_in} selected source modules depend on this source",
                min(fan_in, 20),
            )
        actionable = bool(
            page_issues
            or state in {"source-missing", "source-changed"}
            or (concrete_work and work is not None and work.status == "open")
        )
        items.append(
            {
                "path": path,
                "kind": page["kind"],
                "source_path": source,
                "classification": "actionable" if actionable else "informational",
                "observed_change_category": state,
                "freshness": fresh,
                "ownership": {
                    "surface_role": page["role"],
                    "semantic_section": editable,
                    "instruction": "Preserve generated regions; review semantic prose only"
                    if editable
                    else "Use the owning generator for structural changes",
                },
                "placeholder_signals": list(work.signals) if work else [],
                "work_status": work.status if work else None,
                "lint_severity": "error"
                if any(i.severity == "error" for i in page_issues)
                else "warning"
                if any(i.severity == "warning" for i in page_issues)
                else "info"
                if page_issues
                else None,
                "reachable_from_index": is_reachable,
                "source_fan_in": fan_in,
                "score": sum(r["weight"] for r in reasons),
                "reasons": reasons,
            }
        )
    if maintenance_report is not None:
        from .maintenance_status import compact_maintenance_summary

        by_path = {item["path"]: item for item in items}
        for path, record_ids in maintenance_report.by_path.items():
            rows = [maintenance_report.by_record[record_id] for record_id in record_ids]
            if not any(
                row["recorded_status"] == "pending"
                or row["effective_status"] == "pending"
                or row["mapping"]["state"] != "resolved"
                for row in rows
            ):
                continue
            item = by_path.get(path)
            if item is None:
                page = page_map.get(path, {})
                source = rows[0]["coordinate"]["source_path"] if rows else None
                item = {
                    "path": path,
                    "kind": page.get("kind", path.split("/", 1)[0]),
                    "source_path": source,
                    "classification": "actionable",
                    "observed_change_category": "ordinary-maintenance",
                    "freshness": {
                        "state": "unknown",
                        "reason": "maintenance-observation",
                        "description": "Ordinary review is independently tracked",
                        "live_comparison_performed": False,
                    },
                    "ownership": {
                        "surface_role": page.get("role"),
                        "semantic_section": None,
                        "instruction": "Review the exact ordinary semantic targets",
                    },
                    "placeholder_signals": [],
                    "work_status": None,
                    "lint_severity": None,
                    "reachable_from_index": None,
                    "source_fan_in": None,
                    "score": 0,
                    "reasons": [],
                }
                items.append(item)
                by_path[path] = item
            observed = set().union(*(row["reasons"] for row in rows))
            weights = {
                "executable-syntax-changed": 90,
                "source-deleted": 90,
                "move-unresolved": 65,
                "target-deleted": 60,
                "prose-changed": 45,
                "unreviewed": 40,
                "current-basis-unavailable": 10,
                "implementation-unavailable": 10,
                "producer-incompatible": 10,
                "source-basis-changed": 15,
            }
            for code in sorted(observed):
                weight = weights.get(code, 20)
                item["reasons"].append(
                    {
                        "code": "maintenance:" + code,
                        "message": "Ordinary semantic review: " + code,
                        "weight": weight,
                    }
                )
                item["score"] += weight
            item["classification"] = "actionable"
            scoped = maintenance_report.for_path(path)
            item["maintenance"] = compact_maintenance_summary(scoped)
            scoped_rows = scoped["records"]
            item["record_ids"] = [row["record_id"] for row in scoped_rows]
            item["record_bounds"] = scoped["bounds"]
            targets = [
                {
                    "record_id": row["record_id"],
                    "coordinate": reference["coordinate"],
                    "target": reference["target"],
                    "attribution": role,
                }
                for row in scoped_rows
                for role, reference in [
                    (
                        "retained",
                        {"coordinate": row["coordinate"], "target": row["target"]},
                    ),
                    *(
                        ("candidate", candidate)
                        for candidate in row["mapping"]["candidates"]
                    ),
                ]
                if reference["target"]["canonical_path"] == path
            ]
            total_targets = sum(
                reference["target"]["canonical_path"] == path
                for row in rows
                for reference in [
                    {"target": row["target"]},
                    *row["mapping"]["candidates"],
                ]
            )
            from .knowledge_storage import canonical_bytes

            item["semantic_targets"] = targets[:128]
            item["semantic_target_bounds"] = {
                "total": total_targets,
                "returned": len(item["semantic_targets"]),
                "omitted": total_targets - len(item["semantic_targets"]),
                "truncated": len(item["semantic_targets"]) < total_targets,
                "max_records": 128,
                "max_bytes": 65536,
            }
            while (
                len(
                    canonical_bytes(
                        {
                            key: item[key]
                            for key in (
                                "record_ids",
                                "record_bounds",
                                "semantic_targets",
                                "semantic_target_bounds",
                                "maintenance",
                            )
                        }
                    )
                )
                > 65536
                and item["semantic_targets"]
            ):
                item["semantic_targets"].pop()
                count = len(item["semantic_targets"])
                item["semantic_target_bounds"].update(
                    returned=count, omitted=total_targets - count, truncated=True
                )

        gaps = {}
        for target in maintenance_report.payload["coverage"].get(
            "untracked_targets", ()
        ):
            gaps.setdefault(target["canonical_path"], []).append(
                {"target": target, "reason": "untracked-semantic-target"}
            )
        for issue in maintenance_report.payload["coverage"].get("issues", ()):
            if issue.get("canonical_path"):
                gaps.setdefault(issue["canonical_path"], []).append(
                    {"reason": issue.get("reason", "capture-unavailable")}
                )
        for path, entries in gaps.items():
            item = by_path.get(path)
            if item is None:
                page = page_map.get(path, {})
                item = {
                    "path": path,
                    "kind": page.get("kind", path.split("/", 1)[0]),
                    "source_path": page.get("source_path"),
                    "classification": "informational",
                    "observed_change_category": "ordinary-coverage-gap",
                    "freshness": {
                        "state": "unknown",
                        "reason": "maintenance-capture-gap",
                        "description": "Ordinary coverage is unavailable or untracked",
                        "live_comparison_performed": False,
                    },
                    "ownership": {
                        "surface_role": page.get("role"),
                        "semantic_section": None,
                        "instruction": "Inspect actual untracked targets or source-level capture gaps",
                    },
                    "placeholder_signals": [],
                    "work_status": None,
                    "lint_severity": None,
                    "reachable_from_index": None,
                    "source_fan_in": None,
                    "score": 0,
                    "reasons": [],
                }
                items.append(item)
                by_path[path] = item
            selected_gaps = list(entries[:128])
            from .knowledge_storage import canonical_bytes

            while len(canonical_bytes(selected_gaps)) > 65536 and selected_gaps:
                selected_gaps.pop()
            item["coverage_gaps"] = selected_gaps
            item["coverage_gap_bounds"] = {
                "total": len(entries),
                "returned": len(selected_gaps),
                "omitted": len(entries) - len(selected_gaps),
                "truncated": len(selected_gaps) < len(entries),
            }
            item["reasons"].append(
                {
                    "code": "maintenance:coverage-gap",
                    "message": "Untracked semantic targets or unavailable captured basis",
                    "weight": 20,
                }
            )
            item["score"] += 20
    items.sort(key=lambda item: (-item["score"], item["path"]))
    return {
        "schema_version": QUEUE_SCHEMA,
        "advisory": True,
        "limit": limit,
        "total": len(items),
        "returned": min(limit, len(items)),
        "omitted": max(0, len(items) - limit),
        "items": items[:limit],
        "qualification": {
            "ordinary_review_custody": _ordinary_review_custody(maintenance_report, manifest_basis),
            "freshness_states": dict(sorted(qualification_states.items())),
            "authoring_hint_pages": authoring_hint_pages,
            "scope": "captured page property counts; inspect existing knowledge/status interfaces for individual evidence",
            "limitations": [
                "Unknown provenance alone does not establish a documentation action",
                "Generic authoring hints alone do not establish maintenance work",
            ],
        },
        "limitations": [
            "Freshness compares observations; it is not a verdict about prose correctness",
            "Reachability uses canonical wiki links; fan-in uses selected static source imports",
            "Queue recommendations do not edit pages or change integrity exit policy",
        ],
    }


def build_maintenance_queue(
    src_dir=".",
    wiki_dir="docs/llm_wiki",
    *,
    limit=DEFAULT_QUEUE_LIMIT,
    allow_external_src=False,
    source_selection=None,
    helper_cache_dir=None,
):
    limit = validate_queue_limit(limit)
    captured = capture_context_read(
        src_dir,
        wiki_dir,
        allow_external_src=allow_external_src,
        read_only=True,
        strict_wiki_symlinks=True,
        allow_selection_mismatch=True,
        source_selection=source_selection,
        helper_cache_dir=helper_cache_dir,
    )
    lint = build_report(
        captured.wiki_root,
        str(captured.source_root),
        strict=True,
        knowledge_drift_report=True,
        cache_options=InventoryCacheOptions(enabled=False),
        include_plugins=False,
        source_selection=source_selection,
        helper_cache_dir=helper_cache_dir,
        _captured_inventory_result=captured.inventory_result,
        _captured_source_snapshot=captured.source_snapshot,
    )
    work = build_documentation_worklist(
        captured.wiki_root,
        p1_budget=len(captured.surface_evaluation.pages),
        source_inventory=captured.inventory,
        surface_index=captured.surface_evaluation.payload,
        dependency_metrics=captured.dependency_analysis,
    )
    view = lint.knowledge_view
    freshness = {}
    if not captured.basis_incompatible and view and view.knowledge and view.freshness:
        freshness = {
            concept.document.canonical_path: view.freshness.by_locator[concept.locator]
            for concept in view.knowledge.concepts
            if concept.locator in view.freshness.by_locator
        }
    pages = captured.surface_evaluation.payload["pages"]
    known_paths = {page["canonical_path"] for page in pages}
    issues, global_issues = {}, []
    for issue in [*lint.issues, *lint.diagnostics]:
        path = None
        if issue.path:
            if issue.path in known_paths:
                path = issue.path
            else:
                try:
                    path = (
                        Path(issue.path)
                        .resolve()
                        .relative_to(captured.wiki_root)
                        .as_posix()
                    )
                except ValueError:
                    pass
        if path in known_paths:
            issues.setdefault(path, []).append(issue)
        else:
            global_issues.append(asdict(issue))
    result = compose_queue(
        pages,
        work.items,
        freshness,
        issues,
        captured.dependency_analysis.get("metrics", {}).get("metrics", {}),
        limit=limit,
        maintenance_report=getattr(captured.knowledge_view, "maintenance_report", None),
        manifest_basis=captured.knowledge_view.manifest_basis,
    )
    if captured.basis_incompatible:
        result["limitations"].append(
            "The saved source-selection basis differs from current inputs; page freshness remains unknown"
        )
        for item in result["items"]:
            item["freshness"]["reason"] = "source-selection-basis-incompatible"
    result["diagnostics"] = sorted(
        global_issues, key=lambda i: (i["category"], i["path"] or "", i["message"])
    )
    result["basis"] = {
        "source_identity": captured.source_anchor,
        "wiki_identity": captured.wiki_anchor,
        "knowledge_reason": view.reason_code if view else "unavailable",
        "source_selection_compatible": not captured.basis_incompatible,
    }
    _assert_source_unchanged(captured.source_snapshot, captured.source_anchor)
    _assert_wiki_unchanged(
        captured.wiki_root, captured.wiki_anchor, reject_all_symlinks=True
    )
    _assert_selection_unchanged(captured)
    result["queue_id"] = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(result, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
    )
    return result


def render_queue(queue):
    lines = [
        f"Advisory page queue: {queue['returned']} of {queue['total']} ({queue['omitted']} omitted)"
    ]
    for item in queue["items"]:
        lines.append(
            f"{item['path']} [{item['classification']}; freshness {item['freshness']['state']}]"
        )
        lines.extend("  " + reason["message"] for reason in item["reasons"])
        lines.append("  " + item["ownership"]["instruction"])
    qualification = queue.get("qualification")
    if qualification:
        custody = qualification.get("ordinary_review_custody")
        if custody:
            lines.append("Ordinary durable review custody: " + custody["availability"])
            lines.append("  Source/prose correctness is not established")
            lines.append("  " + custody["review_route"]["instruction"])
            lines.append("  " + custody["limitation"])
        states = ", ".join(
            f"{state}: {count}"
            for state, count in sorted(qualification["freshness_states"].items())
        )
        lines.append("Captured page freshness: " + (states or "no pages"))
        lines.append(
            f"Generic authoring hint pages: {qualification['authoring_hint_pages']}"
        )
        lines.append("  " + qualification["scope"])
        lines.extend("  " + value for value in qualification["limitations"])
    return "\n".join(lines) + "\n"
