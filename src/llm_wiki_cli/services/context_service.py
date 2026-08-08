"""Structured context budgeting — return priority-ranked, token-budgeted
codebase context for LLM agents.

Priority tiers:

- **high**: files changed in the last commit → full deep inventory detail
- **medium**: 1-hop import neighbors of changed files → slim detail
- **low**: everything else → names only

Usage::

    llm-wiki context --budget 32000
    llm-wiki context --budget 8000 --format markdown
    llm-wiki context --budget 32000 --focus all
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Callable, Mapping
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import Any

from ..config import (
    DEFAULT_WIKI_DIR,
    PathValidationError,
    validate_path,
    validate_source_root,
)
from . import wiki_surface
from .contracts import CONTEXT_PROTOCOL_VERSION
from .dependencies import analyze_dependencies
from .documentation_queries import (
    DocumentationGraphQueryService,
    DocumentationQueryError,
)
from .documentation_query_builder import validate_live_query_source_selection
from .extraction_jobs import (
    ExtractionJobPlan,
    ExtractionJobRequest,
    print_extraction_job_plan,
)
from .io import write_text_output
from .infrastructure_inventory import get_yaml_infrastructure_inventory
from .knowledge_artifacts import KNOWLEDGE_INDEX_FILENAME
from .knowledge_consumption import (
    KnowledgeAvailability,
    KnowledgeReadView,
    build_knowledge_read_view,
)
from .knowledge_graph import (
    CORE_RELATIONSHIP_KINDS,
    GRAPH_ORIGINS,
    GRAPH_RESOLUTIONS,
)
from .knowledge_loader import (
    KnowledgeLoadResult,
    KnowledgeMismatchPolicy,
    KnowledgeStateLoadError,
    load_knowledge_state,
)
from .knowledge_model import (
    ComputedFreshness,
    EvidenceState,
    KnowledgeLoadState,
)
from .knowledge_observability import knowledge_freshness_hint
from .plugins import runtime_project_plugins_enabled
from .knowledge_orchestration import (
    RUNTIME_GENERATION_OPTION_DEFAULTS,
    RuntimeLiveEvaluationInputs,
    build_runtime_live_evaluation,
    runtime_generation_options,
)
from .knowledge_verification import (
    attach_machine_verification_read_view,
    verification_summaries_for_concepts,
)
from .sync_manifest import SyncManifest
from .source_snapshot import (
    SourceSnapshot,
    build_source_snapshot,
    capture_source_selection_inputs,
)
from .source_selection import SourceSelectionError, resolve_source_selection
from .validation import nonnegative_int_or_none
from .wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    SurfaceIndexEvaluation,
    evaluate_surface_index,
)
from .extraction_service import (
    InventoryResult,
    _git_changed_files,
    _partition_snapshot_git_changes,
    analyze_data_flow,
    build_data_flow_context,
    build_flow,
    get_entry_points,
    get_docker_inventory,
    get_inventory_result,
    read_console_scripts,
    resolve_call_edges,
)

PROTOCOL_VERSION = CONTEXT_PROTOCOL_VERSION

_REQUEST_KEYS = {
    "protocol",
    "budget_tokens",
    "focus",
    "format",
    "filters",
    "prefer_fresh",
}
_FILTER_KEYS = {
    "language",
    "module",
    "symbol",
    "entrypoint",
    "surface",
    "freshness",
    "evidence",
    "relationship_kind",
    "relationship_origin",
    "relationship_resolution",
    "relationship_direction",
}
_FOCUS_VALUES = {"changed", "neighbors", "all"}
_FORMATS = {"json", "markdown"}
_CONTEXT_QUERY_LIMIT = 20
_CONCEPT_FILTER_KEYS = {"surface", "symbol"}
_KNOWLEDGE_REFINEMENT_KEYS = {"freshness", "evidence"}
_RELATIONSHIP_REFINEMENT_KEYS = {
    "relationship_kind",
    "relationship_origin",
    "relationship_resolution",
    "relationship_direction",
}
_RELATIONSHIP_DIRECTIONS = ("incoming", "outgoing", "both")
_QUALIFIED_RELATIONSHIP_KIND_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9._-]*/[A-Za-z][A-Za-z0-9._-]*$"
)
_FRESHNESS_FILTER_VALUES = {item.value for item in ComputedFreshness}
_EVIDENCE_FILTER_VALUES = {item.value for item in EvidenceState}
_FRESHNESS_ORDER = {
    ComputedFreshness.CURRENT.value: 0,
    ComputedFreshness.NONSEMANTIC_SOURCE_CHANGE.value: 1,
    ComputedFreshness.UNKNOWN.value: 2,
    ComputedFreshness.SOURCE_CHANGED.value: 3,
    ComputedFreshness.SOURCE_MISSING.value: 4,
    ComputedFreshness.BASIS_INCOMPATIBLE.value: 5,
}
_STALE_OR_UNKNOWN_FRESHNESS = {
    ComputedFreshness.UNKNOWN.value,
    ComputedFreshness.SOURCE_CHANGED.value,
    ComputedFreshness.SOURCE_MISSING.value,
    ComputedFreshness.BASIS_INCOMPATIBLE.value,
}


class ProtocolRequestError(ValueError):
    """Validation error for Wiki-as-Context protocol requests."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


def _extractor_failure_message(inventory_result) -> str:
    """Return a compact, structured error message for extractor failures."""
    details = []
    for status in inventory_result.failed:
        detail = f": {status.message}" if status.message else ""
        details.append(f"{status.language} extraction failed{detail}")
    return "; ".join(details) or "Source extraction failed."


def get_inventory(
    src_dir: str,
    *,
    deep: bool = False,
    return_result: bool = False,
    job_request: ExtractionJobRequest | None = None,
    plan_reporter: Callable[[ExtractionJobPlan], None] | None = None,
    include_plugins: bool = True,
    source_selection: str | Path | None = None,
    source_snapshot: SourceSnapshot | None = None,
) -> dict | InventoryResult:
    """Context-local inventory helper kept patchable for protocol tests."""
    inventory_options: dict[str, Any] = {
        "deep": deep,
        "parallel_jobs": (
            job_request.resolved_jobs if job_request is not None else 1
        ),
        "job_request": job_request,
        "plan_reporter": plan_reporter,
        "source_selection": source_selection,
        "source_snapshot": source_snapshot,
    }
    if not include_plugins:
        inventory_options["include_plugins"] = False
    inventory_result = get_inventory_result(
        src_dir,
        **inventory_options,
    )
    if inventory_result.failed:
        raise ProtocolRequestError(
            _extractor_failure_message(inventory_result), "src_dir"
        )
    return inventory_result if return_result else inventory_result.inventory


def _selected_git_changed_files(
    src_dir: str,
    source_snapshot: SourceSnapshot | None,
) -> list[str] | None:
    changed = _git_changed_files(src_dir)
    if (
        changed is None
        or source_snapshot is None
        or source_snapshot.source_selection_policy is None
    ):
        return changed
    selected, boundary_changed = _partition_snapshot_git_changes(
        changed,
        source_snapshot,
    )
    if boundary_changed:
        return list(source_snapshot.all_source_paths)
    return selected


# ── Token estimation ──────────────────────────────────────────────────


def _estimate_tokens(text: str) -> int:
    """Approximate token count using the ~4 chars/token heuristic.

    No external dependency — good enough for budgeting (within ~10-20%).
    """
    return len(text) // 4


# ── Import graph ──────────────────────────────────────────────────────


def _build_import_graph(inventory: dict) -> dict[str, set[str]]:
    """Build a bidirectional import adjacency map from a deep inventory.

    For each file A that imports a symbol from file B (both present in *inventory*),
    adds edges A→B and B→A.  External / stdlib imports are silently skipped.

    Returns ``{filepath: {neighbor_filepaths}}`` with every key appearing
    even if it has no neighbors.
    """
    # Build a lookup: dotted module path → inventory filepath
    # e.g.  "llm_wiki_cli.config" → "src/llm_wiki_cli/config.py"
    module_to_file: dict[str, str] = {}
    for filepath in inventory:
        # Convert filepath to dotted module path
        mod = _filepath_to_module(filepath)
        if mod:
            module_to_file[mod] = filepath

    graph: dict[str, set[str]] = {fp: set() for fp in inventory}

    for filepath, file_data in inventory.items():
        for imp in file_data.get("imports", []):
            imp_module = imp.get("module", "")
            if not imp_module:
                continue

            # Try exact match, then parent module (for ``from pkg.mod import X``)
            target = module_to_file.get(imp_module)
            if target is None:
                # Try progressively shorter prefixes
                parts = imp_module.split(".")
                for i in range(len(parts) - 1, 0, -1):
                    candidate = ".".join(parts[:i])
                    target = module_to_file.get(candidate)
                    if target is not None:
                        break

            if target is not None and target != filepath:
                graph[filepath].add(target)
                graph[target].add(filepath)

    return graph


def _filepath_to_module(filepath: str) -> str | None:
    """Convert ``"src/llm_wiki_cli/config.py"`` → ``"llm_wiki_cli.config"``.

    Strips a leading ``src/`` directory and the ``.py`` suffix, then
    converts path separators to dots.  Returns None for non-Python files.
    """
    p = Path(filepath)
    if p.suffix != ".py":
        return None

    parts = list(p.with_suffix("").parts)

    # Strip leading "src" directory (common in Python projects)
    if parts and parts[0] == "src":
        parts = parts[1:]

    # Strip __init__ (package init files map to the package itself)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]

    return ".".join(parts) if parts else None


# ── Classification ────────────────────────────────────────────────────


def _classify_files(
    all_files: list[str],
    changed: list[str] | None,
    import_graph: dict[str, set[str]],
    focus: str,
    include_neighbors: bool = True,
) -> dict[str, str]:
    """Assign a priority tier to every file in the inventory.

    Returns ``{filepath: "high"|"medium"|"low"}``.
    """
    if focus == "all":
        return {fp: "high" for fp in all_files}

    classification: dict[str, str] = {}
    changed_set = set(changed) if changed else set()

    # High: changed files
    for fp in all_files:
        if fp in changed_set:
            classification[fp] = "high"

    # Medium: 1-hop neighbors of changed files
    if include_neighbors:
        for fp in changed_set:
            for neighbor in import_graph.get(fp, set()):
                if neighbor not in classification:
                    classification[neighbor] = "medium"

    # Low: everything else
    for fp in all_files:
        if fp not in classification:
            classification[fp] = "low"

    return classification


# ── Detail-level serializers ──────────────────────────────────────────


def _deep_entry(file_data: dict) -> dict:
    """Full detail: classes with methods, params, docstrings, imports."""
    return {k: v for k, v in file_data.items() if k != "language"}


def _slim_entry(file_data: dict) -> dict:
    """Slim detail: class names/bases/line, function names/lines."""
    return {
        "classes": [
            {"name": c["name"], "bases": c.get("bases", []), "line": c.get("line")}
            for c in file_data.get("classes", [])
        ],
        "functions": [
            {"name": f["name"], "line": f.get("line")}
            for f in file_data.get("functions", [])
        ],
    }


def _summary_entry(file_data: dict) -> dict:
    """Names only: lists of class names and function names."""
    entry: dict[str, list[str]] = {}
    cls_names = [c["name"] for c in file_data.get("classes", [])]
    fn_names = [f["name"] for f in file_data.get("functions", [])]
    if cls_names:
        entry["classes"] = cls_names
    if fn_names:
        entry["functions"] = fn_names
    return entry


_DETAIL_SERIALIZERS = {
    "deep": _deep_entry,
    "slim": _slim_entry,
    "summary": _summary_entry,
}

_PREFERRED_DETAILS = {
    "high": "deep",
    "medium": "slim",
    "low": "summary",
}

_DETAIL_FALLBACKS = {
    "high": ("deep", "slim", "summary"),
    "medium": ("slim", "summary"),
    "low": ("summary",),
}


# ── Budgeting ─────────────────────────────────────────────────────────


def _build_context_payload(
    inventory: dict,
    classification: dict[str, str],
    budget: int,
    *,
    freshness_rank_by_source: Mapping[str, int] | None = None,
) -> dict:
    """Build a token-budgeted context payload.

    Greedy allocation: high-priority files first, then medium, then low.
    Files are downgraded to smaller detail levels before they are omitted.

    Returns::

        {
            "budget": <requested>,
            "used": <estimated tokens>,
            "truncated": <whether files were downgraded or omitted>,
            "omitted_files": ["path/too_large.py"],
            "downgraded_files": {"path/file.py": "summary"},
            "files": {
                "path/file.py": {"priority": "high", "detail": "deep", ...detail...},
                ...
            }
        }
    """
    files_out: dict[str, dict] = {}
    omitted_files: list[str] = []
    downgraded_files: dict[str, str] = {}
    used = 0

    # Process relevance tiers in their established order. An opt-in freshness
    # rank may break ties inside a tier, but can never move a file across tiers
    # or filter a file independently of the existing budget.
    for tier in ("high", "medium", "low"):
        tier_candidates = (
            fp for fp, pri in classification.items() if pri == tier
        )
        tier_files = (
            sorted(tier_candidates)
            if freshness_rank_by_source is None
            else sorted(
                tier_candidates,
                key=lambda path: (
                    freshness_rank_by_source.get(path, 1),
                    path,
                ),
            )
        )
        for fp in tier_files:
            file_data = inventory.get(fp, {})
            selected_entry: dict | None = None
            selected_tokens = 0
            selected_detail = ""

            for detail in _DETAIL_FALLBACKS[tier]:
                entry = _build_entry(file_data, tier, detail)
                entry_tokens = _entry_tokens(fp, entry)
                if used + entry_tokens <= budget:
                    selected_entry = entry
                    selected_tokens = entry_tokens
                    selected_detail = detail
                    break

            if selected_entry is None:
                omitted_files.append(fp)
                continue

            files_out[fp] = selected_entry
            used += selected_tokens
            if selected_detail != _PREFERRED_DETAILS[tier]:
                downgraded_files[fp] = selected_detail

    return {
        "budget": budget,
        "used": used,
        "truncated": bool(omitted_files or downgraded_files),
        "omitted_files": omitted_files,
        "downgraded_files": downgraded_files,
        "bounds": {
            "files": _bounds_metadata(
                total=len(classification),
                returned=len(files_out),
            )
        },
        "files": files_out,
    }


def _build_context_payload_with_freshness_preference(
    inventory: dict,
    classification: dict[str, str],
    budget: int,
    *,
    freshness_rank_by_source: Mapping[str, int],
) -> tuple[dict[str, Any], bool]:
    """Apply the freshness tie-break only when budget pressure is observed."""

    baseline = _build_context_payload(inventory, classification, budget)
    budget_pressure = bool(
        baseline.get("truncated") or baseline.get("downgraded_files")
    )
    if not freshness_rank_by_source or not budget_pressure:
        return baseline, budget_pressure
    return (
        _build_context_payload(
            inventory,
            classification,
            budget,
            freshness_rank_by_source=freshness_rank_by_source,
        ),
        True,
    )


def _bounds_metadata(*, total: int, returned: int) -> dict[str, int | bool]:
    """Return exact response-layer collection bounds."""

    return {
        "total": total,
        "returned": returned,
        "truncated": total > returned,
    }


def _build_entry(file_data: dict, priority: str, detail: str) -> dict:
    """Serialize one file at a specific detail level."""
    entry = _DETAIL_SERIALIZERS[detail](file_data)
    entry["priority"] = priority
    entry["detail"] = detail
    return entry


def _entry_tokens(filepath: str, entry: dict) -> int:
    return _estimate_tokens(json.dumps({filepath: entry}))


# ── Markdown renderer ─────────────────────────────────────────────────


def _render_markdown(payload: dict) -> str:
    """Render the context payload as agent-friendly markdown."""
    lines: list[str] = []
    lines.append(f"# Context Budget: {payload['used']} / {payload['budget']} tokens")
    lines.append("")
    ranking_policy = payload.get("ranking_policy")
    if isinstance(ranking_policy, Mapping):
        if ranking_policy.get("applied"):
            availability = ""
        elif not ranking_policy.get("freshness_evaluated"):
            availability = " (requested but freshness was unavailable)"
        elif not ranking_policy.get("budget_pressure"):
            availability = " (inactive because the full context fit the budget)"
        else:
            availability = " (requested but no current source mapping was available)"
        lines.append(
            "Ranking policy: current freshness is preferred only within "
            f"existing relevance tiers{availability}."
        )
        lines.append("")

    tier_labels = {
        "high": "Changed Files (High Priority)",
        "medium": "Neighbor Files (Medium Priority)",
        "low": "Index (Low Priority)",
    }

    for tier in ("high", "medium", "low"):
        tier_files = {
            fp: data
            for fp, data in payload["files"].items()
            if data.get("priority") == tier
        }
        if not tier_files:
            continue

        lines.append(f"## {tier_labels[tier]}")
        lines.append("")

        for fp, data in sorted(tier_files.items()):
            lines.append(f"### `{fp}`")
            lines.append("")

            for cls in data.get("classes", []):
                if isinstance(cls, str):
                    lines.append(f"- class **{cls}**")
                else:
                    bases = ", ".join(cls.get("bases", []))
                    base_str = f"({bases})" if bases else ""
                    lines.append(f"- class **{cls['name']}**{base_str}")
                    if cls.get("docstring"):
                        lines.append(f"  > {cls['docstring'].splitlines()[0]}")
                    for method in cls.get("methods", []):
                        params = ", ".join(
                            p.get("name", "") for p in method.get("params", [])
                        )
                        ret = (
                            f" → {method['return_type']}"
                            if method.get("return_type")
                            else ""
                        )
                        async_prefix = "async " if method.get("is_async") else ""
                        lines.append(
                            f"  - {async_prefix}`{method['name']}({params})`{ret}"
                        )

            for fn in data.get("functions", []):
                if isinstance(fn, str):
                    lines.append(f"- def **{fn}**()")
                else:
                    params = ", ".join(p.get("name", "") for p in fn.get("params", []))
                    ret = f" → {fn['return_type']}" if fn.get("return_type") else ""
                    async_prefix = "async " if fn.get("is_async") else ""
                    lines.append(f"- {async_prefix}def **{fn['name']}**({params}){ret}")
                    if fn.get("docstring"):
                        lines.append(f"  > {fn['docstring'].splitlines()[0]}")

            lines.append("")

    omitted = payload.get("omitted_files", [])
    if omitted:
        lines.append("## Omitted Files")
        lines.append("")
        for fp in omitted:
            lines.append(f"- `{fp}`")
        lines.append("")

    knowledge = payload.get("knowledge")
    if knowledge:
        lines.append("## Knowledge")
        lines.append("")
        lines.append(f"- availability: {knowledge.get('availability')}")
        lines.append(f"- reason: {knowledge.get('reason')}")
        lines.append(
            "- freshness evaluated: "
            + ("yes" if knowledge.get("freshness_evaluated") else "no")
        )
        lines.append(f"- freshness: {knowledge.get('freshness')}")
        lines.append("")

    typed_graph = payload.get("typed_graph")
    if typed_graph:
        lines.append("## Typed Relationship Graph")
        lines.append("")
        lines.append(f"- availability: {typed_graph.get('availability')}")
        lines.append(f"- reason: {typed_graph.get('reason')}")
        coverage = typed_graph.get("coverage")
        analyzer_count = len(coverage) if isinstance(coverage, list) else 0
        lines.append(f"- analyzer coverage records: {analyzer_count}")
        lines.append("")

    graphs = payload.get("graphs", {})
    if graphs:
        lines.append("## Documentation Graphs")
        lines.append("")
        symbol_graph = graphs.get("symbol")
        if symbol_graph:
            query = _graph_query(symbol_graph.get("callers"))
            lines.append(f"### Symbol `{query}`")
            lines.append("")
            lines.append(
                f"- callers: {_graph_status(symbol_graph.get('callers'), 'callers')}"
            )
            lines.append(
                f"- callees: {_graph_status(symbol_graph.get('callees'), 'callees')}"
            )
            lines.append(
                f"- pages: {_graph_status(symbol_graph.get('pages'), 'pages')}"
            )
            lines.append("")

        entrypoint_graph = graphs.get("entrypoint")
        if entrypoint_graph:
            query = _graph_query(entrypoint_graph.get("flow"))
            lines.append(f"### Entry point `{query}`")
            lines.append("")
            lines.append(
                f"- flow: {_graph_status(entrypoint_graph.get('flow'), 'flow')}"
            )
            lines.append(
                "- data flow: "
                f"{_graph_status(entrypoint_graph.get('data_flow'), 'data_flow')}"
            )
            lines.append("")

    surface = payload.get("surface")
    if surface:
        lines.append(f"## Surface `{surface['kind']}`")
        lines.append("")
        lines.append(
            f"{surface['count']} page(s)"
            + (" (truncated)" if surface.get("truncated") else "")
        )
        lines.append("")
        for page in surface.get("pages", []):
            title = page.get("title") or page.get("id") or page.get("canonical_path")
            summary = page.get("knowledge")
            badge = ""
            if isinstance(summary, dict):
                freshness = summary.get("freshness")
                state = (
                    freshness.get("state")
                    if isinstance(freshness, dict)
                    else None
                )
                evidence = summary.get("evidence")
                values = [
                    value
                    for value in (state, evidence)
                    if isinstance(value, str) and value
                ]
                if values:
                    badge = f" [{', '.join(values)}]"
                elif summary.get("availability") != KnowledgeAvailability.READY.value:
                    badge = f" [{summary.get('availability')}]"
            lines.append(
                f"- `{page.get('canonical_path')}` - {title} ({page.get('mcp_uri')})"
                f"{badge}{_typed_graph_page_badge(page)}"
            )
            if isinstance(summary, dict) and isinstance(freshness, dict):
                reason = freshness.get("reason")
                hint = freshness.get("hint")
                if isinstance(reason, str) and isinstance(hint, str):
                    lines.append(f"  - freshness reason: `{reason}`")
                    lines.append(f"  - freshness hint: {hint}")
        lines.append("")

    return "\n".join(lines)


def _typed_graph_page_badge(page: Mapping[str, Any]) -> str:
    graph = page.get("typed_graph")
    if not isinstance(graph, Mapping):
        return ""
    availability = graph.get("availability")
    if availability != KnowledgeAvailability.READY.value:
        return f" [typed graph: {availability}]"
    filtered = _nonnegative_count(graph.get("filtered_total"))
    unfiltered = _nonnegative_count(graph.get("unfiltered_total"))
    suffix = ", truncated" if graph.get("truncated") else ""
    return f" [relationships: {filtered}/{unfiltered}{suffix}]"


def _graph_query(result: object) -> str:
    return str(result.get("query", "")) if isinstance(result, dict) else ""


def _graph_status(result: object, collection_key: str) -> str:
    if not isinstance(result, dict):
        return "unavailable"
    if collection_key in result and isinstance(result[collection_key], list):
        count = len(result[collection_key])
    elif result.get(collection_key) is None:
        count = 0
    elif collection_key in result:
        count = 1
    else:
        count = 0
    status = "found" if result.get("found") else "not found"
    if result.get("ambiguous"):
        status = "ambiguous"
    suffix = " (truncated)" if result.get("truncated") else ""
    return f"{status}, {count} item(s){suffix}"


# ── Wiki-as-Context protocol ──────────────────────────────────────────


def _read_protocol_request(source: str) -> dict:
    """Read and validate a Wiki-as-Context protocol request."""
    try:
        raw = (
            sys.stdin.read()
            if source == "-"
            else Path(source).read_text(encoding="utf-8")
        )
    except OSError as exc:
        raise ProtocolRequestError(f"Could not read request: {exc}", "request") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProtocolRequestError(f"Invalid JSON: {exc.msg}", "request") from exc

    return _validate_protocol_request(data)


def _validate_protocol_request(data: object) -> dict:
    """Return a normalised protocol request or raise ``ProtocolRequestError``."""
    if not isinstance(data, dict):
        raise ProtocolRequestError("Request must be a JSON object.", "request")

    unknown = sorted(set(data) - _REQUEST_KEYS)
    if unknown:
        raise ProtocolRequestError(f"Unknown request field: {unknown[0]}", unknown[0])

    protocol = data.get("protocol")
    if protocol != PROTOCOL_VERSION:
        raise ProtocolRequestError(
            f"Unsupported protocol: {protocol!r}. Expected {PROTOCOL_VERSION!r}.",
            "protocol",
        )

    if "budget_tokens" not in data:
        raise ProtocolRequestError(
            "Missing required field: budget_tokens", "budget_tokens"
        )
    budget = data["budget_tokens"]
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1:
        raise ProtocolRequestError(
            "budget_tokens must be a positive integer.", "budget_tokens"
        )

    fmt = data.get("format", "json")
    if fmt not in _FORMATS:
        raise ProtocolRequestError("format must be 'json' or 'markdown'.", "format")

    focus = _normalise_protocol_focus(data.get("focus", ["changed", "neighbors"]))
    filters = _normalise_protocol_filters(data.get("filters", {}))
    prefer_fresh = data.get("prefer_fresh", False)
    if not isinstance(prefer_fresh, bool):
        raise ProtocolRequestError(
            "prefer_fresh must be a boolean.",
            "prefer_fresh",
        )

    return {
        "protocol": PROTOCOL_VERSION,
        "budget_tokens": budget,
        "focus": focus,
        "format": fmt,
        "filters": filters,
        "prefer_fresh": prefer_fresh,
    }


def _normalise_protocol_focus(raw_focus: object) -> list[str]:
    if not isinstance(raw_focus, list) or not raw_focus:
        raise ProtocolRequestError("focus must be a non-empty list.", "focus")

    if any(not isinstance(item, str) for item in raw_focus):
        raise ProtocolRequestError("focus values must be strings.", "focus")

    unknown = sorted(set(raw_focus) - _FOCUS_VALUES)
    if unknown:
        raise ProtocolRequestError(f"Unknown focus value: {unknown[0]}", "focus")

    if len(set(raw_focus)) != len(raw_focus):
        raise ProtocolRequestError("focus values must not be duplicated.", "focus")

    focus_set = set(raw_focus)
    if "all" in focus_set and len(focus_set) > 1:
        raise ProtocolRequestError(
            "focus 'all' cannot be combined with other values.", "focus"
        )

    if "neighbors" in focus_set and "changed" not in focus_set:
        raise ProtocolRequestError("focus 'neighbors' requires 'changed'.", "focus")

    if "all" in focus_set:
        return ["all"]

    ordered = ["changed"] if "changed" in focus_set else []
    if "neighbors" in focus_set:
        ordered.append("neighbors")
    return ordered


def _normalise_protocol_filters(raw_filters: object) -> dict:
    if raw_filters is None:
        return {}
    if not isinstance(raw_filters, dict):
        raise ProtocolRequestError("filters must be a JSON object.", "filters")

    unknown = sorted(set(raw_filters) - _FILTER_KEYS)
    if unknown:
        raise ProtocolRequestError(
            f"Unknown filter field: {unknown[0]}", f"filters.{unknown[0]}"
        )

    filters: dict[str, str] = {}
    for key in (
        "language",
        "module",
        "symbol",
        "entrypoint",
        "surface",
        "freshness",
        "evidence",
        "relationship_kind",
        "relationship_origin",
        "relationship_resolution",
        "relationship_direction",
    ):
        if key not in raw_filters:
            continue
        value = raw_filters[key]
        if not isinstance(value, str) or not value:
            raise ProtocolRequestError(
                f"filters.{key} must be a non-empty string.", f"filters.{key}"
            )
        if key == "surface":
            _validate_surface_filter(value)
        elif key == "freshness":
            _validate_enum_filter(
                key,
                value,
                _FRESHNESS_FILTER_VALUES,
            )
        elif key == "evidence":
            _validate_enum_filter(
                key,
                value,
                _EVIDENCE_FILTER_VALUES,
            )
        elif key == "relationship_kind":
            _validate_relationship_kind_filter(value)
        elif key == "relationship_origin":
            _validate_enum_filter(key, value, set(GRAPH_ORIGINS))
        elif key == "relationship_resolution":
            _validate_enum_filter(key, value, set(GRAPH_RESOLUTIONS))
        elif key == "relationship_direction":
            _validate_enum_filter(
                key,
                value,
                set(_RELATIONSHIP_DIRECTIONS),
            )
        filters[key] = value

    filter_keys = set(filters)
    refinements = _KNOWLEDGE_REFINEMENT_KEYS & filter_keys
    if refinements and not (_CONCEPT_FILTER_KEYS & filter_keys):
        field = next(
            key for key in ("freshness", "evidence") if key in refinements
        )
        raise ProtocolRequestError(
            f"filters.{field} requires filters.surface or filters.symbol.",
            f"filters.{field}",
        )
    relationship_refinements = _RELATIONSHIP_REFINEMENT_KEYS & filter_keys
    if relationship_refinements and not (_CONCEPT_FILTER_KEYS & filter_keys):
        field = next(
            key
            for key in (
                "relationship_kind",
                "relationship_origin",
                "relationship_resolution",
                "relationship_direction",
            )
            if key in relationship_refinements
        )
        raise ProtocolRequestError(
            f"filters.{field} requires filters.surface or filters.symbol.",
            f"filters.{field}",
        )
    return filters


def _validate_surface_filter(value: str) -> None:
    known = {entry.kind.value for entry in wiki_surface.iter_page_kinds()}
    if value not in known:
        raise ProtocolRequestError(
            f"filters.surface must be one of: {', '.join(sorted(known))}.",
            "filters.surface",
        )


def _validate_enum_filter(key: str, value: str, known: set[str]) -> None:
    if value not in known:
        raise ProtocolRequestError(
            f"filters.{key} must be one of: {', '.join(sorted(known))}.",
            f"filters.{key}",
        )


def _validate_relationship_kind_filter(value: str) -> None:
    if (
        value not in CORE_RELATIONSHIP_KINDS
        and _QUALIFIED_RELATIONSHIP_KIND_RE.fullmatch(value) is None
    ):
        raise ProtocolRequestError(
            "filters.relationship_kind must be a core relationship kind or "
            "a qualified plugin kind such as 'vendor.plugin/relationship'.",
            "filters.relationship_kind",
        )


def _protocol_error_payload(error: ProtocolRequestError) -> dict:
    payload: dict[str, Any] = {
        "protocol": PROTOCOL_VERSION,
        "ok": False,
        "error": {
            "code": "invalid_request",
            "message": str(error),
        },
    }
    if error.field:
        payload["error"]["field"] = error.field
    return payload


def _emit_protocol_error(error: ProtocolRequestError) -> None:
    print(json.dumps(_protocol_error_payload(error), indent=2))
    raise SystemExit(1)


def _apply_protocol_filters(inventory: dict, filters: dict) -> dict:
    """Filter inventory before prioritisation and budgeting."""
    if not filters:
        return inventory

    result: dict = {}
    for filepath, data in inventory.items():
        if "language" in filters and data.get("language") != filters["language"]:
            continue
        if "module" in filters and not _matches_module_filter(
            filepath, filters["module"]
        ):
            continue
        result[filepath] = data
    return result


def _matches_module_filter(filepath: str, pattern: str) -> bool:
    posix_path = filepath.replace("\\", "/")
    path_target = PurePosixPath(posix_path).with_suffix("").as_posix()
    module_target = _filepath_to_module(posix_path)
    module_pattern = pattern.replace("/", ".")

    return (
        fnmatch(path_target, pattern)
        or (module_target is not None and fnmatch(module_target, pattern))
        or (module_target is not None and fnmatch(module_target, module_pattern))
    )


def _context_freshness_rank_by_source(
    query_surface: Mapping[str, Any],
    query_service: DocumentationGraphQueryService,
) -> dict[str, int]:
    """Return CURRENT-first tie-break ranks for mapped source files.

    A source receives the preferred rank only when every mapped concept has an
    evaluated CURRENT result. Mixed, unknown, stale, incompatible, unmapped,
    or unevaluated sources remain in deterministic path order.
    """

    status = query_service.knowledge_status
    if (
        status.get("availability") != KnowledgeAvailability.READY.value
        or not status.get("freshness_evaluated")
    ):
        return {}

    states_by_source: dict[str, list[str]] = {}
    for raw_page in query_surface.get("pages", []) or []:
        if not isinstance(raw_page, Mapping):
            continue
        page = _surface_page_ref(raw_page)
        source_path = page.get("source_path")
        if not isinstance(source_path, str) or not source_path:
            continue
        normalized_source = source_path.replace("\\", "/")
        enriched = _knowledge_enriched_page_ref(page, query_service)
        summary = enriched.get("knowledge")
        freshness = (
            summary.get("freshness") if isinstance(summary, Mapping) else None
        )
        state = (
            freshness.get("state") if isinstance(freshness, Mapping) else None
        )
        states_by_source.setdefault(normalized_source, []).append(
            state if isinstance(state, str) else ""
        )

    return {
        source_path: (
            0
            if states
            and all(
                state == ComputedFreshness.CURRENT.value for state in states
            )
            else 1
        )
        for source_path, states in sorted(states_by_source.items())
    }


def _freshness_ranking_policy(
    status: Mapping[str, Any],
    freshness_rank_by_source: Mapping[str, int],
    *,
    budget_pressure: bool = False,
) -> dict[str, Any]:
    evaluated = bool(status.get("freshness_evaluated", False))
    return {
        "name": "relevance-then-current-freshness",
        "prefer_fresh": True,
        "scope": "within-relevance-tiers",
        "freshness_evaluated": evaluated,
        "budget_pressure": budget_pressure,
        "applied": (
            evaluated
            and bool(freshness_rank_by_source)
            and budget_pressure
        ),
        "filters_stale_content": False,
    }


def _build_protocol_enrichment(
    inventory: dict,
    filters: dict,
    *,
    src_root: Path,
    wiki_dir: str,
    inventory_result: InventoryResult | None = None,
    warnings: list[str] | None = None,
    prefer_fresh: bool = False,
    freshness_ranking_out: dict[str, int] | None = None,
) -> dict:
    if not prefer_fresh and not any(
        key in filters for key in ("symbol", "entrypoint", "surface")
    ):
        return {}

    try:
        wiki_root = validate_path(wiki_dir, "--wiki-dir")
        source_snapshot = (
            inventory_result.source_snapshot
            if inventory_result is not None
            else None
        )
        entrypoints = get_entry_points(
            inventory,
            console_scripts=read_console_scripts(
                str(src_root),
                source_snapshot=source_snapshot,
            ),
            root=src_root,
            fallback_root=(
                None
                if source_snapshot is not None
                and source_snapshot.source_selection_policy is not None
                and src_root.resolve() != Path.cwd().resolve()
                else Path.cwd()
            ),
            include_plugins=runtime_project_plugins_enabled(
                src_root,
                source_selection_configured=(
                    source_snapshot is not None
                    and source_snapshot.source_selection_policy is not None
                ),
            ),
        )
        call_edges = resolve_call_edges(inventory) if entrypoints else []
        flows = [build_flow(entrypoint, call_edges) for entrypoint in entrypoints]
        data_flow_context = (
            build_data_flow_context(inventory, call_edges) if entrypoints else None
        )
        data_flows = [
            analyze_data_flow(
                inventory,
                flow,
                call_edges,
                context=data_flow_context,
            )
            for flow in flows
        ]
        surface_evaluation = evaluate_surface_index(
            wiki_root,
            inventory,
            src_dir=src_root,
            entry_points=entrypoints,
        )
        concept_filter_requested = (
            bool(_CONCEPT_FILTER_KEYS & set(filters)) or prefer_fresh
        )
        knowledge_view = (
            _build_context_knowledge_view(
                wiki_root,
                surface_evaluation,
                inventory,
                inventory_result,
            )
            if concept_filter_requested
            else None
        )
        query_surface = _context_query_surface(
            surface_evaluation.payload,
            knowledge_view,
        )
        query_service = DocumentationGraphQueryService(
            inventory,
            call_edges=call_edges,
            flows=flows,
            data_flows=data_flows,
            dependency_analysis=analyze_dependencies(
                inventory,
                str(src_root),
                source_snapshot=(
                    inventory_result.source_snapshot
                    if inventory_result is not None
                    else None
                ),
            ),
            surface_index=query_surface,
            limit=_CONTEXT_QUERY_LIMIT,
            knowledge_view=knowledge_view,
            machine_verification=(
                verification_summaries_for_concepts(knowledge_view)
                if isinstance(knowledge_view, KnowledgeReadView)
                else None
            ),
        )
    except PathValidationError as exc:
        raise ProtocolRequestError(str(exc), "wiki_dir") from exc
    except DocumentationQueryError as exc:
        raise ProtocolRequestError(str(exc), "filters") from exc
    except OSError as exc:
        raise ProtocolRequestError(
            f"Could not read wiki surface: {exc}", "wiki_dir"
        ) from exc

    enrichment: dict = {}
    graphs: dict = {}
    knowledge_candidates: list[dict[str, Any]] = []
    freshness_rank_by_source = (
        _context_freshness_rank_by_source(query_surface, query_service)
        if prefer_fresh
        else {}
    )
    if freshness_ranking_out is not None:
        freshness_ranking_out.update(freshness_rank_by_source)
    relationship_filter_requested = bool(
        _RELATIONSHIP_REFINEMENT_KEYS & set(filters)
    )
    if relationship_filter_requested:
        enrichment["typed_graph"] = _compact_typed_graph_status(
            query_service.typed_graph_status
        )
    if "symbol" in filters:
        symbol = filters["symbol"]
        graphs["symbol"] = {
            "callers": query_service.callers(symbol),
            "callees": query_service.callees(symbol),
            "pages": _symbol_pages_payload(
                query_service,
                query_surface,
                symbol,
                filters,
                observed=knowledge_candidates,
            ),
        }
    if "entrypoint" in filters:
        entrypoint = filters["entrypoint"]
        graphs["entrypoint"] = {
            "flow": query_service.flow_for_entrypoint(entrypoint),
            "data_flow": query_service.data_flow_for_entrypoint(entrypoint),
        }
    if graphs:
        enrichment["graphs"] = graphs
    if "surface" in filters:
        enrichment["surface"] = _surface_filter_payload(
            query_surface,
            filters["surface"],
            limit=_CONTEXT_QUERY_LIMIT,
            query_service=query_service,
            filters=filters,
            observed=knowledge_candidates,
        )
    if concept_filter_requested:
        knowledge_status = dict(query_service.knowledge_status)
        enrichment["knowledge"] = knowledge_status
        _append_knowledge_context_warning(
            knowledge_status,
            knowledge_candidates,
            filters,
            warnings,
        )
        if prefer_fresh:
            enrichment["ranking_policy"] = _freshness_ranking_policy(
                knowledge_status,
                freshness_rank_by_source,
            )
    if relationship_filter_requested:
        _append_typed_graph_context_warning(
            query_service.typed_graph_status,
            knowledge_candidates,
            warnings,
        )
    return enrichment


def _context_query_surface(
    live_surface: Mapping[str, Any],
    knowledge_view: KnowledgeReadView | None,
) -> dict[str, Any]:
    payload = dict(live_surface)
    committed_surface = (
        knowledge_view.surface
        if knowledge_view is not None
        and isinstance(knowledge_view.surface, Mapping)
        else None
    )
    if committed_surface is None:
        return payload

    committed_sources: dict[str, object] = {}
    for page in committed_surface.get("pages", []) or []:
        if not isinstance(page, Mapping):
            continue
        canonical_path = page.get("canonical_path")
        if isinstance(canonical_path, str):
            committed_sources[canonical_path] = page.get("source_path")
    payload["pages"] = [
        _page_with_committed_source(page, committed_sources)
        for page in live_surface.get("pages", []) or []
        if isinstance(page, Mapping)
    ]
    return payload


def _page_with_committed_source(
    page: Mapping[str, Any],
    committed_sources: Mapping[str, object],
) -> dict[str, Any]:
    copied = dict(page)
    canonical_path = copied.get("canonical_path")
    if isinstance(canonical_path, str) and canonical_path in committed_sources:
        copied["source_path"] = committed_sources[canonical_path]
    return copied


def _surface_filter_payload(
    surface_index: Mapping[str, Any],
    surface: str,
    *,
    limit: int,
    query_service: DocumentationGraphQueryService | None = None,
    filters: dict | None = None,
    observed: list[dict[str, Any]] | None = None,
) -> dict:
    pages = [
        _surface_page_ref(page)
        for page in surface_index.get("pages", []) or []
        if page.get("kind") == surface
    ]
    if query_service is None:
        capped = pages[:limit]
        bounds = _bounds_metadata(total=len(pages), returned=len(capped))
        return {
            "kind": surface,
            "count": len(capped),
            "returned": len(capped),
            "total": len(pages),
            "truncated": bounds["truncated"],
            "bounds": {"pages": bounds},
            "pages": capped,
        }

    capped, selection = _select_knowledge_page_refs(
        pages,
        filters or {},
        query_service,
        limit=limit,
        observed=observed,
    )
    bounds = _bounds_metadata(
        total=int(selection["filtered_total"]),
        returned=len(capped),
    )
    return {
        "kind": surface,
        "count": len(capped),
        "returned": len(capped),
        "total": selection["filtered_total"],
        "truncated": bounds["truncated"],
        "bounds": {"pages": bounds},
        "knowledge_selection": selection,
        "pages": capped,
    }


def _symbol_pages_payload(
    query_service: DocumentationGraphQueryService,
    surface_index: Mapping[str, Any],
    symbol: str,
    filters: dict,
    *,
    observed: list[dict[str, Any]],
) -> dict:
    result = query_service.pages_for_symbol(symbol)
    pages: list[dict] = []
    if result.get("found"):
        selected = result.get("symbol")
        source_path = selected.get("file") if isinstance(selected, dict) else None
        if isinstance(source_path, str):
            source_path = source_path.replace("\\", "/")
            pages = [
                _surface_page_ref(page)
                for page in surface_index.get("pages", []) or []
                if str(page.get("source_path", "")).replace("\\", "/")
                == source_path
            ]

    capped, selection = _select_knowledge_page_refs(
        pages,
        filters,
        query_service,
        limit=_CONTEXT_QUERY_LIMIT,
        observed=observed,
    )
    response_truncated = bool(result.get("truncated"))
    bounds = dict(result.get("bounds", {}))
    bounds["pages"] = _bounds_metadata(
        total=int(selection["filtered_total"]),
        returned=len(capped),
    )
    result["pages"] = capped
    result["bounds"] = bounds
    result["knowledge_selection"] = selection
    result["truncated"] = response_truncated or bool(selection["truncated"])
    return result


def _select_knowledge_page_refs(
    pages: list[dict],
    filters: dict,
    query_service: DocumentationGraphQueryService,
    *,
    limit: int,
    observed: list[dict[str, Any]] | None,
) -> tuple[list[dict], dict[str, int | bool]]:
    enriched = [
        _knowledge_enriched_page_ref(page, query_service) for page in pages
    ]
    if _RELATIONSHIP_REFINEMENT_KEYS & set(filters):
        enriched = [
            _typed_graph_enriched_page_ref(page, filters, query_service)
            for page in enriched
        ]
    if observed is not None:
        observed.extend(enriched)
    ordered = sorted(
        enriched,
        key=lambda page: _knowledge_page_sort_key(
            page,
            query_service.knowledge_status,
        ),
    )
    filtered = [
        page
        for page in ordered
        if _matches_knowledge_refinement(page, filters)
        and _matches_typed_graph_refinement(page, filters)
    ]
    capped = filtered[:limit]
    selection: dict[str, int | bool] = {
        "unfiltered_total": len(enriched),
        "filtered_total": len(filtered),
        "returned": len(capped),
        "truncated": len(filtered) > limit,
    }
    return capped, selection


def _surface_page_ref(page: Mapping[str, Any]) -> dict:
    return {
        "kind": page.get("kind"),
        "id": page.get("id"),
        "title": page.get("title"),
        "canonical_path": page.get("canonical_path"),
        "source_path": page.get("source_path"),
        "role": page.get("role"),
        "mcp_uri": page.get("mcp_uri"),
    }


def _knowledge_enriched_page_ref(
    page: dict,
    query_service: DocumentationGraphQueryService,
) -> dict:
    enriched = dict(page)
    status = {
        "availability": query_service.knowledge_status["availability"],
        "reason": query_service.knowledge_status["reason"],
        "freshness_disclosure": query_service.knowledge_status["freshness"],
        "freshness_evaluated": query_service.knowledge_status[
            "freshness_evaluated"
        ],
    }
    canonical_path = page.get("canonical_path")
    if (
        status["availability"] == KnowledgeAvailability.READY.value
        and isinstance(canonical_path, str)
        and canonical_path
    ):
        result = query_service.get_concept(canonical_path)
        concept = result.get("concept")
        if isinstance(concept, dict):
            status.update(
                {
                    "origin": concept.get("origin"),
                    "evidence": concept.get("evidence"),
                    "verification": concept.get("verification"),
                    "freshness": _compact_context_freshness(
                        concept.get("freshness")
                    ),
                }
            )
            lifecycle = concept.get("lifecycle")
            if isinstance(lifecycle, str):
                status["lifecycle"] = lifecycle
            successor_uid = concept.get("successor_uid")
            if isinstance(successor_uid, str):
                status["successor_uid"] = successor_uid
            reviews = concept.get("reviews")
            if isinstance(reviews, Mapping):
                status["review"] = _compact_context_review(reviews)
            machine_verification = concept.get("machine_verification")
            if isinstance(machine_verification, Mapping):
                status["machine_verification"] = (
                    _compact_context_machine_verification(
                        machine_verification
                    )
                )
    enriched["knowledge"] = status
    return enriched


def _typed_graph_enriched_page_ref(
    page: dict,
    filters: dict,
    query_service: DocumentationGraphQueryService,
) -> dict:
    """Add a compact persisted-graph selection without exposing edge evidence."""

    enriched = dict(page)
    locator = page.get("mcp_uri")
    if not isinstance(locator, str) or not locator:
        locator = page.get("canonical_path")

    if not isinstance(locator, str) or not locator:
        status = _compact_typed_graph_status(query_service.typed_graph_status)
        enriched["typed_graph"] = {
            **status,
            "found": False,
            "direction": filters.get("relationship_direction", "both"),
            "filters": _relationship_filter_summary(filters),
            "unfiltered_total": 0,
            "filtered_total": 0,
            "returned": 0,
            "truncated": False,
            "coverage": _empty_returned_edge_coverage(),
        }
        return enriched

    unfiltered = query_service.traverse_typed_graph(
        locator,
        direction="both",
        include_evidence=False,
    )
    selected_direction = filters.get("relationship_direction", "both")
    traversal_options: dict[str, Any] = {
        "direction": selected_direction,
        "include_evidence": False,
    }
    if "relationship_kind" in filters:
        traversal_options["kinds"] = (filters["relationship_kind"],)
    if "relationship_origin" in filters:
        traversal_options["origins"] = (filters["relationship_origin"],)
    if "relationship_resolution" in filters:
        traversal_options["resolutions"] = (
            filters["relationship_resolution"],
        )

    if (
        selected_direction == "both"
        and len(traversal_options) == 2
    ):
        selected = unfiltered
    else:
        selected = query_service.traverse_typed_graph(
            locator,
            **traversal_options,
        )

    typed_graph_status = selected.get("typed_graph")
    status = _compact_typed_graph_status(
        typed_graph_status
        if isinstance(typed_graph_status, Mapping)
        else query_service.typed_graph_status
    )
    enriched["typed_graph"] = {
        **status,
        "found": bool(selected.get("found")),
        "direction": selected_direction,
        "filters": _relationship_filter_summary(filters),
        "unfiltered_total": _nonnegative_count(unfiltered.get("total")),
        "filtered_total": _nonnegative_count(selected.get("total")),
        "returned": _nonnegative_count(selected.get("returned")),
        "truncated": bool(selected.get("truncated")),
        "coverage": _compact_returned_edge_coverage(selected.get("edges")),
    }
    return enriched


def _relationship_filter_summary(filters: Mapping[str, Any]) -> dict[str, str]:
    return {
        key: str(filters[key])
        for key in (
            "relationship_kind",
            "relationship_origin",
            "relationship_resolution",
            "relationship_direction",
        )
        if key in filters
    }


def _compact_typed_graph_status(
    status: Mapping[str, Any],
) -> dict[str, Any]:
    coverage = status.get("coverage")
    analyzers = coverage if isinstance(coverage, list) else []
    return {
        "availability": status.get("availability"),
        "reason": status.get("reason"),
        "coverage": [
            _compact_analyzer_coverage(item)
            for item in analyzers
            if isinstance(item, Mapping)
        ],
    }


def _compact_analyzer_coverage(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: (
            sorted(
                {
                    item
                    for item in value.get("limitations", [])
                    if isinstance(item, str)
                }
            )
            if key == "limitations"
            else value.get(key)
        )
        for key in (
            "analyzer",
            "observed",
            "emitted",
            "omitted",
            "limit",
            "truncated",
            "limitations",
        )
    }


def _compact_returned_edge_coverage(value: object) -> dict[str, Any]:
    edges = value if isinstance(value, list) else []
    observed = 0
    emitted = 0
    omitted = 0
    truncated = False
    limitations: set[str] = set()
    returned_edges = 0
    for edge in edges:
        if not isinstance(edge, Mapping):
            continue
        coverage = edge.get("coverage")
        if not isinstance(coverage, Mapping):
            continue
        returned_edges += 1
        observed += _nonnegative_count(coverage.get("observed"))
        emitted += _nonnegative_count(coverage.get("emitted"))
        omitted += _nonnegative_count(coverage.get("omitted"))
        truncated = truncated or bool(coverage.get("truncated"))
        raw_limitations = coverage.get("limitations")
        if isinstance(raw_limitations, list):
            limitations.update(
                item for item in raw_limitations if isinstance(item, str)
            )
    return {
        "scope": "returned-edges",
        "edges": returned_edges,
        "observed": observed,
        "emitted": emitted,
        "omitted": omitted,
        "truncated": truncated,
        "limitations": sorted(limitations),
    }


def _empty_returned_edge_coverage() -> dict[str, Any]:
    return {
        "scope": "returned-edges",
        "edges": 0,
        "observed": 0,
        "emitted": 0,
        "omitted": 0,
        "truncated": False,
        "limitations": [],
    }


def _nonnegative_count(value: object) -> int:
    parsed = nonnegative_int_or_none(value)
    return 0 if parsed is None else parsed


def _compact_context_freshness(value: object) -> dict[str, Any]:
    freshness = value if isinstance(value, dict) else {}
    state = freshness.get("state")
    reason = freshness.get("reason")
    result = {
        "state": state,
        "reason": reason,
        "live_comparison_performed": bool(
            freshness.get("live_comparison_performed", False)
        ),
    }
    hint = knowledge_freshness_hint(state, reason)
    if hint is not None:
        result["hint"] = hint
    return result


def _compact_context_review(value: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize bounded section review without reviewer or event metadata."""

    raw_items = value.get("items")
    items = raw_items if isinstance(raw_items, list) else []
    valid_returned = sum(
        1
        for item in items
        if isinstance(item, Mapping) and item.get("state") == "valid"
    )
    expired_returned = sum(
        1
        for item in items
        if isinstance(item, Mapping) and item.get("state") == "expired"
    )
    total = _nonnegative_count(value.get("total"))
    returned = _nonnegative_count(value.get("returned"))
    truncated = bool(value.get("truncated"))
    if total == 0:
        state = "untracked"
    elif truncated:
        state = "partial"
    elif valid_returned and expired_returned:
        state = "mixed"
    elif valid_returned:
        state = "has-valid-sections"
    elif expired_returned:
        state = "has-expired-sections"
    else:
        state = "unknown"
    reason_values: set[str] = set()
    for item in items:
        if not isinstance(item, Mapping):
            continue
        raw_reasons = item.get("reasons")
        if not isinstance(raw_reasons, list):
            continue
        reason_values.update(
            reason
            for reason in raw_reasons
            if isinstance(reason, str)
            and re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", reason)
        )
    reasons = sorted(reason_values)
    return {
        "scope": "section",
        "state": state,
        "total": total,
        "returned": returned,
        "valid_returned": valid_returned,
        "expired_returned": expired_returned,
        "truncated": truncated,
        "reasons": reasons,
    }


def _compact_context_machine_verification(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    """Summarize a receipt without scope identifiers or diagnostics."""

    availability = value.get("availability")
    if availability != "recorded":
        compact = {"availability": availability}
        reason = value.get("reason")
        if isinstance(reason, str) and re.fullmatch(
            r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*",
            reason,
        ):
            compact["reason"] = reason
        return compact

    raw_checks = value.get("checks")
    checks = raw_checks if isinstance(raw_checks, Mapping) else {}
    results = [
        check.get("result")
        for check in checks.values()
        if isinstance(check, Mapping)
    ]
    compact: dict[str, Any] = {
        "availability": availability,
        "valid": value.get("valid"),
        "recorded_result": value.get("recorded_result"),
        "passed": value.get("passed"),
        "checks": {
            "total": len(results),
            "passed": sum(result == "passed" for result in results),
            "failed": sum(result == "failed" for result in results),
        },
    }
    invalidation_reasons = value.get("invalidation_reasons")
    if isinstance(invalidation_reasons, list):
        compact["invalidation_reasons"] = sorted(
            {
                reason
                for reason in invalidation_reasons
                if isinstance(reason, str)
                and re.fullmatch(
                    r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*",
                    reason,
                )
            }
        )
    return compact


def _matches_knowledge_refinement(page: dict, filters: dict) -> bool:
    summary = page.get("knowledge")
    if not isinstance(summary, dict):
        return not (_KNOWLEDGE_REFINEMENT_KEYS & set(filters))
    if (
        "evidence" in filters
        and summary.get("evidence") != filters["evidence"]
    ):
        return False
    if "freshness" in filters:
        freshness = summary.get("freshness")
        if (
            not isinstance(freshness, dict)
            or freshness.get("state") != filters["freshness"]
        ):
            return False
    return True


def _matches_typed_graph_refinement(page: dict, filters: dict) -> bool:
    if not (_RELATIONSHIP_REFINEMENT_KEYS & set(filters)):
        return True
    summary = page.get("typed_graph")
    if not isinstance(summary, Mapping):
        return False
    if summary.get("availability") != KnowledgeAvailability.READY.value:
        # An unavailable persisted graph cannot safely disprove a candidate.
        # Retaining the reference plus its explicit state avoids presenting
        # missing/degraded graph data as a trustworthy empty match set.
        return True
    return _nonnegative_count(summary.get("filtered_total")) > 0


def _knowledge_page_sort_key(page: dict, status: dict) -> tuple:
    canonical_path = str(page.get("canonical_path") or "")
    path_key = (canonical_path.casefold(), canonical_path)
    if (
        status.get("availability") != KnowledgeAvailability.READY.value
        or not status.get("freshness_evaluated")
    ):
        return (0, 0, *path_key)

    summary = page.get("knowledge")
    freshness = summary.get("freshness") if isinstance(summary, dict) else None
    raw_state = freshness.get("state") if isinstance(freshness, dict) else None
    state = raw_state if isinstance(raw_state, str) else None
    evidence = summary.get("evidence") if isinstance(summary, dict) else None
    freshness_rank = (
        len(_FRESHNESS_ORDER)
        if state is None
        else _FRESHNESS_ORDER.get(state, len(_FRESHNESS_ORDER))
    )
    return (
        freshness_rank,
        0 if evidence == EvidenceState.PRESENT.value else 1,
        *path_key,
    )


def _append_knowledge_context_warning(
    status: dict,
    candidates: list[dict[str, Any]],
    filters: dict,
    warnings: list[str] | None,
) -> None:
    if warnings is None:
        return
    unique_candidates = {
        str(page.get("canonical_path") or ""): page for page in candidates
    }
    availability = status.get("availability")
    reason = status.get("reason")
    refinements = _KNOWLEDGE_REFINEMENT_KEYS & set(filters)
    if not candidates and not refinements:
        return
    message: str | None = None
    if availability != KnowledgeAvailability.READY.value:
        message = (
            f"Knowledge context is {availability} ({reason}); concept ranking"
            " and requested refinements are unavailable."
            if refinements
            else (
                f"Knowledge context is {availability} ({reason}); concept"
                " freshness ranking is unavailable and no candidates were dropped."
            )
        )
    elif "freshness" in filters and not status.get("freshness_evaluated"):
        message = (
            "Knowledge freshness was not evaluated; the requested freshness "
            "refinement matched no concept references."
        )
    elif "freshness" not in filters and not status.get("freshness_evaluated"):
        message = (
            "Knowledge freshness was not evaluated; concept references remain "
            "in deterministic path order and no freshness candidates were dropped."
        )
    elif "freshness" not in filters:
        stale_states: dict[str, int] = {}
        for page in unique_candidates.values():
            if not _matches_knowledge_refinement(page, filters):
                continue
            summary = page.get("knowledge")
            freshness = (
                summary.get("freshness") if isinstance(summary, dict) else None
            )
            state = (
                freshness.get("state") if isinstance(freshness, dict) else None
            )
            if state in _STALE_OR_UNKNOWN_FRESHNESS:
                stale_states[state] = stale_states.get(state, 0) + 1
        if stale_states:
            detail = ", ".join(
                f"{state}={stale_states[state]}"
                for state in _FRESHNESS_ORDER
                if state in stale_states
            )
            message = (
                "Knowledge context includes stale or unknown concept references "
                f"({detail}); they were retained by default."
            )
    if message is not None and message not in warnings:
        warnings.append(message)


def _append_typed_graph_context_warning(
    status: Mapping[str, Any],
    candidates: list[dict[str, Any]],
    warnings: list[str] | None,
) -> None:
    if warnings is None or not candidates:
        return
    availability = status.get("availability")
    if availability == KnowledgeAvailability.READY.value:
        return
    reason = status.get("reason")
    message = (
        f"Typed relationship graph is {availability} ({reason}); requested "
        "relationship refinements could not be evaluated and no candidates "
        "were dropped."
    )
    if message not in warnings:
        warnings.append(message)


def _build_context_knowledge_view(
    wiki_root: Path,
    surface_evaluation: SurfaceIndexEvaluation,
    inventory: dict,
    inventory_result: InventoryResult | None,
) -> KnowledgeReadView:
    surface_path = wiki_root / SURFACE_INDEX_FILENAME
    knowledge_path = wiki_root / KNOWLEDGE_INDEX_FILENAME
    if not _context_knowledge_projection_declared(
        wiki_root,
        surface_path,
        knowledge_path,
    ):
        return build_knowledge_read_view(
            KnowledgeLoadResult(
                status=KnowledgeLoadState.ABSENT,
                surface=surface_evaluation.payload,
                knowledge=None,
                manifest_basis=None,
            ),
            snapshot_only=True,
        )

    try:
        load_result = load_knowledge_state(
            wiki_root,
            policy=KnowledgeMismatchPolicy.DEGRADED,
            markdown_pages=surface_evaluation.content_by_path,
        )
    except KnowledgeStateLoadError as exc:
        return _knowledge_error_view(surface_evaluation.payload, exc)

    live_evaluation = None
    snapshot_only = False
    if load_result.status is KnowledgeLoadState.VALID:
        source_snapshot = (
            inventory_result.source_snapshot
            if inventory_result is not None
            else None
        )
        if source_snapshot is None:
            snapshot_only = True
        else:
            assert inventory_result is not None
            assert load_result.knowledge is not None
            assert load_result.manifest_basis is not None
            try:
                docker_infrastructure = get_docker_inventory(
                    str(source_snapshot.root),
                    source_snapshot=source_snapshot,
                )
                infrastructure_inventory = dict(docker_infrastructure)
                for source_path, record in get_yaml_infrastructure_inventory(
                    source_snapshot.root,
                    source_snapshot=source_snapshot,
                ).items():
                    infrastructure_inventory.setdefault(source_path, record)
                live_evaluation = build_runtime_live_evaluation(
                    RuntimeLiveEvaluationInputs(
                        knowledge=load_result.knowledge,
                        manifest=load_result.manifest_basis,
                        inventory=inventory,
                        source_snapshot=source_snapshot,
                        infrastructure_inventory=infrastructure_inventory,
                        missing_source_paths=_reliably_missing_context_sources(
                            load_result.knowledge,
                            source_snapshot,
                        ),
                        inventory_complete=True,
                        extractor_registry=inventory_result.extractor_registry,
                        plugin_extractor_components=(
                            inventory_result.plugin_components
                        ),
                        plugin_components=(
                            inventory_result.producer_plugin_components
                        ),
                        generation_options=runtime_generation_options(
                            surfaces=load_result.manifest_basis.surfaces,
                            generation_inputs=(
                                load_result.manifest_basis.generation_inputs
                            ),
                            include_tests=(),
                            preserve_semantic=True,
                        ),
                        generation_option_defaults=(
                            RUNTIME_GENERATION_OPTION_DEFAULTS
                        ),
                        generation_option_allowlist=tuple(
                            RUNTIME_GENERATION_OPTION_DEFAULTS
                        ),
                    )
                )
            except (OSError, TypeError, UnicodeError, ValueError):
                snapshot_only = True
    view = build_knowledge_read_view(
        load_result,
        live_evaluation=live_evaluation,
        snapshot_only=snapshot_only,
    )
    return attach_machine_verification_read_view(wiki_root, view)


def _context_knowledge_projection_declared(
    wiki_root: Path,
    surface_path: Path,
    knowledge_path: Path,
) -> bool:
    if any(
        path.exists() or path.is_symlink()
        for path in (surface_path, knowledge_path)
    ):
        return True
    try:
        manifest = SyncManifest.load(wiki_root)
    except (FileNotFoundError, OSError, UnicodeError, ValueError):
        return False
    return manifest.artifact_hashes is not None


def _reliably_missing_context_sources(
    knowledge,
    source_snapshot,
) -> frozenset[str]:
    captured = source_snapshot.captured_content_hashes
    uncaptured = {
        basis.source_path
        for concept in knowledge.concepts
        if (basis := concept.facets.structure.basis) is not None
        and basis.source_path is not None
        and basis.source_path not in captured
    }
    missing: set[str] = set()
    for source_path in sorted(uncaptured):
        try:
            (source_snapshot.root / source_path).lstat()
        except FileNotFoundError:
            missing.add(source_path)
        except OSError:
            continue
    return frozenset(missing)


def _knowledge_error_view(
    surface: Mapping[str, Any],
    error: KnowledgeStateLoadError,
) -> KnowledgeReadView:
    unsupported = any(
        issue.code
        in {
            "knowledge-schema-version-unsupported",
            "manifest-version-unsupported",
            "surface-schema-version-unsupported",
        }
        for issue in error.issues
    )
    load_result = (
        KnowledgeLoadResult(
            status=KnowledgeLoadState.INVALID,
            surface=None,
            knowledge=None,
            manifest_basis=None,
            issues=error.issues,
        )
        if unsupported
        else KnowledgeLoadResult(
            status=KnowledgeLoadState.DEGRADED,
            surface=surface,
            knowledge=None,
            manifest_basis=None,
            issues=error.issues,
            underlying_status=error.status,
        )
    )
    return build_knowledge_read_view(
        load_result,
        snapshot_only=True,
    )


def _build_context(
    src_dir: str,
    budget: int,
    fmt: str,
    focus_values: list[str],
    filters: dict | None = None,
    *,
    prefer_fresh: bool = False,
    emit_warnings: bool = True,
    allow_external_src: bool = False,
    read_only: bool = False,
    wiki_dir: str = DEFAULT_WIKI_DIR,
    job_request: ExtractionJobRequest | None = None,
    plan_reporter: Callable[[ExtractionJobPlan], None] | None = None,
    source_selection: str | Path | None = None,
) -> tuple[dict, list[str]]:
    """Build a context payload and return ``(payload, warnings)``."""
    src_root = validate_source_root(
        src_dir,
        "--src-dir",
        allow_external=allow_external_src,
    )
    try:
        selection_policy = resolve_source_selection(src_root, source_selection)
        selection_inputs = capture_source_selection_inputs(
            src_root,
            source_selection=source_selection,
            selection_policy=selection_policy,
        )
        validate_live_query_source_selection(
            source_root=src_root,
            wiki_root=validate_path(wiki_dir, "--wiki-dir"),
            live_identity=(
                selection_policy.identity if selection_policy is not None else None
            ),
            live_selection_inputs=selection_inputs,
            operation="context query",
            allow_empty_wiki=True,
        )
    except PathValidationError as exc:
        raise ProtocolRequestError(str(exc), "wiki_dir") from exc
    except (DocumentationQueryError, SourceSelectionError) as exc:
        raise ProtocolRequestError(str(exc), "source_selection") from exc
    source_snapshot = build_source_snapshot(
        src_root,
        source_selection=source_selection,
        selection_policy=selection_policy,
        expected_selection_inputs=selection_inputs,
    )

    collected_inventory = get_inventory(
        str(src_root),
        deep=True,
        return_result=True,
        job_request=job_request,
        plan_reporter=plan_reporter,
        source_selection=source_selection,
        source_snapshot=source_snapshot,
    )
    inventory_result = (
        collected_inventory
        if isinstance(collected_inventory, InventoryResult)
        else None
    )
    raw_inventory = (
        inventory_result.inventory
        if inventory_result is not None
        else collected_inventory
    )
    if not isinstance(raw_inventory, dict):
        raise ProtocolRequestError(
            "Source extraction returned an invalid inventory.", "src_dir"
        )
    try:
        source_snapshot = (
            inventory_result.source_snapshot
            if inventory_result is not None
            else None
        )
        snapshot_identity = getattr(
            source_snapshot,
            "source_selection_identity",
            None,
        )
        if snapshot_identity is not None:
            live_selection_identity = snapshot_identity
        else:
            policy = resolve_source_selection(src_root, source_selection)
            live_selection_identity = policy.identity if policy is not None else None
        validate_live_query_source_selection(
            source_root=src_root,
            wiki_root=validate_path(wiki_dir, "--wiki-dir"),
            live_identity=live_selection_identity,
            live_selection_inputs=getattr(
                source_snapshot,
                "source_selection_inputs",
                None,
            ),
            operation="context query",
            allow_empty_wiki=True,
        )
    except PathValidationError as exc:
        raise ProtocolRequestError(str(exc), "wiki_dir") from exc
    except (DocumentationQueryError, SourceSelectionError) as exc:
        raise ProtocolRequestError(str(exc), "source_selection") from exc
    filters = filters or {}
    inventory = _apply_protocol_filters(raw_inventory, filters)
    warnings: list[str] = []
    freshness_rank_by_source: dict[str, int] = {}
    enrichment: dict[str, Any] = {}
    if prefer_fresh:
        enrichment = _build_protocol_enrichment(
            raw_inventory,
            filters,
            src_root=src_root,
            wiki_dir=wiki_dir,
            inventory_result=inventory_result,
            warnings=warnings,
            prefer_fresh=True,
            freshness_ranking_out=freshness_rank_by_source,
        )

    if not inventory:
        payload = {
            "budget": budget,
            "used": 0,
            "truncated": False,
            "omitted_files": [],
            "downgraded_files": {},
            "bounds": {
                "files": _bounds_metadata(total=0, returned=0),
            },
            "files": {},
        }
        if not prefer_fresh:
            enrichment = _build_protocol_enrichment(
                raw_inventory,
                filters,
                src_root=src_root,
                wiki_dir=wiki_dir,
                inventory_result=inventory_result,
                warnings=warnings,
            )
        payload.update(enrichment)
        _emit_context_warnings(warnings, enabled=emit_warnings)
        return payload, warnings

    changed: list[str] | None = None
    focus_mode = "all" if "all" in focus_values else "changed"
    include_neighbors = "neighbors" in focus_values

    if focus_mode == "changed":
        changed = _selected_git_changed_files(
            str(src_root),
            inventory_result.source_snapshot if inventory_result is not None else None,
        )
        if changed is None:
            warnings.append(
                "Could not get changed files from git. Treating all files as high priority."
            )
            focus_mode = "all"
        elif not changed:
            warnings.append(
                "No files changed in the last commit. Treating all files as high priority."
            )
            focus_mode = "all"
        else:
            changed = _normalise_changed_paths(changed, inventory)

    import_graph = _build_import_graph(inventory)
    classification = _classify_files(
        list(inventory.keys()),
        changed,
        import_graph,
        focus_mode,
        include_neighbors=include_neighbors,
    )

    payload, budget_pressure = (
        _build_context_payload_with_freshness_preference(
            inventory,
            classification,
            budget,
            freshness_rank_by_source=(
                freshness_rank_by_source if prefer_fresh else {}
            ),
        )
    )
    ranking_policy = enrichment.get("ranking_policy")
    if isinstance(ranking_policy, dict):
        ranking_policy["budget_pressure"] = budget_pressure
        ranking_policy["applied"] = bool(
            ranking_policy.get("freshness_evaluated")
            and freshness_rank_by_source
            and budget_pressure
        )
    if not prefer_fresh:
        enrichment = _build_protocol_enrichment(
            raw_inventory,
            filters,
            src_root=src_root,
            wiki_dir=wiki_dir,
            inventory_result=inventory_result,
            warnings=warnings,
        )
    payload.update(enrichment)
    _emit_context_warnings(warnings, enabled=emit_warnings)
    return payload, warnings


def _emit_context_warnings(warnings: list[str], *, enabled: bool) -> None:
    if not enabled:
        return
    for warning in warnings:
        print(f"Warning: {warning}", file=sys.stderr, flush=True)


def _protocol_success_payload(
    request: dict, payload: dict, warnings: list[str]
) -> dict:
    response = {
        "protocol": PROTOCOL_VERSION,
        "ok": True,
        "budget_tokens": request["budget_tokens"],
        "used_tokens": payload["used"],
        "format": request["format"],
        "focus": request["focus"],
        "filters": request["filters"],
    }
    if request.get("prefer_fresh"):
        response["prefer_fresh"] = True
    for field_name in (
        "truncated",
        "omitted_files",
        "downgraded_files",
        "bounds",
    ):
        if field_name in payload:
            response[field_name] = payload[field_name]
    if warnings:
        response["warnings"] = warnings
    if "graphs" in payload:
        response["graphs"] = payload["graphs"]
    if "surface" in payload:
        response["surface"] = payload["surface"]
    if "knowledge" in payload:
        response["knowledge"] = payload["knowledge"]
    if "typed_graph" in payload:
        response["typed_graph"] = payload["typed_graph"]
    if "ranking_policy" in payload:
        response["ranking_policy"] = payload["ranking_policy"]

    if request["format"] == "markdown":
        response["content"] = _render_markdown(payload)
    else:
        response["files"] = payload["files"]
    return response


def _run_protocol(args) -> None:
    output_path: str | None = getattr(args, "output", None)
    try:
        request = _read_protocol_request(args.request)
        payload, warnings = _build_context(
            getattr(args, "src_dir", "."),
            request["budget_tokens"],
            request["format"],
            request["focus"],
            request["filters"],
            prefer_fresh=request["prefer_fresh"],
            emit_warnings=False,
            allow_external_src=getattr(args, "allow_external_src", False),
            read_only=getattr(args, "read_only", False),
            wiki_dir=getattr(args, "wiki_dir", DEFAULT_WIKI_DIR),
            job_request=ExtractionJobRequest.resolved(1),
            plan_reporter=print_extraction_job_plan,
            source_selection=getattr(args, "source_selection", None),
        )
    except ProtocolRequestError as exc:
        _emit_protocol_error(exc)
        return

    rendered = json.dumps(
        _protocol_success_payload(request, payload, warnings), indent=2
    )
    if output_path:
        write_text_output(output_path, rendered + "\n")
        print(f"Context output written to: {output_path}", file=sys.stderr)
    else:
        print(rendered)


def _run_packet_output(
    *,
    src_dir: str,
    wiki_dir: str,
    budget: int,
    focus_values: list[str],
    prefer_fresh: bool,
    output_path: str | None,
    allow_external_src: bool,
    source_selection: str | Path | None,
) -> None:
    """Build and emit canonical QCP bytes for the CLI-only packet format."""

    from .context_packet import ContextPacketError, build_qualified_context

    request = {
        "protocol": PROTOCOL_VERSION,
        "budget_tokens": budget,
        "focus": focus_values,
        "format": "json",
        "filters": {},
        "prefer_fresh": prefer_fresh,
    }
    try:
        packet = build_qualified_context(
            src_dir,
            wiki_dir,
            request,
            allow_external_src=allow_external_src,
            read_only=True,
            job_request=ExtractionJobRequest.resolved(1),
            plan_reporter=print_extraction_job_plan,
            source_selection=source_selection,
        )
    except (ContextPacketError, PathValidationError, ProtocolRequestError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    rendered = packet.to_bytes().decode("utf-8")
    if output_path:
        write_text_output(output_path, rendered)
        print(f"Context output written to: {output_path}", file=sys.stderr)
    else:
        sys.stdout.write(rendered)


# ── CLI entry point ───────────────────────────────────────────────────


def run(args) -> None:
    if getattr(args, "request", None):
        _run_protocol(args)
        return

    src_dir: str = getattr(args, "src_dir", ".")
    budget: int | None = getattr(args, "budget", None)
    fmt: str = getattr(args, "format", "json")
    focus: str = getattr(args, "focus", "changed")
    output_path: str | None = getattr(args, "output", None)
    allow_external_src: bool = getattr(args, "allow_external_src", False)
    read_only: bool = getattr(args, "read_only", False)
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    prefer_fresh: bool = bool(getattr(args, "prefer_fresh", False))
    source_selection = getattr(args, "source_selection", None)

    if budget is None:
        print("Error: --budget is required unless --request is used.", file=sys.stderr)
        raise SystemExit(2)
    if budget < 1:
        print("Error: --budget must be greater than zero.", file=sys.stderr)
        raise SystemExit(2)

    focus_values = ["all"] if focus == "all" else ["changed", "neighbors"]
    if fmt == "packet":
        _run_packet_output(
            src_dir=src_dir,
            wiki_dir=wiki_dir,
            budget=budget,
            focus_values=focus_values,
            prefer_fresh=prefer_fresh,
            output_path=output_path,
            allow_external_src=allow_external_src,
            source_selection=source_selection,
        )
        return
    try:
        payload, _warnings = _build_context(
            src_dir,
            budget,
            fmt,
            focus_values,
            prefer_fresh=prefer_fresh,
            emit_warnings=True,
            allow_external_src=allow_external_src,
            read_only=read_only,
            wiki_dir=wiki_dir,
            job_request=ExtractionJobRequest.resolved(1),
            plan_reporter=print_extraction_job_plan,
            source_selection=source_selection,
        )
    except ProtocolRequestError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not payload["files"]:
        rendered = "{}" if fmt == "json" else "No source files found."
        if output_path:
            write_text_output(output_path, rendered + "\n")
            print(f"Context output written to: {output_path}", file=sys.stderr)
        else:
            print(rendered)
        return

    if fmt == "markdown":
        rendered = _render_markdown(payload)
    else:
        rendered = json.dumps(payload, indent=2)
    if output_path:
        write_text_output(output_path, rendered + "\n")
        print(f"Context output written to: {output_path}", file=sys.stderr)
    else:
        print(rendered)


def _normalise_changed_paths(changed: list[str], inventory: dict) -> list[str]:
    """Match git-reported changed paths to inventory keys.

    Git paths are relative to the repo root; inventory keys may include
    a leading ``src/`` or similar prefix.  This function tries exact
    match first, then suffix match against inventory keys.
    """
    inv_keys = list(inventory.keys())
    normalised: list[str] = []
    for ch in changed:
        if ch in inventory:
            normalised.append(ch)
            continue
        # Try suffix matching
        for key in inv_keys:
            if key.endswith(ch) or ch.endswith(key):
                normalised.append(key)
                break
    return normalised
