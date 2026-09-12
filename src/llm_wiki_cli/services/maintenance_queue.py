"""Advisory managed-page selection from existing freshness and worklist evidence."""

from __future__ import annotations

import hashlib
import json
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


def compose_queue(pages, work_items, freshness, issues, metrics, *, limit=30):
    """Rank captured evidence; unknown provenance never becomes confirmed drift."""
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
        raise ValueError("Queue limit must be between 1 and 1000")
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
        if state != "current":
            reason(
                "freshness:" + state,
                fresh["description"],
                _FRESHNESS_WEIGHT.get(state, 5),
            )
        work = work_map.get(path)
        editable = _EDITABLE.get(page["kind"])
        if work:
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
        if not reasons:
            continue
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
            or (work and work.status == "open")
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
    items.sort(key=lambda item: (-item["score"], item["path"]))
    return {
        "schema_version": QUEUE_SCHEMA,
        "advisory": True,
        "total": len(items),
        "returned": min(limit, len(items)),
        "omitted": max(0, len(items) - limit),
        "items": items[:limit],
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
    limit=30,
    allow_external_src=False,
    source_selection=None,
    helper_cache_dir=None,
):
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
        raise ValueError("Queue limit must be between 1 and 1000")
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
    return "\n".join(lines) + "\n"
