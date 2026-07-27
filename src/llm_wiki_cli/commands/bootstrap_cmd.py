from __future__ import annotations

import io
import json
import re
import shlex
import sys
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, TextIO

from ..config import (
    DEFAULT_WIKI_DIR as _DEFAULT_WIKI_DIR,
)
from ..config import (
    validate_path,
    validate_source_root,
)
from ..services.api_contracts import (
    ApiContractError,
    attach_routes_to_entry_points,
    build_api_contracts,
    render_api_contracts_markdown,
    render_flow_api_contract_section,
)
from ..services.bootstrap_service import (
    BootstrapContractError,
    BootstrapExtractionError,
    BootstrapRequest,
    BootstrapResult,
)
from ..services.contracts import (
    BOOTSTRAP_SUMMARY_SCHEMA_VERSION,
    KNOWLEDGE_SCHEMA_VERSION,
)
from ..services.data_flow import (
    analyze_data_flow,
    analyze_data_flow_detailed,
    build_data_flow_context,
)
from ..services.dependencies import (
    analyze_dependencies,
    build_dependency_observations,
    build_external_dependency_observations,
    package_dependency_graph,
)
from ..services.diagrams import (
    data_flow_diagram,
    flowchart,
    resolve_diagram_style,
    sequence_diagram,
)
from ..services.entrypoints import (
    build_flow,
    build_flow_detailed,
    entry_points_from_detailed_observations,
    get_detailed_entry_points,
    read_console_scripts,
)
from ..services.imports import ModulePathResolver, build_module_path_resolver
from ..services.infrastructure_inventory import (
    RUNTIME_CONFIG_TYPES,
    get_yaml_infrastructure_inventory,
    infrastructure_display_label,
    infrastructure_page_name,
)
from ..services.io import read_md, write_md
from ..services.knowledge_artifacts import (
    ArtifactWriteState,
    KnowledgeCommitResult,
)
from ..services.knowledge_orchestration import (
    RUNTIME_GENERATION_OPTION_DEFAULTS,
    RuntimeKnowledgeInputs,
    collect_runtime_repository_evidence,
    finalize_runtime_knowledge,
    persist_runtime_generation_policy,
    runtime_generation_options,
)
from ..services.markdown_sections import (
    preserve_level_two_section_exact as _service_preserve_level_two_section_exact,
)
from ..services.module_maps import build_module_dependency_maps
from ..services.paths import normalize_source_path
from ..services.relationships import build_entity_relationship_summaries
from ..services.schema import (
    ALL_SCHEMA_FILES as _AGENT_SCHEMA_FILES,
)
from ..services.schema import (
    CONSTRAINT_END as _CONSTRAINT_END,
)
from ..services.schema import (
    CONSTRAINT_START as _CONSTRAINT_START,
)
from ..services.source_snapshot import (
    build_source_snapshot,
    format_unsupported_source_summary,
    unsupported_source_summary,
)
from ..services.sync_manifest import SyncManifest
from ..services.wiki_surface import PageKind, canonical_path, iter_page_kinds
from ..services.wiki_surface_index import evaluate_surface_index
from .extract_cmd import (
    InventoryResult,
    get_call_graph,
    get_docker_inventory,
    get_inventory_result,
    print_inventory_failures,
    resolve_call_observations,
    resolve_call_edges,
)

_SURFACE_LABELS = {entry.kind: entry.label for entry in iter_page_kinds()}
_SOURCE_DOC_LINK_RE = re.compile(r"(!)?\[([^\]]+)\]\(([^)]+)\)")
_UNSAFE_PAGE_ID_CHARS_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_HASKELL_DECLARATION_LABELS = {
    "data": "Data",
    "newtype": "Newtype",
    "type": "Type alias",
    "class": "Type class",
    "instance": "Instance",
}
_HASKELL_FUNCTION_LABELS = {
    "signature": "Signature",
    "value": "Value",
    "function": "Function",
}
EntityOccurrenceKey = tuple[str, str, int]


def _preserve_source_doc_link(target: str) -> bool:
    target = target.strip().lower()
    return (
        "://" in target
        or target.startswith("mailto:")
        or target.startswith("tel:")
        or target.startswith("#")
    )


def _sanitize_source_doc_markdown(value: object) -> str:
    """Keep extracted source prose readable without creating broken wiki links."""
    if value in (None, ""):
        return ""

    def repl(match: re.Match[str]) -> str:
        label = match.group(2).strip()
        target = match.group(3).strip()
        if _preserve_source_doc_link(target):
            return match.group(0)
        if match.group(1):
            return label
        target_text = target.strip("<>").strip("`")
        if not target_text or label.strip("`") == target_text:
            return label
        return f"{label} (`{target_text}`)"

    return _SOURCE_DOC_LINK_RE.sub(repl, str(value))


def _source_doc_first_line(value: object) -> str:
    return _sanitize_source_doc_markdown(value).split("\n")[0] if value else ""


def _generated_diagram_style(
    surface: str,
    *,
    root: str | Path = ".",
    fallback_root: str | Path | None = None,
    **context: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"surface": surface}
    payload.update(context)
    return resolve_diagram_style(payload, root=root, fallback_root=fallback_root)


def _module_name_from_path(filepath: str) -> str:
    """Derive a short module name from a file path."""
    return Path(filepath).stem


def _is_haskell_filepath(filepath: str) -> bool:
    return Path(filepath).suffix.lower() in {".hs", ".lhs"}


def _is_haskell_file_data(file_data: Mapping | None) -> bool:
    return isinstance(file_data, Mapping) and file_data.get("language") == "haskell"


def _haskell_module_name(file_data: Mapping | None) -> str:
    if not isinstance(file_data, Mapping):
        return ""
    module = file_data.get("module")
    return str(module).strip() if module not in (None, "") else ""


def _display_module_name(filepath: str, file_data: Mapping | None = None) -> str:
    if _is_haskell_file_data(file_data):
        return _haskell_module_name(file_data) or _module_name_from_path(filepath)
    return _module_name_from_path(filepath)


def _safe_page_component(value: object, *, fallback: str = "page") -> str:
    raw = str(value).strip() if value not in (None, "") else ""
    safe = _UNSAFE_PAGE_ID_CHARS_RE.sub("_", raw).strip("_")
    safe = re.sub(r"_+", "_", safe).lstrip(".")
    return safe or fallback


def _page_name_for_module(filepath: str) -> str:
    """Return the wiki page stem for a module.

    For collision-aware naming use :func:`build_module_page_map` instead.
    """
    return Path(filepath).stem


def _page_name_for_entity(cls_name: str) -> str:
    """Return the wiki page stem for an entity.

    For collision-aware naming use :func:`build_entity_page_map` instead.
    """
    return _safe_page_component(cls_name, fallback="entity")


# ── Collision-aware page-name builders ────────────────────────────────


def _disambiguate_paths(fps: list[str], stem: str) -> dict[str, str]:
    """Given filepaths sharing *stem*, return ``{filepath: unique_name}``.

    Progressively adds parent directory components until every name is
    unique.  Falls back to the full path (sans extension) if needed.
    """
    max_depth = max(len(Path(fp).parts) for fp in fps)
    for depth in range(1, max_depth):
        candidates: dict[str, str] = {}
        for fp in fps:
            dir_parts = Path(fp).parts[:-1]  # directories only
            prefix_parts = dir_parts[-depth:] if len(dir_parts) >= depth else dir_parts
            candidates[fp] = "_".join(prefix_parts) + "_" + stem
        if len(set(candidates.values())) == len(fps):
            return candidates
    # Fallback: full path plus extension, with a final numeric guard.
    candidates = {fp: _page_name_with_extension(fp) for fp in fps}
    if len(set(candidates.values())) == len(fps):
        return candidates

    seen: dict[str, int] = defaultdict(int)
    unique: dict[str, str] = {}
    for fp in sorted(fps):
        name = candidates[fp]
        seen[name] += 1
        unique[fp] = name if seen[name] == 1 else f"{name}_{seen[name]}"
    return unique


def _page_name_with_extension(filepath: str) -> str:
    """Return a page-safe path stem that includes the source extension."""
    path = Path(filepath)
    base = path.with_suffix("").as_posix()
    base = base.replace("/", "_").replace("\\", "_").replace(".", "_")
    ext = path.suffix.lower().lstrip(".") or "file"
    ext = ext.replace(".", "_")
    return f"{base}_{ext}"


def _page_name_from_source_path(filepath: str) -> str:
    """Return a page-safe stem from the full source path without extension."""
    path = Path(filepath)
    base = path.with_suffix("").as_posix()
    base = base.replace("/", "_").replace("\\", "_").replace(".", "_")
    return _safe_page_component(base, fallback=_page_name_for_module(filepath))


def _globally_disambiguate_module_pages(page_map: dict[str, str]) -> dict[str, str]:
    """Resolve page-id collisions left after stem-group disambiguation."""
    from collections import Counter

    page_counts = Counter(page_map.values())
    colliding_pages = {page for page, count in page_counts.items() if count > 1}
    if not colliding_pages:
        return page_map

    resolved = dict(page_map)
    used = {page for filepath, page in page_map.items() if page not in colliding_pages}
    for filepath in sorted(page_map):
        if page_map[filepath] not in colliding_pages:
            continue
        base = _page_name_from_source_path(filepath)
        candidates = [base, _page_name_with_extension(filepath)]
        candidate = next((item for item in candidates if item not in used), base)
        suffix = 2
        while candidate in used:
            candidate = f"{base}_{suffix}"
            suffix += 1
        resolved[filepath] = candidate
        used.add(candidate)
    return resolved


def build_module_page_map(inventory: dict) -> dict[str, str]:
    """Return ``{filepath: page_stem}`` qualifying colliding stems.

    When two files share the same stem (e.g. ``pkg_a/cli.py`` and
    ``pkg_b/cli.py``) parent directory components are prepended to
    disambiguate.  A final global pass resolves collisions between already
    qualified names and unrelated raw stems. Non-colliding stems keep their
    short name.
    """
    from collections import defaultdict

    stem_groups: defaultdict[str, list[str]] = defaultdict(list)
    for fp in inventory:
        stem_groups[Path(fp).stem].append(fp)

    page_map: dict[str, str] = {}
    for stem, fps in stem_groups.items():
        if len(fps) == 1:
            page_map[fps[0]] = stem
        else:
            page_map.update(_disambiguate_paths(fps, stem))
    return _globally_disambiguate_module_pages(page_map)


def _entity_occurrences(
    inventory: Mapping[str, Mapping],
) -> list[tuple[EntityOccurrenceKey, Mapping]]:
    occurrences: list[tuple[EntityOccurrenceKey, Mapping]] = []
    for fp, data in inventory.items():
        seen_names: defaultdict[str, int] = defaultdict(int)
        for cls in data.get("classes", []):
            name = cls.get("name")
            if not name:
                continue
            name_text = str(name)
            seen_names[name_text] += 1
            occurrences.append(((name_text, fp, seen_names[name_text]), cls))
    return occurrences


def _legacy_entity_page_map(
    occurrence_page_map: Mapping[EntityOccurrenceKey, str],
) -> dict[tuple[str, str], str]:
    page_map: dict[tuple[str, str], str] = {}
    for (name, filepath, _occurrence), page_name in occurrence_page_map.items():
        page_map.setdefault((name, filepath), page_name)
    return page_map


def build_entity_occurrence_page_map(
    inventory: dict,
    module_page_map: Mapping[str, str] | None = None,
) -> dict[EntityOccurrenceKey, str]:
    """Return occurrence-aware ``{(class_name, filepath, occurrence): page_stem}``.

    The occurrence value is one-based per class name within a file. This keeps
    duplicate class declarations in one source file addressable without
    changing stable page names for non-colliding entities.
    """
    from collections import Counter

    occurrences = _entity_occurrences(inventory)
    name_counts = Counter(key[0] for key, _cls in occurrences)
    files_by_name: defaultdict[str, set[str]] = defaultdict(set)
    for (name, filepath, _occurrence), _cls in occurrences:
        files_by_name[name].add(filepath)

    mod_page_map = dict(module_page_map or build_module_page_map(inventory))
    proposed_pages: list[tuple[EntityOccurrenceKey, str, str]] = []
    for key, _cls in occurrences:
        name, filepath, occurrence = key
        safe_name = _page_name_for_entity(name)
        if name_counts[name] > 1 and len(files_by_name[name]) > 1:
            page_name = _safe_page_component(f"{mod_page_map[filepath]}_{safe_name}")
        else:
            page_name = safe_name
        if occurrence > 1:
            page_name = _safe_page_component(f"{page_name}_{occurrence}")
        proposed_pages.append((key, page_name, mod_page_map[filepath]))

    page_counts = Counter(page for _, page, _ in proposed_pages)
    used: set[str] = set()
    page_map: dict[EntityOccurrenceKey, str] = {}
    for key, page_name, module_page in proposed_pages:
        candidate = page_name
        if page_counts[page_name] > 1:
            candidate = _safe_page_component(f"{module_page}_{page_name}")
        suffix = 2
        while candidate in used:
            candidate = f"{page_name}_{suffix}"
            suffix += 1
        page_map[key] = candidate
        used.add(candidate)
    return page_map


def build_entity_page_map(inventory: dict) -> dict[tuple[str, str], str]:
    """Return ``{(class_name, filepath): page_stem}`` qualifying collisions.

    Legacy projection of :func:`build_entity_occurrence_page_map`. If the same
    class name appears multiple times in one file, this returns the first
    occurrence for older consumers that cannot address occurrences directly.
    """
    return _legacy_entity_page_map(build_entity_occurrence_page_map(inventory))


def _build_relationships(
    inventory: dict,
    module_page_map: dict[str, str] | None = None,
    *,
    target_entities: set[tuple[str, str]] | None = None,
    resolver: ModulePathResolver | None = None,
) -> dict:
    """Cross-reference imports against known entity identities to build a usage graph.

    Returns a dict mapping ``(entity_name, defining_filepath)`` to a list of
    {module, module_page, function, relationship} records. Duplicate entity names
    are only linked when the import module resolves to exactly one defining file.

    *module_page_map*: optional mapping of filepath -> wiki page stem produced by
    ``_page_name_for_module``.  When provided every relationship record carries
    ``module_page`` so that generated links point to the correct page even when
    the module stem was qualified to resolve a collision.
    """
    entity_to_files: dict[str, set[str]] = defaultdict(set)
    for filepath, data in inventory.items():
        for cls in data.get("classes", []):
            entity_to_files[cls["name"]].add(filepath)

    # relationship map: (entity_name, defining_filepath) -> relationship records
    relationships = defaultdict(list)
    _mod_page_map = module_page_map or {}
    module_resolver = resolver or build_module_path_resolver(inventory)

    for filepath, data in inventory.items():
        mod_name = _module_name_from_path(filepath)
        mod_page = _mod_page_map.get(filepath, mod_name)
        imported_entities: dict[tuple[str, str], set[str]] = {}
        for imp in data.get("imports", []):
            entity_name = imp.get("name")
            if not entity_name or entity_name not in entity_to_files:
                continue
            candidates = set(entity_to_files[entity_name])
            module_candidates = module_resolver.candidates(
                imp.get("module", ""), filepath
            )
            if module_candidates:
                candidates &= module_candidates
            candidates.discard(filepath)
            if len(candidates) != 1:
                continue
            defining_filepath = next(iter(candidates))
            entity_key = (entity_name, defining_filepath)
            if target_entities is not None and entity_key not in target_entities:
                continue
            visible_names = {entity_name}
            if imp.get("alias"):
                visible_names.add(imp["alias"])
            imported_entities[entity_key] = visible_names

        for entity_key, visible_names in imported_entities.items():
            for fn in data.get("functions", []):
                mentions_entity = False
                for p in fn.get("params", []):
                    if any(name in p.get("type", "") for name in visible_names):
                        mentions_entity = True
                if any(name in fn.get("return_type", "") for name in visible_names):
                    mentions_entity = True
                for dec in fn.get("decorators", []):
                    if any(name in dec for name in visible_names):
                        mentions_entity = True

                if mentions_entity:
                    relationships[entity_key].append(
                        {
                            "module": mod_name,
                            "module_page": mod_page,
                            "module_path": filepath,
                            "function": fn["name"],
                            "rel": "used_by",
                        }
                    )

            # If imported but not found in any specific function, still note the import
            if not any(r["module_path"] == filepath for r in relationships[entity_key]):
                relationships[entity_key].append(
                    {
                        "module": mod_name,
                        "module_page": mod_page,
                        "module_path": filepath,
                        "function": None,
                        "rel": "imported_by",
                    }
                )

    return dict(relationships)


def _format_signature(fn: dict) -> str:
    """Build a readable function signature string."""
    if fn.get("signature") and not fn.get("params"):
        return str(fn["signature"])

    records = list(fn.get("params", []))
    params: list[str] = []
    inserted_keyword_separator = False
    for index, p in enumerate(records):
        kind = p.get("kind", "positional_or_keyword")
        if kind == "keyword_only" and not inserted_keyword_separator:
            if not any(
                item.get("kind") == "var_positional" for item in records[:index]
            ):
                params.append("*")
            inserted_keyword_separator = True

        part = p["name"]
        if kind == "var_positional":
            part = f"*{part}"
            inserted_keyword_separator = True
        elif kind == "var_keyword":
            part = f"**{part}"
        if p.get("type"):
            part += f": {p['type']}"
        if p.get("default") not in (None, ""):
            part += f" = {p['default']}"
        params.append(part)
        if kind == "positional_only" and (
            index + 1 == len(records)
            or records[index + 1].get("kind") != "positional_only"
        ):
            params.append("/")

    ret = fn.get("return_type", "")
    sig = f"({', '.join(params)})"
    if ret:
        sig += f" -> {ret}"
    return sig


def _table_text(value: object) -> str:
    if value in (None, ""):
        return "—"
    return str(value).replace("\n", "<br>").replace("|", "\\|")


def _table_inline_code(value: object) -> str:
    if value in (None, ""):
        return "—"
    text = str(value).replace("\n", " ").replace("|", "\\|")
    runs = [len(match.group(0)) for match in re.finditer(r"`+", text)]
    fence = "`" * (max(runs, default=0) + 1)
    padding = " " if runs or text.startswith(" ") or text.endswith(" ") else ""
    return f"{fence}{padding}{text}{padding}{fence}"


def _haskell_declaration_label(kind: object) -> str:
    normalized = str(kind).strip().casefold() if kind not in (None, "") else ""
    return _HASKELL_DECLARATION_LABELS.get(normalized, "Declaration")


def _haskell_function_label(kind: object) -> str:
    normalized = str(kind).strip().casefold() if kind not in (None, "") else ""
    return _HASKELL_FUNCTION_LABELS.get(normalized, "Function")


def _dash(value: object) -> str:
    return "—" if value in (None, "") else str(value)


def _code_or_dash(value: object) -> str:
    return "—" if value in (None, "") else f"`{_md_cell(value)}`"


def _yes_no(value: object) -> str:
    return "yes" if bool(value) else "no"


def _line_sort_value(value: object) -> int:
    try:
        if value in (None, ""):
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def _module_page_stem(
    filepath: str | None, module_page_map: Mapping[str, str] | None = None
) -> str | None:
    if not filepath:
        return None
    return (module_page_map or {}).get(filepath, _module_name_from_path(filepath))


def _module_link(
    filepath: str | None, module_page_map: Mapping[str, str] | None = None
) -> str:
    stem = _module_page_stem(filepath, module_page_map)
    if not stem:
        return "—"
    return f"[{stem}](../modules/{stem}.md)"


def _code_join(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in values) if values else "—"


def _entity_node_label(summary: Mapping) -> str:
    file_label = summary.get("file") or "unknown"
    return f"{summary.get('name', 'entity')} ({file_label})"


def _class_ref_label(ref: Mapping) -> str:
    file_label = ref.get("file")
    if file_label:
        return f"{ref.get('name', 'class')} ({file_label})"
    return str(ref.get("name") or "class")


def _reference_label(ref: Mapping) -> str:
    symbol = ref.get("symbol")
    file_label = ref.get("file") or ref.get("module") or "unknown"
    return f"{symbol} ({file_label})" if symbol else str(file_label)


def _entity_relationship_graph(
    summary: Mapping,
    module_page_map: Mapping[str, str] | None,
    diagram_style: Mapping[str, Any] | None = None,
) -> str | None:
    current = _entity_node_label(summary)
    nodes = [current]
    edges: list[tuple[str, str]] = []
    links: dict[str, str] = {}

    current_file = summary.get("file")
    current_stem = _module_page_stem(
        str(current_file) if current_file else None, module_page_map
    )
    if current_stem:
        links[current] = f"../modules/{current_stem}.md"

    for base in summary.get("bases", []) or []:
        target = _class_ref_label(base)
        nodes.append(target)
        edges.append((current, target))
        stem = _module_page_stem(base.get("file"), module_page_map)
        if stem:
            links[target] = f"../modules/{stem}.md"

    for subclass in summary.get("subclasses", []) or []:
        source = _class_ref_label(subclass)
        nodes.append(source)
        edges.append((source, current))
        stem = _module_page_stem(subclass.get("file"), module_page_map)
        if stem:
            links[source] = f"../modules/{stem}.md"

    for reference in summary.get("references", []) or []:
        source = _reference_label(reference)
        nodes.append(source)
        edges.append((source, current))
        stem = _module_page_stem(reference.get("file"), module_page_map)
        if stem:
            links[source] = f"../modules/{stem}.md"

    if not edges:
        return None
    if diagram_style is None:
        diagram_style = _generated_diagram_style(
            "relationships",
            entity=summary.get("name"),
            file=summary.get("file"),
        )
    return flowchart(nodes, edges, direction="LR", links=links, style=diagram_style)


def _relationship_source_cell(
    record: Mapping, module_page_map: Mapping[str, str] | None
) -> str:
    filepath = record.get("file")
    return _module_link(str(filepath) if filepath else None, module_page_map)


def _is_haskell_declaration_summary(summary: Mapping) -> bool:
    filepath = summary.get("file")
    if not filepath or not _is_haskell_filepath(str(filepath)):
        return False
    kind = summary.get("kind")
    normalized = str(kind).strip().casefold() if kind not in (None, "") else ""
    return normalized in _HASKELL_DECLARATION_LABELS


def _append_haskell_relationship_summary_table(
    lines: list[str],
    summary: Mapping,
    module_page_map: Mapping[str, str] | None,
) -> None:
    lines.append("| Module | Declaration kind |")
    lines.append("|---|---|")
    lines.append(
        f"| {_module_link(summary.get('file'), module_page_map)} | "
        f"{_haskell_declaration_label(summary.get('kind'))} |"
    )
    lines.append("")


def _append_default_relationship_summary_table(
    lines: list[str],
    summary: Mapping,
    module_page_map: Mapping[str, str] | None,
) -> None:
    lines.append("| Module | Methods | Attributes |")
    lines.append("|---|---:|---|")
    lines.append(
        "| "
        + " | ".join(
            [
                _module_link(summary.get("file"), module_page_map),
                str(summary.get("methods_count", 0)),
                _code_join(list(summary.get("attributes", []) or [])),
            ]
        )
        + " |"
    )
    lines.append("")


def _append_entity_relationship_tables(
    lines: list[str],
    summary: Mapping,
    module_page_map: Mapping[str, str] | None,
) -> None:
    lines.extend(["### Summary", ""])
    if _is_haskell_declaration_summary(summary):
        _append_haskell_relationship_summary_table(lines, summary, module_page_map)
    else:
        _append_default_relationship_summary_table(lines, summary, module_page_map)

    structure_rows = []
    for base in summary.get("bases", []) or []:
        structure_rows.append(("Base", base))
    for subclass in summary.get("subclasses", []) or []:
        structure_rows.append(("Subclass", subclass))
    if structure_rows:
        lines.extend(["### Structure", ""])
        lines.append("| Kind | Entity | Module |")
        lines.append("|---|---|---|")
        for kind, item in structure_rows:
            lines.append(
                f"| {kind} | `{_md_cell(item.get('name'))}` | "
                f"{_relationship_source_cell(item, module_page_map)} |"
            )
        lines.append("")

    references = list(summary.get("references", []) or [])
    if references:
        lines.extend(["### References", ""])
        lines.append("| Reference | Kind | Source |")
        lines.append("|---|---|---|")
        for reference in references:
            symbol = reference.get("symbol") or reference.get("module") or "module"
            lines.append(
                f"| `{_md_cell(symbol)}` | {_md_cell(reference.get('kind'))} | "
                f"{_relationship_source_cell(reference, module_page_map)} |"
            )
        lines.append("")


def _generate_entity_relationship_section(
    summary: Mapping | None,
    module_page_map: Mapping[str, str] | None = None,
    diagram_style: Mapping[str, Any] | None = None,
) -> list[str]:
    lines = [
        "## Relationships",
        "",
        "<!-- Auto-generated relationship summary. Do not edit by hand. -->",
    ]
    if not summary:
        lines.extend(["*No generated relationships detected.*", ""])
        return lines

    diagram = _entity_relationship_graph(summary, module_page_map, diagram_style)
    if diagram:
        lines.append(diagram)
    else:
        lines.append("*No generated relationships detected.*")
    lines.append("")
    _append_entity_relationship_tables(lines, summary, module_page_map)
    return lines


def _module_map_node_link(
    node: str, module_page_map: Mapping[str, str] | None = None
) -> str | None:
    stem = (module_page_map or {}).get(node)
    if stem:
        return f"../modules/{stem}.md"
    return None


def _module_dependency_graph(
    summary: Mapping,
    module_page_map: Mapping[str, str] | None,
    diagram_style: Mapping[str, Any] | None = None,
) -> str | None:
    edges = list(summary.get("edges", []) or [])
    if not edges:
        return None
    nodes = list(summary.get("nodes", []) or [])
    links = {
        str(node): link
        for node in nodes
        for link in [_module_map_node_link(str(node), module_page_map)]
        if link
    }
    if diagram_style is None:
        diagram_style = _generated_diagram_style(
            "module_dependency",
            file=summary.get("file"),
        )
    return flowchart(
        nodes,
        edges,
        direction="LR",
        links=links,
        highlight_edges=summary.get("cycle_edges", []),
        style=diagram_style,
    )


def _module_dependency_cell(
    item: object, module_page_map: Mapping[str, str] | None
) -> str:
    if isinstance(item, Mapping):
        return f"`{_md_cell(item.get('package'))}` ({_md_cell(item.get('count'))})"
    return _module_link(str(item), module_page_map)


def _append_module_dependency_tables(
    lines: list[str],
    summary: Mapping,
    module_page_map: Mapping[str, str] | None,
) -> None:
    rows = [("Inbound", item) for item in summary.get("inbound", []) or []] + [
        ("Outbound", item) for item in summary.get("outbound", []) or []
    ]
    if rows:
        lines.extend(["### Internal neighbors", ""])
        lines.append("| Direction | Module |")
        lines.append("|---|---|")
        for direction, item in rows:
            lines.append(
                f"| {direction} | {_module_dependency_cell(item, module_page_map)} |"
            )
        lines.append("")

    external = summary.get("external", {}) or {}
    if external:
        lines.extend(["### External packages", ""])
        lines.append("| Language | Used packages | Undeclared packages |")
        lines.append("|---|---:|---:|")
        for language in sorted(external):
            data = external[language]
            lines.append(
                f"| {_md_cell(language)} | {_md_cell(data.get('used_count'))} | "
                f"{_md_cell(data.get('undeclared_count'))} |"
            )
        lines.append("")

    overflow = summary.get("overflow", {}) or {}
    if overflow.get("omitted_count"):
        lines.append(
            f"> Showing {overflow.get('node_limit')} local graph nodes; "
            f"{overflow.get('omitted_count')} neighbor(s) are summarized by package."
        )
        lines.append("")


def _generate_module_dependency_section(
    summary: Mapping | None,
    module_page_map: Mapping[str, str] | None = None,
    diagram_style: Mapping[str, Any] | None = None,
) -> list[str]:
    lines = [
        "## Local dependency map",
        "",
        "<!-- Auto-generated local dependency summary. Do not edit by hand. -->",
    ]
    if not summary:
        lines.extend(["*No internal module dependencies detected.*", ""])
        return lines

    diagram = _module_dependency_graph(summary, module_page_map, diagram_style)
    if diagram:
        if summary.get("cycle_participation"):
            lines.append(
                "<!-- Thick arrows (==>) mark edges inside an import cycle. -->"
            )
        lines.append(diagram)
    else:
        lines.append("*No internal module dependencies detected.*")
    lines.append("")
    _append_module_dependency_tables(lines, summary, module_page_map)
    return lines


def _append_relationships_to_entity(
    lines: list[str],
    name: str,
    filepath: str,
    relationships: dict,
    *,
    relationship_summary: Mapping | None,
    module_page_map: Mapping[str, str] | None,
    diagram_style: Mapping[str, Any] | None,
) -> None:
    if relationship_summary is not None:
        lines.extend(
            _generate_entity_relationship_section(
                relationship_summary, module_page_map, diagram_style
            )
        )
        return

    rels = relationships.get((name, filepath), relationships.get(name, []))
    lines.append("## Relationships")
    lines.append("")
    if rels:
        for r in rels:
            page = r.get("module_page", r["module"])
            mod_link = f"[{r['module']}](../modules/{page}.md)"
            if r.get("function"):
                lines.append(f"- **{r['rel']}**: `{r['function']}()` in {mod_link}")
            else:
                lines.append(f"- **{r['rel']}**: {mod_link}")
    else:
        lines.append("*No cross-module references detected.*")
    lines.append("")


def _generate_haskell_entity_md(
    class_info: dict,
    filepath: str,
    relationships: dict,
    mod_page_name: str | None = None,
    *,
    relationship_summary: Mapping | None = None,
    module_page_map: Mapping[str, str] | None = None,
    diagram_style: Mapping[str, Any] | None = None,
) -> str:
    name = class_info["name"]
    line = class_info.get("line", "?")
    docstring = class_info.get("docstring", "")
    kind_label = _haskell_declaration_label(class_info.get("kind"))
    mod_name = (
        mod_page_name if mod_page_name is not None else _module_name_from_path(filepath)
    )

    lines = [
        f"# {name}",
        "",
        f"**Location:** `{filepath}:{line}`",
        f"**Kind:** `{kind_label}`",
        f"**Module:** [{mod_name}](../modules/{mod_name}.md)",
        "",
        "## Description",
        "",
    ]
    if docstring:
        lines.append(_sanitize_source_doc_markdown(docstring))
    else:
        lines.append(f"_Auto-generated from `{name}` in `{filepath}`._")
    lines.extend(
        [
            "",
            "## Declaration",
            "",
            "| Kind | Line | Module |",
            "|---|---:|---|",
            f"| {kind_label} | {line} | [{mod_name}](../modules/{mod_name}.md) |",
            "",
        ]
    )

    _append_relationships_to_entity(
        lines,
        name,
        filepath,
        relationships,
        relationship_summary=relationship_summary,
        module_page_map=module_page_map,
        diagram_style=diagram_style,
    )
    return "\n".join(lines)


def _append_import_section(
    lines: list[str], imports: list[dict], *, haskell: bool
) -> None:
    if not imports:
        return

    lines.append("## Imports")
    lines.append("")
    if haskell:
        lines.append("| Module | Qualified | Alias | Line |")
        lines.append("|---|---|---|---:|")
        for imp in sorted(
            imports,
            key=lambda item: (
                str(item.get("module", "")),
                _line_sort_value(item.get("line")),
                str(item.get("alias") or ""),
            ),
        ):
            lines.append(
                f"| `{_md_cell(imp.get('module'))}` | {_yes_no(imp.get('qualified'))} | "
                f"{_code_or_dash(imp.get('alias'))} | {_dash(imp.get('line'))} |"
            )
        lines.append("")
        return

    grouped: dict[str, list[str]] = defaultdict(list)
    for imp in imports:
        grouped[imp["module"]].append(imp["name"])

    lines.append("| Source | Symbols |")
    lines.append("|--------|---------|")
    for module, names in sorted(grouped.items()):
        symbols = ", ".join(f"`{n}`" for n in names) if names else "—"
        lines.append(f"| `{module}` | {symbols} |")
    lines.append("")


def _append_haskell_declarations(
    lines: list[str],
    declarations: list[dict],
    entity_page_map: Mapping | None,
    *,
    filepath: str | None = None,
    entity_occurrence_page_map: Mapping[EntityOccurrenceKey, str] | None = None,
) -> None:
    if not declarations:
        return
    lines.append("## Declarations")
    lines.append("")
    lines.append("| Declaration | Kind | Line | Description |")
    lines.append("|---|---|---:|---|")
    seen_names: defaultdict[str, int] = defaultdict(int)
    for declaration in declarations:
        name = declaration["name"]
        seen_names[name] += 1
        page_name = _entity_page_from_maps(
            name,
            filepath,
            seen_names[name],
            entity_page_map,
            entity_occurrence_page_map,
        )
        entity_link = f"[{name}](../entities/{page_name}.md)"
        kind = _haskell_declaration_label(declaration.get("kind"))
        doc = _source_doc_first_line(declaration.get("docstring")) or "—"
        lines.append(
            f"| {entity_link} | {kind} | {_dash(declaration.get('line'))} | {doc} |"
        )
    lines.append("")


def _entity_page_from_maps(
    name: str,
    filepath: str | None,
    occurrence: int,
    entity_page_map: Mapping | None,
    entity_occurrence_page_map: Mapping[EntityOccurrenceKey, str] | None = None,
) -> str:
    if filepath is not None and entity_occurrence_page_map is not None:
        page_name = entity_occurrence_page_map.get((name, filepath, occurrence))
        if page_name:
            return page_name
    return (entity_page_map or {}).get(name, _page_name_for_entity(name))


def _append_haskell_functions(lines: list[str], functions: list[dict]) -> None:
    if not functions:
        return
    lines.append("## Functions")
    lines.append("")
    lines.append("| Function | Kind | Signature | Line | Description |")
    lines.append("|---|---|---|---:|---|")
    for fn in functions:
        doc = _source_doc_first_line(fn.get("docstring")) or "—"
        lines.append(
            f"| `{fn['name']}` | {_haskell_function_label(fn.get('kind'))} | "
            f"{_code_or_dash(fn.get('signature'))} | {_dash(fn.get('line'))} | {doc} |"
        )
    lines.append("")


def _append_module_signals_section(lines: list[str], file_data: Mapping) -> None:
    if file_data.get("language") not in {"typescript", "javascript"}:
        return

    rows: list[tuple[str, str]] = []
    exports = [str(name) for name in file_data.get("exports", []) if str(name)]
    if exports:
        rows.append(("Exports", ", ".join(f"`{name}`" for name in exports)))

    constants = [
        str(constant.get("name"))
        for constant in file_data.get("constants", [])
        if isinstance(constant, Mapping) and constant.get("name")
    ]
    if constants:
        rows.append(("Constants", ", ".join(f"`{name}`" for name in constants)))

    module_calls = [
        f"`{_format_side_effect_call(call)}`"
        for call in file_data.get("module_calls", [])
        if isinstance(call, Mapping)
    ]
    if module_calls:
        rows.append(("Module calls", ", ".join(module_calls)))

    if not rows:
        return

    lines.append("## Module Signals")
    lines.append("")
    lines.append("| Signal | Values |")
    lines.append("|--------|--------|")
    for label, value in rows:
        lines.append(f"| {label} | {value} |")
    lines.append("")


def _entity_kind_label(class_info: Mapping) -> str:
    if class_info.get("model_kind") == "pydantic":
        return "Pydantic model"
    return {
        "class": "Class",
        "enum": "Enum",
        "type_alias": "Type alias",
    }.get(str(class_info.get("kind") or "class"), "Class")


def _field_wire_name(attribute: Mapping) -> str:
    alias = attribute.get("alias")
    input_name = attribute.get("validation_alias") or alias
    output_name = attribute.get("serialization_alias") or alias
    if input_name and output_name and input_name != output_name:
        return f"input: {input_name}; output: {output_name}"
    if input_name or output_name:
        return str(input_name or output_name)
    for unknown in attribute.get("unknowns", []):
        if unknown.get("property") in {
            "alias",
            "validation_alias",
            "serialization_alias",
        }:
            return f"unknown ({unknown.get('expression', '?')})"
    return str(attribute.get("name") or "—")


def _field_default(attribute: Mapping) -> str:
    if attribute.get("value") not in (None, ""):
        return _table_inline_code(attribute["value"])
    if "default" in attribute:
        return _table_inline_code(attribute["default"])
    if attribute.get("default_factory"):
        return f"factory: {_table_inline_code(attribute['default_factory'])}"
    return "—"


def _field_constraints(attribute: Mapping) -> str:
    parts = [
        f"{name}={value}" for name, value in attribute.get("constraints", {}).items()
    ]
    parts.extend(str(value) for value in attribute.get("annotated_metadata", []))
    parts.extend(
        f"{str(unknown.get('property')).split(':', 1)[-1]}=unknown "
        f"({unknown.get('expression', '?')})"
        for unknown in attribute.get("unknowns", [])
        if str(unknown.get("property", "")).startswith("constraint:")
    )
    return _table_text("; ".join(parts)) if parts else "—"


def _model_config_value(setting: Mapping) -> str:
    unknowns = setting.get("unknowns", [])
    if unknowns:
        expression = unknowns[0].get("expression", "?")
        return _table_inline_code(f"unknown ({expression})")
    return _table_inline_code(setting.get("value"))


def _append_model_contract_sections(lines: list[str], class_info: Mapping) -> None:
    model_config = class_info.get("model_config", [])
    if model_config:
        lines.extend(
            [
                "## Model Configuration",
                "",
                "| Setting | Value | Source |",
                "|---------|-------|--------|",
            ]
        )
        for setting in model_config:
            lines.append(
                f"| `{_table_text(setting.get('name'))}` | "
                f"{_model_config_value(setting)} | "
                f"{_table_text(setting.get('source'))} |"
            )
        lines.append("")

    validators = [
        (method, method.get("validator"))
        for method in class_info.get("methods", [])
        if method.get("validator")
    ]
    if validators:
        lines.extend(
            [
                "## Validators",
                "",
                "| Method | Scope | Fields | Mode | Options |",
                "|--------|-------|--------|------|---------|",
            ]
        )
        for method, validator in validators:
            fields = ", ".join(validator.get("fields", [])) or "—"
            options = "; ".join(
                f"{name}={value}"
                for name, value in validator.get("options", {}).items()
            )
            lines.append(
                f"| `{_table_text(method.get('name'))}` | "
                f"{_table_text(validator.get('kind'))} | {_table_text(fields)} | "
                f"{_table_text(validator.get('mode'))} | {_table_text(options)} |"
            )
        lines.append("")


def _append_attribute_contract(lines: list[str], class_info: Mapping) -> None:
    attributes = list(class_info.get("attributes", []))
    lines.extend(["## Attributes", ""])
    if not attributes:
        lines.extend(["*No annotated attributes found.*", ""])
        return

    if class_info.get("kind") == "enum":
        lines.extend(
            [
                "| Name | Declared value | Description |",
                "|------|-------|-------------|",
            ]
        )
        for attribute in attributes:
            lines.append(
                f"| `{_table_text(attribute.get('name'))}` | "
                f"{_field_default(attribute)} | "
                f"{_table_text(attribute.get('description'))} |"
            )
        lines.append("")
        return

    enriched = class_info.get("model_kind") == "pydantic" or any(
        any(
            key in attribute
            for key in (
                "alias",
                "validation_alias",
                "serialization_alias",
                "constraints",
                "annotated_metadata",
            )
        )
        for attribute in attributes
    )
    if not enriched:
        lines.extend(
            [
                "| Name | Type | Default | Description |",
                "|------|------|---------|-------------|",
            ]
        )
        for attribute in attributes:
            default = (
                _table_inline_code(attribute["default"])
                if attribute.get("default")
                else "*required*"
            )
            lines.append(
                f"| `{_table_text(attribute.get('name'))}` | "
                f"{_table_inline_code(attribute.get('type'))} | {default} | "
                f"{_table_text(attribute.get('description'))} |"
            )
        lines.append("")
        return

    lines.extend(
        [
            "| Name | Type | Wire name | Required | Nullable | Default | "
            "Constraints | Examples | Description |",
            "|------|------|-----------|----------|----------|---------|"
            "-------------|-------------|----------|",
        ]
    )
    for attribute in attributes:
        required = "Yes" if attribute.get("required") else "No"
        nullable = "Yes" if attribute.get("nullable") else "No"
        example_values = list(attribute.get("examples", []))
        example_values.extend(
            f"unknown ({unknown.get('expression', '?')})"
            for unknown in attribute.get("unknowns", [])
            if unknown.get("property") == "examples"
        )
        examples = ", ".join(example_values)
        lines.append(
            f"| `{_table_text(attribute.get('name'))}` | "
            f"{_table_inline_code(attribute.get('type'))} | "
            f"{_table_inline_code(_field_wire_name(attribute))} | {required} | "
            f"{nullable} | {_field_default(attribute)} | "
            f"{_field_constraints(attribute)} | "
            f"{_table_text(examples)} | "
            f"{_table_text(attribute.get('description'))} |"
        )
    lines.append("")


def _generate_entity_md(
    class_info: dict,
    filepath: str,
    relationships: dict,
    mod_page_name: str | None = None,
    *,
    relationship_summary: Mapping | None = None,
    module_page_map: Mapping[str, str] | None = None,
    diagram_style: Mapping[str, Any] | None = None,
) -> str:
    """Generate comprehensive markdown for a class entity."""
    if _is_haskell_filepath(filepath):
        return _generate_haskell_entity_md(
            class_info,
            filepath,
            relationships,
            mod_page_name,
            relationship_summary=relationship_summary,
            module_page_map=module_page_map,
            diagram_style=diagram_style,
        )

    name = class_info["name"]
    bases = class_info.get("bases", [])
    line = class_info.get("line", "?")
    docstring = class_info.get("docstring", "")
    decorators = class_info.get("decorators", [])
    methods = class_info.get("methods", [])
    mod_name = (
        mod_page_name if mod_page_name is not None else _module_name_from_path(filepath)
    )

    bases_str = ", ".join(f"`{b}`" for b in bases) if bases else "—"

    lines = [
        f"# {name}",
        "",
        f"**Location:** `{filepath}:{line}`",
        f"**Kind:** {_entity_kind_label(class_info)}",
        f"**Bases:** {bases_str}",
        f"**Module:** [{mod_name}](../modules/{mod_name}.md)",
    ]
    if class_info.get("target"):
        lines.append(f"**Target:** {_table_inline_code(class_info['target'])}")
    lines.append("")

    if decorators:
        lines.append(f"**Decorators:** {', '.join(f'`@{d}`' for d in decorators)}")
        lines.append("")

    # Description
    lines.append("## Description")
    lines.append("")
    if docstring:
        lines.append(_sanitize_source_doc_markdown(docstring))
    else:
        lines.append(f"_Auto-generated from `{name}` in `{filepath}`._")
    lines.append("")

    _append_model_contract_sections(lines, class_info)
    _append_attribute_contract(lines, class_info)

    # Methods
    lines.append("## Methods")
    lines.append("")
    if methods:
        lines.append("| Method | Signature | Decorators | Description |")
        lines.append("|--------|-----------|------------|-------------|")
        for m in methods:
            sig = _format_signature(m)
            decs = (
                ", ".join(_table_inline_code(f"@{d}") for d in m.get("decorators", []))
                or "—"
            )
            doc = _source_doc_first_line(m.get("docstring")) or "—"
            async_tag = "*(async)* " if m.get("is_async") else ""
            lines.append(
                f"| `{_table_text(m['name'])}` | {async_tag}{_table_inline_code(sig)} | "
                f"{decs} | {_table_text(doc)} |"
            )
    else:
        lines.append("*No public methods. Inherits from base classes.*")
    lines.append("")

    # Relationships
    _append_relationships_to_entity(
        lines,
        name,
        filepath,
        relationships,
        relationship_summary=relationship_summary,
        module_page_map=module_page_map,
        diagram_style=diagram_style,
    )

    return "\n".join(lines)


def _generate_module_md(
    filepath: str,
    file_data: dict,
    entity_page_map: dict | None = None,
    *,
    module_dependency_map: Mapping | None = None,
    module_page_map: Mapping[str, str] | None = None,
    entity_occurrence_page_map: Mapping[EntityOccurrenceKey, str] | None = None,
    diagram_style: Mapping[str, Any] | None = None,
) -> str:
    """Generate comprehensive markdown for a module page."""
    is_haskell = _is_haskell_file_data(file_data)
    declared_haskell_module = _haskell_module_name(file_data)
    mod_name = _display_module_name(filepath, file_data)
    classes = file_data.get("classes", [])
    functions = file_data.get("functions", [])
    imports = file_data.get("imports", [])
    module_docstring = file_data.get("module_docstring", "")

    lines = [
        f"# {mod_name} Module",
        "",
        f"**Path:** `{filepath}`",
    ]
    if declared_haskell_module:
        lines.append(f"**Declared module:** `{declared_haskell_module}`")
    lines.append("")

    # Description
    lines.append("## Description")
    lines.append("")
    if module_docstring:
        lines.append(_sanitize_source_doc_markdown(module_docstring))
    else:
        lines.append(f"_Auto-generated from `{filepath}`._")
    lines.append("")

    _append_import_section(lines, imports, haskell=is_haskell)
    _append_module_signals_section(lines, file_data)

    if module_dependency_map is not None:
        lines.extend(
            _generate_module_dependency_section(
                module_dependency_map, module_page_map, diagram_style
            )
        )

    # Classes / declarations
    if is_haskell:
        _append_haskell_declarations(
            lines,
            classes,
            entity_page_map,
            filepath=filepath,
            entity_occurrence_page_map=entity_occurrence_page_map,
        )
    elif classes:
        lines.append("## Classes")
        lines.append("")
        include_kind = any(
            item.get("kind") not in (None, "", "class") for item in classes
        )
        if include_kind:
            lines.append("| Class | Kind | Line | Bases / Target | Description |")
            lines.append("|-------|------|------|----------------|-------------|")
        else:
            lines.append("| Class | Line | Bases | Description |")
            lines.append("|-------|------|-------|-------------|")
        seen_names: defaultdict[str, int] = defaultdict(int)
        for c in classes:
            seen_names[c["name"]] += 1
            page_name = _entity_page_from_maps(
                c["name"],
                filepath,
                seen_names[c["name"]],
                entity_page_map,
                entity_occurrence_page_map,
            )
            entity_link = f"[{c['name']}](../entities/{page_name}.md)"
            bases = ", ".join(_table_inline_code(base) for base in c.get("bases", []))
            bases = bases or _table_inline_code(c.get("target"))
            doc = _source_doc_first_line(c.get("docstring")) or "—"
            if include_kind:
                lines.append(
                    f"| {entity_link} | {_entity_kind_label(c)} | "
                    f"{c.get('line', '?')} | {bases} | {_table_text(doc)} |"
                )
            else:
                lines.append(
                    f"| {entity_link} | {c.get('line', '?')} | {bases} | "
                    f"{_table_text(doc)} |"
                )
        lines.append("")

    # Functions
    if is_haskell:
        _append_haskell_functions(lines, functions)
    elif functions:
        lines.append("## Functions")
        lines.append("")
        lines.append("| Function | Signature | Decorators | Description |")
        lines.append("|----------|-----------|------------|-------------|")
        for fn in functions:
            sig = _format_signature(fn)
            decs = (
                ", ".join(_table_inline_code(f"@{d}") for d in fn.get("decorators", []))
                or "—"
            )
            doc = _source_doc_first_line(fn.get("docstring")) or "—"
            async_tag = "*(async)* " if fn.get("is_async") else ""
            lines.append(
                f"| `{_table_text(fn['name'])}` | {async_tag}{_table_inline_code(sig)} | "
                f"{decs} | {_table_text(doc)} |"
            )
        lines.append("")

    return "\n".join(lines)


def _flow_index_category(flow: dict) -> str:
    """Category for a flow index entry, derived from the id prefix when absent."""
    return flow.get("category") or flow["id"].split("-", 1)[0]


def _overview_target(count: int, heading: str) -> str:
    if count <= 0:
        return "No pages"
    anchor = heading.casefold().replace(" ", "-")
    return f"[Open section](#{anchor})"


def _overview_row(label: str, count: int, target: str) -> str:
    return f"| {label} | {count} | {target} |"


def _append_surface_overview(
    lines: list[str],
    *,
    entity_count: int,
    module_count: int,
    workflow_count: int,
    guide_count: int,
    flow_count: int,
    infrastructure_count: int,
    api_contracts_present: bool,
    architecture_count: int,
    log_present: bool,
) -> None:
    lines.extend(
        [
            "## Surface Overview",
            "",
            "| Surface | Count | Start here |",
            "|---|---:|---|",
            _overview_row(
                _SURFACE_LABELS[PageKind.ENTITIES],
                entity_count,
                _overview_target(entity_count, _SURFACE_LABELS[PageKind.ENTITIES]),
            ),
            _overview_row(
                _SURFACE_LABELS[PageKind.MODULES],
                module_count,
                _overview_target(module_count, _SURFACE_LABELS[PageKind.MODULES]),
            ),
            _overview_row(
                _SURFACE_LABELS[PageKind.WORKFLOWS],
                workflow_count,
                _overview_target(workflow_count, _SURFACE_LABELS[PageKind.WORKFLOWS]),
            ),
            _overview_row(
                _SURFACE_LABELS[PageKind.GUIDES],
                guide_count,
                _overview_target(guide_count, _SURFACE_LABELS[PageKind.GUIDES]),
            ),
            _overview_row(
                _SURFACE_LABELS[PageKind.FLOWS],
                flow_count,
                _overview_target(flow_count, _SURFACE_LABELS[PageKind.FLOWS]),
            ),
            _overview_row(
                _SURFACE_LABELS[PageKind.INFRASTRUCTURE],
                infrastructure_count,
                _overview_target(
                    infrastructure_count, _SURFACE_LABELS[PageKind.INFRASTRUCTURE]
                ),
            ),
            _overview_row(
                _SURFACE_LABELS[PageKind.API_CONTRACTS],
                1 if api_contracts_present else 0,
                f"[Open contracts]({canonical_path(PageKind.API_CONTRACTS)})"
                if api_contracts_present
                else "No pages",
            ),
            _overview_row(
                "Dependency architecture",
                architecture_count,
                _overview_target(architecture_count, "Dependency Architecture"),
            ),
            _overview_row(
                _SURFACE_LABELS[PageKind.LOG],
                1 if log_present else 0,
                f"[Open log]({canonical_path(PageKind.LOG)})"
                if log_present
                else "No pages",
            ),
            "",
        ]
    )


def _append_index_entities(lines: list[str], entity_names: list[str]) -> None:
    if not entity_names:
        return
    lines.append(f"## {_SURFACE_LABELS[PageKind.ENTITIES]}")
    lines.append("")
    for name in sorted(entity_names):
        lines.append(f"- [{name}]({canonical_path(PageKind.ENTITIES, name)})")
    lines.append("")


def _append_index_modules(lines: list[str], module_entries: list[dict]) -> None:
    if not module_entries:
        return
    lines.append(f"## {_SURFACE_LABELS[PageKind.MODULES]}")
    lines.append("")
    for entry in sorted(module_entries, key=lambda e: e["name"]):
        desc = _source_doc_first_line(entry.get("docstring"))
        source_path = entry.get("path")
        suffix = f" - {desc}" if desc else f" - `{source_path}`" if source_path else ""
        path = canonical_path(PageKind.MODULES, entry["name"])
        lines.append(f"- [{entry['name']}]({path}){suffix}")
    lines.append("")


def _append_index_workflows(
    lines: list[str], workflow_entries: list[dict] | None
) -> None:
    if not workflow_entries:
        return
    lines.append(f"## {_SURFACE_LABELS[PageKind.WORKFLOWS]}")
    lines.append("")
    for wf in sorted(workflow_entries, key=lambda w: w["name"]):
        entry_point = wf.get("entry", "")
        path = canonical_path(PageKind.WORKFLOWS, wf["name"])
        lines.append(f"- [{wf['name']}]({path}) - entry: `{entry_point}`")
    lines.append("")


def _append_index_guides(lines: list[str], guide_entries: list[dict] | None) -> None:
    if not guide_entries:
        return
    lines.append(f"## {_SURFACE_LABELS[PageKind.GUIDES]}")
    lines.append("")
    for guide in sorted(guide_entries, key=lambda entry: entry["name"]):
        label = guide.get("label") or guide["name"]
        path = canonical_path(PageKind.GUIDES, guide["name"])
        lines.append(f"- [{label}]({path})")
    lines.append("")


def _append_index_user_flows(lines: list[str], flow_entries: list[dict] | None) -> None:
    """Append the grouped "User Flows" section to *lines* (in place).

    Tolerates minimal entries (``{"id"}``) so ``sync`` can re-index existing flow
    pages without re-running entry-point detection.
    """
    if not flow_entries:
        return
    lines.append("## User Flows")
    lines.append("")
    for category in sorted({_flow_index_category(f) for f in flow_entries}):
        lines.append(f"**{category}**")
        lines.append("")
        for flow in sorted(
            (f for f in flow_entries if _flow_index_category(f) == category),
            key=lambda f: f["id"],
        ):
            entry = flow.get("entry", "")
            suffix = f" - entry: `{entry}`" if entry else ""
            path = canonical_path(PageKind.FLOWS, flow["id"])
            lines.append(f"- [{flow['id']}]({path}){suffix}")
        lines.append("")


def _append_index_infrastructure(
    lines: list[str], infra_entries: list[dict] | None
) -> None:
    if not infra_entries:
        return
    lines.append(f"## {_SURFACE_LABELS[PageKind.INFRASTRUCTURE]}")
    lines.append("")
    for entry in sorted(infra_entries, key=lambda e: e["name"]):
        label = entry.get("label") or entry["name"]
        desc = entry.get("type", "")
        suffix = f" - {desc}" if desc else ""
        path = canonical_path(PageKind.INFRASTRUCTURE, entry["name"])
        lines.append(f"- [{label}]({path}){suffix}")
    lines.append("")


def _append_index_api_contracts(
    lines: list[str], *, api_contracts_present: bool
) -> None:
    if not api_contracts_present:
        return
    lines.append(f"## {_SURFACE_LABELS[PageKind.API_CONTRACTS]}")
    lines.append("")
    lines.append(
        f"- [Production HTTP API inventory]({canonical_path(PageKind.API_CONTRACTS)})"
    )
    lines.append("")


def _architecture_path(page: str) -> str:
    if page == PageKind.DEPENDENCIES.value:
        return canonical_path(PageKind.DEPENDENCIES)
    if page == PageKind.LOAD_ORDER.value:
        return canonical_path(PageKind.LOAD_ORDER)
    return f"{page}.md"


def _architecture_order(entry: dict) -> int:
    order = {
        PageKind.DEPENDENCIES.value: 0,
        PageKind.LOAD_ORDER.value: 1,
    }
    return order.get(entry.get("page", ""), 99)


def _append_index_architecture(
    lines: list[str], architecture_entries: list[dict] | None
) -> None:
    """Append the dependency architecture section linking top-level analysis pages.

    Keeps ``dependencies.md`` / ``load-order.md`` linked from the index so lint
    does not flag them as orphans. Omitted entirely when no such pages exist.
    """
    if not architecture_entries:
        return
    lines.append("## Dependency Architecture")
    lines.append("")
    for entry in sorted(
        architecture_entries,
        key=lambda e: (_architecture_order(e), e["page"]),
    ):
        lines.append(f"- [{entry['name']}]({_architecture_path(entry['page'])})")
    lines.append("")


def _append_index_log(lines: list[str], *, log_present: bool) -> None:
    if not log_present:
        return
    lines.append(f"## {_SURFACE_LABELS[PageKind.LOG]}")
    lines.append("")
    lines.append(f"- [Architectural log]({canonical_path(PageKind.LOG)})")
    lines.append("")


def _generate_index_md(
    entity_names: list[str],
    module_entries: list[dict],
    workflow_entries: list[dict] | None = None,
    guide_entries: list[dict] | None = None,
    infra_entries: list[dict] | None = None,
    flow_entries: list[dict] | None = None,
    architecture_entries: list[dict] | None = None,
    *,
    api_contracts_present: bool = False,
    log_present: bool = True,
) -> str:
    """Generate the full index.md content."""
    workflow_entries = workflow_entries or []
    guide_entries = guide_entries or []
    infra_entries = infra_entries or []
    flow_entries = flow_entries or []
    architecture_entries = architecture_entries or []
    lines = [
        "# LLM Wiki Index",
        "",
        "Use this landing page to choose the right wiki surface.",
        "",
    ]

    _append_surface_overview(
        lines,
        entity_count=len(entity_names),
        module_count=len(module_entries),
        workflow_count=len(workflow_entries),
        guide_count=len(guide_entries),
        flow_count=len(flow_entries),
        infrastructure_count=len(infra_entries),
        api_contracts_present=api_contracts_present,
        architecture_count=len(architecture_entries),
        log_present=log_present,
    )
    _append_index_entities(lines, entity_names)
    _append_index_modules(lines, module_entries)
    _append_index_workflows(lines, workflow_entries)
    _append_index_guides(lines, guide_entries)
    _append_index_user_flows(lines, flow_entries)
    _append_index_infrastructure(lines, infra_entries)
    _append_index_api_contracts(lines, api_contracts_present=api_contracts_present)
    _append_index_architecture(lines, architecture_entries)
    _append_index_log(lines, log_present=log_present)

    return "\n".join(lines)


def _workflow_module_refs(
    wf: dict,
    module_page_map: Mapping[str, str] | None = None,
) -> list[tuple[str, str]]:
    """Return ``(label, page_stem)`` pairs for workflow module links."""
    page_map = module_page_map or {}
    paths = wf.get("modules_touched_paths") or []
    if paths:
        refs = []
        for path in paths:
            page = page_map.get(path, _module_name_from_path(path))
            refs.append((page, page))
        return sorted(set(refs), key=lambda item: item[0])

    return [(m, m) for m in wf.get("modules_touched", [])]


def _generate_workflow_md(
    name: str,
    wf: dict,
    module_page_map: Mapping[str, str] | None = None,
) -> str:
    """Generate a skeleton workflow page from call-graph data."""
    entry = wf["entry"]
    modules = _workflow_module_refs(wf, module_page_map)
    chain = wf.get("chain", [])
    docstring = wf.get("docstring", "")

    lines = [
        f"# {name}",
        "",
        f"**Entry point:** `{entry}`",
        f"**Modules involved:** {', '.join(f'[{label}](../modules/{page}.md)' for label, page in modules)}",
        "",
    ]

    if docstring:
        lines.append(f"> {_sanitize_source_doc_markdown(docstring)}")
        lines.append("")

    lines.append("## Sequence")
    lines.append("")
    lines.append(
        "<!-- Auto-detected call chain. Refine order and conditions after review. -->"
    )
    if chain:
        for i, step in enumerate(chain, 1):
            lines.append(f"{i}. `{step}`")
    else:
        lines.append("*No detailed chain extracted — refine manually.*")
    lines.append("")

    lines.append("## Touches")
    lines.append("")
    for label, page in modules:
        lines.append(f"- [{label}](../modules/{page}.md)")
    lines.append("")

    return "\n".join(lines)


def _flow_module_refs(
    flow: dict,
    module_page_map: Mapping[str, str] | None = None,
) -> list[tuple[str, str]]:
    """Return sorted ``(label, page_stem)`` pairs for a flow's touched modules."""
    page_map = module_page_map or {}
    refs = [
        (
            page_map.get(path, _module_name_from_path(path)),
            page_map.get(path, _module_name_from_path(path)),
        )
        for path in flow.get("modules_touched", [])
    ]
    return sorted(set(refs), key=lambda item: item[0])


def _flow_related_module_refs(
    flow: dict,
    module_page_map: Mapping[str, str] | None = None,
) -> list[tuple[str, str]]:
    """Return sorted module links for process-related internal imports."""
    page_map = module_page_map or {}
    refs = [
        (
            page_map.get(path, _module_name_from_path(path)),
            page_map.get(path, _module_name_from_path(path)),
        )
        for path in flow.get("related_modules", [])
    ]
    return sorted(set(refs), key=lambda item: item[0])


def _flow_interactions(flow: dict) -> list[dict]:
    """Convert depth-tagged flow steps into caller→callee sequence interactions.

    Reconstructs each step's caller from the most recent shallower step so the
    nested call tree renders as an ordered sequence. External and unresolved
    calls are marked ``dashed``.
    """
    interactions: list[dict] = []
    stack: dict[int, str] = {}
    for step in flow.get("steps", []):
        depth = step["depth"]
        symbol = step["symbol"]
        if depth == 0:
            stack = {0: symbol}
            continue
        interactions.append(
            {
                "from": stack.get(depth - 1, "?"),
                "to": symbol,
                "label": symbol,
                "dashed": step["kind"] in ("external", "unresolved"),
            }
        )
        stack[depth] = symbol
        for deeper in [d for d in stack if d > depth]:
            del stack[deeper]
    return interactions


_FLOW_SEQUENCE_INTERACTION_LIMIT = 30


def _bounded_flow_interactions(interactions: list[dict]) -> tuple[list[dict], int]:
    shown = interactions[:_FLOW_SEQUENCE_INTERACTION_LIMIT]
    return shown, max(0, len(interactions) - len(shown))


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|") if value not in (None, "") else "-"


def _effect_label(effect: Mapping) -> str:
    label = (
        effect.get("name")
        or effect.get("value")
        or effect.get("target")
        or effect.get("annotation")
        or effect.get("kind")
        or "?"
    )
    if effect.get("type"):
        label = f"{label}: {effect['type']}"
    return str(label)


def _effects_cell(effects: list[Mapping]) -> str:
    if not effects:
        return "-"
    return ", ".join(f"`{_md_cell(_effect_label(effect))}`" for effect in effects)


def _generate_data_flow_section(
    data_flow: Mapping,
    module_page_map: Mapping[str, str] | None = None,
    diagram_style: Mapping[str, Any] | None = None,
) -> list[str]:
    lines = [
        "## Data flow",
        "",
        "<!-- Auto-generated static analysis. Treat values and boundaries as "
        "best-effort hints, not runtime proof. -->",
        data_flow_diagram(data_flow, module_page_map, style=diagram_style),
        "",
        "### Step data",
        "",
        "| Step | Inputs | Reads | Writes | Returns |",
        "|---|---|---|---|---|",
    ]
    for step in data_flow.get("steps", []):
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{_md_cell(step.get('symbol'))}`",
                    _effects_cell(step.get("inputs", [])),
                    _effects_cell(step.get("reads", [])),
                    _effects_cell(step.get("writes", [])),
                    _effects_cell(step.get("returns", [])),
                ]
            )
            + " |"
        )
    lines.extend(["", "### Call data", ""])
    transfers = data_flow.get("transfers", [])
    if transfers:
        lines.extend(["| From | To | Line | Call |", "|---|---|---:|---|"])
        for transfer in transfers:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(transfer.get("from")),
                        _md_cell(transfer.get("to")),
                        _md_cell(transfer.get("line")),
                        f"`{_md_cell(transfer.get('call'))}`",
                    ]
                )
                + " |"
            )
    else:
        lines.append("*No call data transfers detected.*")
    lines.extend(["", "### Boundary effects", ""])
    boundaries = data_flow.get("boundaries", [])
    if boundaries:
        lines.extend(["| Kind | Target | Step | Line |", "|---|---|---|---:|"])
        for boundary in boundaries:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(boundary.get("kind")),
                        f"`{_md_cell(boundary.get('target'))}`",
                        f"`{_md_cell(boundary.get('step'))}`",
                        _md_cell(boundary.get("line")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("*No boundary effects detected.*")
    lines.extend(["", "### Static analysis gaps", ""])
    gaps = data_flow.get("gaps", [])
    if gaps:
        lines.extend(["| Kind | Step | Target | Line |", "|---|---|---|---:|"])
        for gap in gaps:
            lines.append(
                "| "
                + " | ".join(
                    [
                        _md_cell(gap.get("kind")),
                        f"`{_md_cell(gap.get('step'))}`",
                        f"`{_md_cell(gap.get('target'))}`",
                        _md_cell(gap.get("line")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("*No static analysis gaps detected.*")
    lines.append("")
    return lines


def _generate_flow_md(
    flow: dict,
    module_page_map: Mapping[str, str] | None = None,
    *,
    data_flow: Mapping | None = None,
    diagram_style: Mapping[str, Any] | None = None,
    api_contract_operations: Sequence[Mapping[str, Any]] | None = None,
) -> str:
    """Generate a user-flow page with a Mermaid sequence diagram from *flow*."""
    entry = flow["entry"]
    page_map = module_page_map or {}
    interactions = _flow_interactions(flow)
    modules = _flow_module_refs(flow, page_map)
    related_modules = _flow_related_module_refs(flow, page_map)

    lines = [
        f"# {entry['label']}",
        "",
        f"**Entry point:** `{entry['symbol']}` (`{entry['category']}`)",
    ]
    if entry.get("file"):
        stem = page_map.get(entry["file"], _module_name_from_path(entry["file"]))
        lines.append(f"**Source:** [{stem}](../modules/{stem}.md)")
    if modules:
        joined = ", ".join(
            f"[{label}](../modules/{page}.md)" for label, page in modules
        )
        lines.append(f"**Modules touched:** {joined}")
    if related_modules:
        joined = ", ".join(
            f"[{label}](../modules/{page}.md)" for label, page in related_modules
        )
        lines.append(f"**Related modules:** {joined}")
    lines.append("")

    lines.append("## Call sequence")
    lines.append("")
    lines.append(
        "<!-- Auto-generated from static call edges. Dashed arrows are external "
        "or unresolved calls. Refine order and conditions after review. -->"
    )
    if interactions:
        shown_interactions, omitted_interactions = _bounded_flow_interactions(
            interactions
        )
        lines.append(sequence_diagram(shown_interactions))
        if omitted_interactions:
            lines.append("")
            lines.append(
                f"> Call sequence truncated for readability: first "
                f"{_FLOW_SEQUENCE_INTERACTION_LIMIT} interactions shown; "
                f"{omitted_interactions} omitted."
            )
    else:
        lines.append("*No outbound calls detected — describe the behavior manually.*")
    if flow.get("truncated"):
        lines.append("")
        lines.append("> Trace truncated at the depth limit; deeper calls are omitted.")
    lines.append("")

    if data_flow is not None:
        if diagram_style is None:
            diagram_style = _generated_diagram_style(
                "data_flow",
                flow_id=entry.get("id"),
                category=entry.get("category"),
            )
        lines.extend(_generate_data_flow_section(data_flow, page_map, diagram_style))

    api_contract_section = render_flow_api_contract_section(
        api_contract_operations or []
    )
    if api_contract_section:
        lines.extend(api_contract_section.rstrip().splitlines())
        lines.append("")

    lines.append("## Behavior")
    lines.append("")
    lines.append(
        "_Describe what this flow does, when it is triggered, and its key side "
        "effects or outputs. Replace this placeholder._"
    )
    lines.append("")

    return "\n".join(lines)


def _preserve_level_two_section(existing: str, generated: str, heading: str) -> str:
    """Carry one human-owned level-two section into regenerated Markdown."""
    return _service_preserve_level_two_section_exact(existing, generated, heading)


# ── Architecture pages: dependencies + load order (Epic 2.4) ──────────

# Above this many module nodes, the ``auto`` graph detail collapses the
# flowchart to top-level packages so large repos stay readable (DL-404).
_DEPENDENCY_GRAPH_NODE_LIMIT = 40


def _dependency_module_link(filepath: str, module_page_map: Mapping[str, str]) -> str:
    """Markdown link from an architecture page (wiki root) to a module page."""
    stem = module_page_map.get(filepath, _module_name_from_path(filepath))
    return f"[{stem}](modules/{stem}.md)"


def _cyclic_edges(
    edges: list[tuple[str, str]], cycles: list[list[str]]
) -> set[tuple[str, str]]:
    """Return the edges whose endpoints sit in the same import cycle."""
    group_of: dict[str, int] = {}
    for index, cycle in enumerate(cycles):
        for node in cycle:
            group_of[node] = index
    return {
        (src, dst)
        for src, dst in edges
        if src in group_of and group_of[src] == group_of.get(dst)
    }


def _render_dependency_graph(
    analysis: dict,
    module_page_map: Mapping[str, str],
    detail: str,
    diagram_style: Mapping[str, Any] | None = None,
) -> tuple[str | None, str]:
    """Render the dependency flowchart, choosing module vs package detail.

    Returns ``(diagram_or_None, rendered_detail)``. ``auto`` collapses to a
    package-level graph past :data:`_DEPENDENCY_GRAPH_NODE_LIMIT`; ``package``
    always collapses; ``module`` keeps the full graph with per-module links and
    cyclic edges highlighted. ``None`` when there is nothing to draw.
    """
    graph = analysis["graph"]
    nodes = graph["nodes"]
    if diagram_style is None:
        diagram_style = _generated_diagram_style("dependencies", detail=detail)
    use_package = detail == "package" or (
        detail == "auto" and len(nodes) > _DEPENDENCY_GRAPH_NODE_LIMIT
    )
    if use_package:
        collapsed = package_dependency_graph(graph)
        if not collapsed["nodes"]:
            return None, "package"
        return (
            flowchart(collapsed["nodes"], collapsed["edges"], style=diagram_style),
            "package",
        )
    if not nodes:
        return None, "module"
    links = {
        node: f"modules/{module_page_map.get(node, _module_name_from_path(node))}.md"
        for node in nodes
    }
    highlight = _cyclic_edges(graph["edges"], analysis["cycles"])
    return (
        flowchart(
            nodes,
            graph["edges"],
            links=links,
            highlight_edges=highlight,
            style=diagram_style,
        ),
        "module",
    )


def _format_package_list(packages: list[str]) -> str:
    return ", ".join(f"`{pkg}`" for pkg in packages) if packages else "—"


def _append_external_dependencies(lines: list[str], reconciliation: dict) -> None:
    """Append the per-language external-dependency section (DL-205) to *lines*."""
    lines.append("## External dependencies")
    lines.append("")
    languages = reconciliation.get("languages", {})
    emitted = False
    for language in sorted(languages):
        lang = languages[language]
        if not (lang["used"] or lang["undeclared"] or lang["unused"]):
            continue
        emitted = True
        lines.append(f"### {language}")
        lines.append("")
        lines.append(f"- **Used:** {_format_package_list(sorted(lang['used']))}")
        if lang["undeclared"]:
            lines.append(
                f"- ⚠️ **Undeclared:** {_format_package_list(lang['undeclared'])}"
            )
        if lang["unused"]:
            lines.append(
                f"- **Unused (declared, not imported):** "
                f"{_format_package_list(lang['unused'])}"
            )
        lines.append("")
    if not emitted:
        lines.append("*No external dependencies detected.*")
        lines.append("")


def _generate_dependencies_md(
    analysis: dict,
    module_page_map: Mapping[str, str] | None = None,
    *,
    detail: str = "auto",
    diagram_style: Mapping[str, Any] | None = None,
) -> str:
    """Render ``dependencies.md`` from a :func:`analyze_dependencies` bundle.

    Sections: a linked internal-module Mermaid ``flowchart`` (cyclic edges
    thickened), import **Cycles**, a **Fan-in / Fan-out** table, **External
    dependencies** grouped by language, and a ``## Notes`` semantic placeholder.
    Deterministic; degrades cleanly with no cycles or no external deps.
    """
    page_map = module_page_map or {}
    cycles = analysis["cycles"]
    metrics = analysis["metrics"]

    lines = [
        "# Dependencies",
        "",
        "Internal module dependency graph and external package reconciliation.",
        "",
        "## Module graph",
        "",
    ]
    diagram, rendered_detail = _render_dependency_graph(
        analysis, page_map, detail, diagram_style
    )
    if diagram and rendered_detail == "package":
        lines.append(
            "<!-- Collapsed to top-level packages; the full module list is in the "
            "Fan-in / Fan-out table below. -->"
        )
        lines.append(diagram)
    elif diagram:
        lines.append("<!-- Thick arrows (==>) mark edges inside an import cycle. -->")
        lines.append(diagram)
    else:
        lines.append("*No internal module dependencies detected.*")
    lines.append("")

    lines.append("## Cycles")
    lines.append("")
    if cycles:
        lines.append(
            "> Import cycles are legal but complicate load order — review the "
            "modules below."
        )
        lines.append("")
        for cycle in cycles:
            joined = " ⇄ ".join(_dependency_module_link(fp, page_map) for fp in cycle)
            lines.append(f"- {joined}")
    else:
        lines.append("*No import cycles detected.*")
    lines.append("")

    lines.append("## Fan-in / Fan-out")
    lines.append("")
    ranking = metrics.get("most_depended_on", [])
    if ranking:
        lines.append("| Module | Fan-in | Fan-out |")
        lines.append("|--------|--------|---------|")
        for module in ranking:
            counts = metrics["metrics"][module]
            link = _dependency_module_link(module, page_map)
            lines.append(f"| {link} | {counts['fan_in']} | {counts['fan_out']} |")
    else:
        lines.append("*No internal modules detected.*")
    lines.append("")

    _append_external_dependencies(lines, analysis["reconciliation"])

    lines.append("## Notes")
    lines.append("")
    lines.append(
        "_Document dynamic or conditional imports, intentional cycles, and the "
        "rationale behind notable dependencies. Replace this placeholder._"
    )
    lines.append("")
    return "\n".join(lines)


def _format_side_effect_call(call: Mapping) -> str:
    """Render a ``module_calls`` record as ``target = label`` or ``label``."""
    label = str(call.get("attr") or call.get("name", ""))
    target = call.get("target")
    return f"{target} = {label}" if target else label


def _generate_load_order_md(
    analysis: dict,
    module_page_map: Mapping[str, str] | None = None,
) -> str:
    """Render ``load-order.md`` from a :func:`analyze_dependencies` bundle.

    Sections: the topological **Load order** (numbered, dependency-first),
    **Module-level side effects**, a heuristic **Factory / wiring** table,
    **Indeterminate (cyclic) groups** whose order cannot be resolved, and a
    ``## Notes`` placeholder. Deterministic; degrades cleanly when empty.
    """
    page_map = module_page_map or {}
    load_order = analysis["load_order"]
    side_effects = analysis["side_effects"]
    order = load_order.get("order", [])
    cycle_groups = load_order.get("cycle_groups", [])

    lines = [
        "# Load order",
        "",
        "Topological module load / startup order and import-time side effects.",
        "",
        "## Load order",
        "",
        "<!-- Dependency-first order: each module loads after the internal "
        "modules it imports. -->",
    ]
    if order:
        for index, filepath in enumerate(order, 1):
            lines.append(f"{index}. {_dependency_module_link(filepath, page_map)}")
    else:
        lines.append("*No modules detected.*")
    lines.append("")

    lines.append("## Module-level side effects")
    lines.append("")
    effects = side_effects.get("side_effects", [])
    if effects:
        lines.append("| Module | Import-time calls |")
        lines.append("|--------|-------------------|")
        for entry in effects:
            calls = ", ".join(
                f"`{_format_side_effect_call(call)}`" for call in entry["calls"]
            )
            link = _dependency_module_link(entry["file"], page_map)
            lines.append(f"| {link} | {calls} |")
    else:
        lines.append("*No import-time side effects detected.*")
    lines.append("")

    lines.append("## Factory / wiring")
    lines.append("")
    factories = side_effects.get("factories", [])
    if factories:
        lines.append(
            "<!-- Heuristic, name-based detection of app-factory / wiring "
            "functions. -->"
        )
        lines.append("")
        lines.append("| Function | Kind | Module |")
        lines.append("|----------|------|--------|")
        for factory in factories:
            link = _dependency_module_link(factory["file"], page_map)
            lines.append(f"| `{factory['symbol']}` | {factory['kind']} | {link} |")
    else:
        lines.append("*No factory or wiring functions detected.*")
    lines.append("")

    if cycle_groups:
        lines.append("## Indeterminate (cyclic) groups")
        lines.append("")
        lines.append(
            "> These modules form import cycles, so their relative load order is "
            "indeterminate."
        )
        lines.append("")
        for group in cycle_groups:
            joined = " ⇄ ".join(_dependency_module_link(fp, page_map) for fp in group)
            lines.append(f"- {joined}")
        lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append(
        "_Document required initialization order, lazy imports, and side effects "
        "that must run before others. Replace this placeholder._"
    )
    lines.append("")
    return "\n".join(lines)


_SOURCE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")


def _normalize_source_path(path: str) -> str:
    """Normalize Docker COPY source paths for comparison with inventory keys."""
    return normalize_source_path(path) or ""


def _coerce_module_links(
    module_links: Mapping[str, str] | set[str] | None,
) -> dict[str, str]:
    """Return ``{source_path: module_page_stem}`` for Docker COPY linking.

    ``set[str]`` is accepted for backward compatibility with older tests that
    passed raw module stems.
    """
    if not module_links:
        return {}
    if isinstance(module_links, Mapping):
        return {
            _normalize_source_path(source_path): page_name
            for source_path, page_name in module_links.items()
        }

    coerced: dict[str, str] = {}
    for stem in module_links:
        for ext in _SOURCE_EXTS:
            coerced[f"{stem}{ext}"] = stem
    return coerced


def _copy_source_candidates(source: str, docker_filename: str) -> list[str]:
    """Return likely project-relative source paths for a Docker COPY source."""
    source = _normalize_source_path(source)
    if not source:
        return []

    docker_path = Path(docker_filename.replace("\\", "/"))
    docker_parent = docker_path.parent

    candidates: list[str] = []
    if str(docker_parent) not in ("", "."):
        # Common repo layout: Dockerfiles live in ./docker while the build
        # context is the project/worktree root one level above that directory.
        if docker_parent.name == "docker":
            candidates.append((docker_parent.parent / source).as_posix())
        candidates.append((docker_parent / source).as_posix())
    candidates.append(source)

    seen: set[str] = set()
    result: list[str] = []
    for candidate in candidates:
        normalized = _normalize_source_path(candidate)
        if normalized and normalized not in seen:
            result.append(normalized)
            seen.add(normalized)
    return result


def _module_page_for_copy_source(
    source: str,
    docker_filename: str,
    module_links: Mapping[str, str] | set[str] | None,
) -> str | None:
    """Resolve a Docker COPY source to a module page stem if unambiguous."""
    source = _normalize_source_path(source)
    if not source or "*" in source or source.endswith("/"):
        return None

    links = _coerce_module_links(module_links)
    if not links:
        return None

    for candidate in _copy_source_candidates(source, docker_filename):
        if candidate in links:
            return links[candidate]

    suffix_matches = {
        page_name
        for source_path, page_name in links.items()
        if source_path == source or source_path.endswith(f"/{source}")
    }
    if len(suffix_matches) == 1:
        return next(iter(suffix_matches))
    return None


def _split_copy_sources(source: str) -> list[str]:
    """Split a Docker COPY source field while preserving a safe fallback."""
    source = source.strip()
    if not source:
        return []
    try:
        parts = shlex.split(source)
    except ValueError:
        return [source]
    return parts or [source]


def _format_copy_source_links(
    source: str,
    docker_filename: str,
    module_links: Mapping[str, str] | set[str] | None,
) -> str:
    """Format a Docker COPY source cell with module links where safe."""
    sources = _split_copy_sources(source)
    if not sources:
        return "—"

    formatted: list[str] = []
    for item in sources:
        page_name = _module_page_for_copy_source(item, docker_filename, module_links)
        if page_name:
            formatted.append(f"[`{item}`](../modules/{page_name}.md)")
        else:
            formatted.append(f"`{item}`")
    return ", ".join(formatted)


def _unsupported_source_path_map(
    unsupported_sources: dict[str, dict[str, object]] | None,
) -> dict[str, str]:
    """Return ``{source_path: language}`` for unsupported-source advisories."""
    if not unsupported_sources:
        return {}
    result: dict[str, str] = {}
    for language, data in sorted(unsupported_sources.items()):
        paths = data.get("paths", [])
        if not isinstance(paths, list):
            continue
        for path in paths:
            normalized = _normalize_source_path(str(path))
            if normalized:
                result[normalized] = language
    return result


def _unsupported_copy_source_matches(
    source: str,
    docker_filename: str,
    unsupported_sources: dict[str, dict[str, object]] | None,
) -> list[dict[str, str]]:
    """Resolve Docker COPY sources to known unsupported source paths."""
    unsupported = _unsupported_source_path_map(unsupported_sources)
    if not unsupported:
        return []

    matches: list[dict[str, str]] = []
    for item in _split_copy_sources(source):
        for candidate in _copy_source_candidates(item, docker_filename):
            language = unsupported.get(candidate)
            if language:
                matches.append(
                    {"source": item, "path": candidate, "language": language}
                )
                break
    return matches


def _unsupported_language_label(language: str) -> str:
    return "Shell" if language == "shell" else language.title()


def _generate_docker_md(
    filename: str,
    info: dict,
    module_links: Mapping[str, str] | set[str] | None = None,
    *,
    module_stems: set[str] | None = None,
    unsupported_sources: dict[str, dict[str, object]] | None = None,
) -> str:
    """Generate a wiki page for a Dockerfile or docker-compose file."""
    if module_links is None and module_stems is not None:
        module_links = module_stems
    if info["type"] == "dockerfile":
        return _generate_dockerfile_md(
            filename, info, module_links, unsupported_sources
        )
    return _generate_compose_md(filename, info, module_links)


def _generate_infrastructure_md(
    filename: str,
    info: dict,
    module_links: Mapping[str, str] | set[str] | None = None,
    unsupported_sources: dict[str, dict[str, object]] | None = None,
) -> str:
    """Generate a wiki page for any supported infrastructure inventory entry."""
    if info["type"] in {"dockerfile", "compose"}:
        return _generate_docker_md(
            filename, info, module_links, unsupported_sources=unsupported_sources
        )
    if info["type"] == "github_actions":
        return _generate_github_actions_md(filename, info)
    if info["type"] == "kubernetes":
        return _generate_kubernetes_md(filename, info)
    if info["type"] in RUNTIME_CONFIG_TYPES:
        return _generate_runtime_config_md(filename, info)
    return _generate_unsupported_infrastructure_md(filename, info)


def _append_infrastructure_advisories(lines: list[str], advisories: list[str]) -> None:
    if not advisories:
        return
    lines.append("## Advisories")
    lines.append("")
    for advisory in advisories:
        lines.append(f"- {advisory}")
    lines.append("")


def _generate_github_actions_md(filename: str, info: dict) -> str:
    """Generate markdown for a GitHub Actions workflow file."""
    title = infrastructure_display_label(filename, info)
    lines = [
        f"# {title}",
        "",
        f"**Path:** `{filename}`",
        "**Type:** `github_actions`",
        "",
    ]
    triggers = info.get("triggers") or []
    if triggers:
        lines.append("## Triggers")
        lines.append("")
        for trigger in triggers:
            lines.append(f"- `{trigger}`")
        lines.append("")

    jobs = info.get("jobs") or []
    if jobs:
        lines.append("## Jobs")
        lines.append("")
        lines.append("| Job | Display Name | Runs On | Needs | Steps |")
        lines.append("|---|---|---|---|---:|")
        for job in jobs:
            needs = job.get("needs") or []
            needs_text = ", ".join(f"`{item}`" for item in needs) if needs else "—"
            name = f"`{job['name']}`" if job.get("name") else "—"
            runs_on = f"`{job['runs_on']}`" if job.get("runs_on") else "—"
            step_count = len(job.get("steps") or [])
            lines.append(
                f"| `{job['id']}` | {name} | {runs_on} | {needs_text} | {step_count} |"
            )
        lines.append("")

        for job in jobs:
            lines.append(f"### {job['id']}")
            lines.append("")
            for step in job.get("steps") or []:
                label = (
                    step.get("name") or step.get("uses") or step.get("run") or "step"
                )
                details = []
                if step.get("uses"):
                    details.append(f"uses `{step['uses']}`")
                if step.get("run"):
                    details.append(f"runs `{step['run']}`")
                suffix = f" - {'; '.join(details)}" if details else ""
                lines.append(f"- {label}{suffix}")
            lines.append("")

    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _generate_kubernetes_md(filename: str, info: dict) -> str:
    """Generate markdown for a Kubernetes manifest file."""
    title = infrastructure_display_label(filename, info)
    lines = [
        f"# {title}",
        "",
        f"**Path:** `{filename}`",
        "**Type:** `kubernetes`",
        "",
    ]
    resources = info.get("resources") or []
    if resources:
        lines.append("## Resources")
        lines.append("")
        lines.append("| Kind | Name | Namespace | API Version | Replicas |")
        lines.append("|---|---|---|---|---:|")
        for resource in resources:
            kind = resource.get("kind") or "unknown"
            name = resource.get("name") or "unknown"
            api_version = resource.get("api_version") or "unknown"
            namespace = resource.get("namespace") or "—"
            replicas = resource.get("replicas") or "—"
            lines.append(
                f"| `{kind}` | `{name}` | {namespace} | `{api_version}` | {replicas} |"
            )
        lines.append("")

        for resource in resources:
            heading = (
                f"{resource.get('kind') or 'Resource'} "
                f"{resource.get('name') or 'unknown'}"
            )
            lines.append(f"### {heading}")
            lines.append("")
            containers = resource.get("containers") or []
            if containers:
                lines.append("#### Containers")
                lines.append("")
                lines.append("| Name | Image | Ports | Requests | Limits |")
                lines.append("|---|---|---|---|---|")
                for container in containers:
                    ports = ", ".join(f"`{p}`" for p in container.get("ports") or [])
                    requests = _format_resource_map(container.get("requests") or {})
                    limits = _format_resource_map(container.get("limits") or {})
                    name = container.get("name") or "unknown"
                    image = container.get("image") or "unknown"
                    lines.append(
                        f"| `{name}` | `{image}` | {ports or '—'} | "
                        f"{requests} | {limits} |"
                    )
                lines.append("")
            service_ports = resource.get("service_ports") or []
            if service_ports:
                lines.append("#### Service Ports")
                lines.append("")
                lines.append("| Port | Target Port | Protocol |")
                lines.append("|---:|---|---|")
                for port in service_ports:
                    port_value = port.get("port") or "unknown"
                    target_port = port.get("target_port") or "unknown"
                    protocol = port.get("protocol") or "TCP"
                    lines.append(f"| `{port_value}` | `{target_port}` | `{protocol}` |")
                lines.append("")
            selector = resource.get("selector") or {}
            if selector:
                lines.append(f"**Selector:** {_format_resource_map(selector)}")
                lines.append("")

    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _format_resource_map(values: Mapping[str, str]) -> str:
    if not values:
        return "—"
    return ", ".join(f"`{key}={value}`" for key, value in sorted(values.items()))


def _runtime_config_header(filename: str, info: dict) -> list[str]:
    title = infrastructure_display_label(filename, info)
    return [
        f"# {title}",
        "",
        f"**Path:** `{filename}`",
        f"**Type:** `{info['type']}`",
        "",
    ]


def _append_value_list(lines: list[str], title: str, values: Iterable[str]) -> None:
    values = list(values)
    if not values:
        return
    lines.append(f"## {title}")
    lines.append("")
    for value in values:
        lines.append(f"- `{value}`")
    lines.append("")


def _append_setting_table(lines: list[str], settings: Mapping[str, str]) -> None:
    visible = [(key, value) for key, value in settings.items() if value]
    if not visible:
        return
    lines.append("## Settings")
    lines.append("")
    lines.append("| Setting | Value |")
    lines.append("|---|---|")
    for key, value in visible:
        lines.append(f"| `{key}` | `{value}` |")
    lines.append("")


def _generate_runtime_config_md(filename: str, info: dict) -> str:
    entry_type = info["type"]
    if entry_type == "prometheus":
        return _generate_prometheus_md(filename, info)
    if entry_type == "prometheus_rules":
        return _generate_prometheus_rules_md(filename, info)
    if entry_type == "grafana_provisioning":
        return _generate_grafana_provisioning_md(filename, info)
    if entry_type == "promtail":
        return _generate_promtail_md(filename, info)
    if entry_type == "loki":
        return _generate_loki_md(filename, info)
    if entry_type == "envoy":
        return _generate_envoy_md(filename, info)
    if entry_type == "buf":
        return _generate_buf_md(filename, info)
    if entry_type == "model_service_config":
        return _generate_model_service_config_md(filename, info)
    return _generate_unsupported_infrastructure_md(filename, info)


def _generate_prometheus_md(filename: str, info: dict) -> str:
    lines = _runtime_config_header(filename, info)
    _append_value_list(lines, "Rule Files", info.get("rule_files") or [])
    _append_value_list(lines, "Scrape Jobs", info.get("scrape_jobs") or [])
    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _generate_prometheus_rules_md(filename: str, info: dict) -> str:
    lines = _runtime_config_header(filename, info)
    groups = info.get("groups") or []
    if groups:
        lines.append("## Rule Groups")
        lines.append("")
        lines.append("| Group | Interval | Rules |")
        lines.append("|---|---|---:|")
        for group in groups:
            name = group.get("name") or "unknown"
            interval = group.get("interval") or "—"
            rules = group.get("rules") or 0
            lines.append(f"| `{name}` | `{interval}` | {rules} |")
        lines.append("")
    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _generate_grafana_provisioning_md(filename: str, info: dict) -> str:
    lines = _runtime_config_header(filename, info)
    lines.extend(
        [
            f"**Provisioning Kind:** `{info.get('provisioning_kind') or 'unknown'}`",
            "",
        ]
    )
    _append_value_list(lines, "Entries", info.get("entries") or [])
    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _generate_promtail_md(filename: str, info: dict) -> str:
    lines = _runtime_config_header(filename, info)
    _append_setting_table(lines, {"http_listen_port": info.get("listen_port") or ""})
    _append_value_list(lines, "Clients", info.get("clients") or [])
    _append_value_list(lines, "Scrape Jobs", info.get("scrape_jobs") or [])
    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _generate_loki_md(filename: str, info: dict) -> str:
    lines = _runtime_config_header(filename, info)
    _append_setting_table(
        lines,
        {
            "auth_enabled": info.get("auth_enabled") or "",
            "http_listen_port": info.get("listen_port") or "",
            "retention_period": info.get("retention_period") or "",
        },
    )
    _append_value_list(lines, "Schema Stores", info.get("schema_stores") or [])
    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _generate_envoy_md(filename: str, info: dict) -> str:
    lines = _runtime_config_header(filename, info)
    _append_value_list(lines, "Listeners", info.get("listeners") or [])
    _append_value_list(lines, "Clusters", info.get("clusters") or [])
    _append_value_list(lines, "Admin Ports", info.get("admin_ports") or [])
    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _generate_buf_md(filename: str, info: dict) -> str:
    lines = _runtime_config_header(filename, info)
    _append_setting_table(
        lines,
        {
            "config_kind": info.get("config_kind") or "",
            "version": info.get("version") or "",
        },
    )
    _append_value_list(lines, "Modules", info.get("modules") or [])
    _append_value_list(lines, "Dependencies", info.get("deps") or [])
    _append_value_list(lines, "Plugins", info.get("plugins") or [])
    _append_value_list(lines, "Outputs", info.get("outputs") or [])
    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _generate_model_service_config_md(filename: str, info: dict) -> str:
    lines = _runtime_config_header(filename, info)
    _append_setting_table(lines, info.get("settings") or {})
    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _generate_unsupported_infrastructure_md(filename: str, info: dict) -> str:
    lines = [
        f"# {filename}",
        "",
        f"**Path:** `{filename}`",
        f"**Type:** `{info.get('type') or 'unknown'}`",
        "",
        "## Advisories",
        "",
        "- This infrastructure file type is recognized but does not have a renderer yet.",
        "",
    ]
    _append_infrastructure_advisories(lines, info.get("advisories") or [])
    return "\n".join(lines)


def _dockerfile_base_images(stages: list[dict]) -> list[str]:
    return [s["image"] for s in stages] if stages else ["unknown"]


def _dockerfile_header_lines(filename: str, stages: list[dict]) -> list[str]:
    return [
        f"# {filename}",
        "",
        f"**Path:** `{filename}`",
        f"**Base Image(s):** {', '.join(f'`{img}`' for img in _dockerfile_base_images(stages))}",
        "",
    ]


def _append_dockerfile_build_stages(lines: list[str], stages: list[dict]) -> None:
    if not (len(stages) > 1 or (stages and stages[0].get("alias"))):
        return

    lines.append("## Build Stages")
    lines.append("")
    lines.append("| Stage | Base Image |")
    lines.append("|-------|-----------|")
    for s in stages:
        alias = f"`{s['alias']}`" if s.get("alias") else "*(final)*"
        lines.append(f"| {alias} | `{s['image']}` |")
    lines.append("")


def _append_dockerfile_list_section(
    lines: list[str], title: str, values: list[str]
) -> None:
    if not values:
        return

    lines.append(f"## {title}")
    lines.append("")
    for value in values:
        lines.append(f"- `{value}`")
    lines.append("")


def _append_dockerfile_default_table(
    lines: list[str],
    title: str,
    first_column: str,
    rows: list[dict],
) -> None:
    if not rows:
        return

    lines.append(f"## {title}")
    lines.append("")
    lines.append(f"| {first_column} | Default |")
    lines.append("|----------|---------|")
    for row in rows:
        default = f"`{row['default']}`" if row["default"] else "—"
        lines.append(f"| `{row['name']}` | {default} |")
    lines.append("")


def _append_dockerfile_workdir(lines: list[str], workdir: str) -> None:
    if not workdir:
        return

    lines.append(f"**Working Directory:** `{workdir}`")
    lines.append("")


def _append_dockerfile_entrypoint(lines: list[str], entrypoint: str, cmd: str) -> None:
    if not (entrypoint or cmd):
        return

    lines.append("## Entry Point")
    lines.append("")
    if entrypoint:
        lines.append(f"**ENTRYPOINT:** `{entrypoint}`")
    if cmd:
        lines.append(f"**CMD:** `{cmd}`")
    lines.append("")


def _append_dockerfile_copies(
    lines: list[str],
    copies: list[dict],
    filename: str,
    module_links: Mapping[str, str] | set[str] | None,
) -> None:
    if not copies:
        return

    lines.append("## File Copies")
    lines.append("")
    lines.append("| Instruction | Source | Destination | From Stage |")
    lines.append("|-------------|--------|-------------|------------|")
    for copy_info in copies:
        stage = f"`{copy_info['from_stage']}`" if copy_info.get("from_stage") else "—"
        src_text = _format_copy_source_links(copy_info["src"], filename, module_links)
        lines.append(
            f"| `{copy_info['instruction']}` | {src_text} | `{copy_info['dest']}` | {stage} |"
        )
    lines.append("")


def _append_dockerfile_unsupported_copies(
    lines: list[str],
    copies: list[dict],
    filename: str,
    unsupported_sources: dict[str, dict[str, object]] | None,
) -> None:
    matches: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for copy_info in copies:
        for match in _unsupported_copy_source_matches(
            copy_info.get("src", ""), filename, unsupported_sources
        ):
            key = (match["source"], match["path"], match["language"])
            if key not in seen:
                matches.append(match)
                seen.add(key)
    if not matches:
        return

    lines.append("## Unsupported Copied Sources")
    lines.append("")
    lines.append(
        "Shell extraction is not yet supported; these copied deployment scripts "
        "are reported as unsupported-source coverage notices."
    )
    lines.append("")
    lines.append("| COPY Source | Resolved Source | Language |")
    lines.append("|-------------|-----------------|----------|")
    for match in matches:
        lines.append(
            f"| `{match['source']}` | `{match['path']}` | "
            f"{_unsupported_language_label(match['language'])} |"
        )
    lines.append("")


def _append_dockerfile_labels(lines: list[str], labels: dict[str, str]) -> None:
    if not labels:
        return

    lines.append("## Labels")
    lines.append("")
    lines.append("| Key | Value |")
    lines.append("|-----|-------|")
    for key, value in labels.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.append("")


def _append_dockerfile_healthcheck(lines: list[str], healthcheck: str) -> None:
    if not healthcheck:
        return

    lines.append(f"**Healthcheck:** `{healthcheck}`")
    lines.append("")


def _generate_dockerfile_md(
    filename: str,
    info: dict,
    module_links: Mapping[str, str] | set[str] | None = None,
    unsupported_sources: dict[str, dict[str, object]] | None = None,
) -> str:
    """Generate markdown for a Dockerfile."""
    stages = info.get("stages", [])
    lines = _dockerfile_header_lines(filename, stages)

    _append_dockerfile_build_stages(lines, stages)
    _append_dockerfile_list_section(lines, "Exposed Ports", info.get("ports", []))
    _append_dockerfile_default_table(
        lines, "Build Arguments", "Argument", info.get("build_args", [])
    )
    _append_dockerfile_default_table(
        lines, "Environment Variables", "Variable", info.get("env_vars", [])
    )
    _append_dockerfile_list_section(lines, "Volumes", info.get("volumes", []))
    _append_dockerfile_workdir(lines, info.get("workdir", ""))
    _append_dockerfile_entrypoint(
        lines, info.get("entrypoint", ""), info.get("cmd", "")
    )
    _append_dockerfile_copies(lines, info.get("copies", []), filename, module_links)
    _append_dockerfile_unsupported_copies(
        lines, info.get("copies", []), filename, unsupported_sources
    )
    _append_dockerfile_labels(lines, info.get("labels", {}))
    _append_dockerfile_healthcheck(lines, info.get("healthcheck", ""))
    return "\n".join(lines)


def _generate_compose_md(
    filename: str, info: dict, module_links: Mapping[str, str] | set[str] | None = None
) -> str:
    """Generate markdown for a docker-compose / compose file."""
    services = info.get("services", {})
    networks = info.get("networks", [])
    named_volumes = info.get("volumes", [])

    lines = [
        f"# {filename}",
        "",
        f"**Path:** `{filename}`",
        "",
    ]

    # Services summary table
    if services:
        lines.append("## Services")
        lines.append("")
        lines.append("| Service | Image / Build | Ports | Depends On |")
        lines.append("|---------|---------------|-------|------------|")
        for name, svc in services.items():
            image = svc.get("image", "")
            build = svc.get("build", "")
            if isinstance(build, dict):
                build = build.get("context", ".")
            img_str = f"build: `{build}`" if build else (f"`{image}`" if image else "—")
            ports = svc.get("ports", [])
            ports_str = (
                ", ".join(f"`{p}`" for p in ports)
                if isinstance(ports, list)
                else (f"`{ports}`" if ports else "—")
            )
            depends = svc.get("depends_on", [])
            deps_str = (
                ", ".join(f"`{d}`" for d in depends)
                if isinstance(depends, list)
                else (f"`{depends}`" if depends else "—")
            )
            lines.append(f"| `{name}` | {img_str} | {ports_str} | {deps_str} |")
        lines.append("")

        # Per-service detail
        for name, svc in services.items():
            lines.append(f"### {name}")
            lines.append("")
            image = svc.get("image", "")
            build = svc.get("build", "")
            if build:
                ctx = build if isinstance(build, str) else build.get("context", ".")
                lines.append(f"- **Build context:** `{ctx}`")
            if image:
                lines.append(f"- **Image:** `{image}`")
            ports = svc.get("ports", [])
            if ports:
                ports_list = ports if isinstance(ports, list) else [ports]
                lines.append(f"- **Ports:** {', '.join(f'`{p}`' for p in ports_list)}")
            vols = svc.get("volumes", [])
            if vols:
                vols_list = vols if isinstance(vols, list) else [vols]
                lines.append(f"- **Volumes:** {', '.join(f'`{v}`' for v in vols_list)}")
            env = svc.get("environment", [])
            if env:
                env_list = env if isinstance(env, list) else [env]
                lines.append(
                    f"- **Environment:** {', '.join(f'`{e}`' for e in env_list)}"
                )
            depends = svc.get("depends_on", [])
            if depends:
                deps_list = depends if isinstance(depends, list) else [depends]
                lines.append(
                    f"- **Depends on:** {', '.join(f'`{d}`' for d in deps_list)}"
                )
            command = svc.get("command", "")
            if command:
                lines.append(f"- **Command:** `{command}`")
            lines.append("")

    # Networks
    if networks:
        lines.append("## Networks")
        lines.append("")
        for n in networks:
            lines.append(f"- `{n}`")
        lines.append("")

    # Named volumes
    if named_volumes:
        lines.append("## Named Volumes")
        lines.append("")
        for v in named_volumes:
            lines.append(f"- `{v}`")
        lines.append("")

    return "\n".join(lines)


@dataclass(frozen=True)
class _BootstrapRunOptions:
    src_dir: str
    wiki_dir: Path
    src_dir_for_scan: str
    depth: str
    deep: bool
    skip_workflows: bool
    skip_flows: bool
    skip_data_flow: bool
    skip_dependencies: bool
    api_contracts: bool
    openapi_file: str | None
    dependency_graph_detail: str
    overwrite: bool
    json_mode: bool
    source_adapter: bool
    helper_cache_dir: str | None
    include_tests: Iterable[str] | None
    trust_source_plugins: bool
    progress_stream: TextIO


@dataclass
class _BootstrapRunState:
    options: _BootstrapRunOptions
    source_snapshot: Any = None
    created_files: list[str] = field(default_factory=list)
    updated_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    unsupported_sources: dict[str, dict[str, object]] = field(default_factory=dict)
    written_structural_page_paths: set[str] = field(default_factory=set)
    summary: dict[str, Any] | None = None


@dataclass(frozen=True)
class _BootstrapPageMaps:
    module_page_map: dict[str, str]
    entity_page_name_cache: dict[tuple[str, str], str]
    entity_occurrence_page_name_cache: dict[EntityOccurrenceKey, str]


@dataclass(frozen=True)
class _EntityModuleResult:
    all_entity_names: list[str]
    module_entries: list[dict]
    entities_created: int
    modules_created: int


@dataclass(frozen=True)
class _WorkflowResult:
    entries: list[dict]
    created: int


@dataclass(frozen=True)
class _FlowResult:
    entries: list[dict]
    created: int
    data_flow_summary: dict
    entrypoint_observations: dict = field(default_factory=dict)
    flows: list[dict] = field(default_factory=list)
    data_flows: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class _InfrastructureResult:
    entries: list[dict]
    created: int
    docker_inventory: dict
    yaml_inventory: dict
    infrastructure_inventory: dict


@dataclass(frozen=True)
class _DependencyResult:
    architecture_entries: list[dict]
    created: int
    summary: dict
    evidence: dict


@dataclass(frozen=True)
class _ApiContractResult:
    contracts: dict | None
    present: bool
    created: int


@dataclass(frozen=True)
class _BootstrapGenerationResult:
    entity: _EntityModuleResult
    workflow: _WorkflowResult
    flow: _FlowResult
    infrastructure: _InfrastructureResult
    dependency: _DependencyResult
    api_contract: _ApiContractResult
    cross_reference_count: int
    call_observations: dict = field(default_factory=dict)
    dependency_observations: dict = field(default_factory=dict)
    external_dependencies: list[dict] = field(default_factory=list)
    graph_analyzer_limitations: dict[str, tuple[str, ...]] = field(
        default_factory=dict
    )


def _data_flow_summary(
    *, generated: bool, analyzed: int = 0, boundary_effects: int = 0, gaps: int = 0
) -> dict:
    return {
        "generated": generated,
        "analyzed": analyzed,
        "boundary_effects": boundary_effects,
        "gaps": gaps,
    }


def _with_unsupported_sources(
    payload: dict, unsupported_sources: dict[str, dict[str, object]]
) -> dict:
    if unsupported_sources:
        payload["unsupported_sources"] = unsupported_sources
    return payload


def _bootstrap_run_options_from_args(args) -> _BootstrapRunOptions:
    src_dir = args.src_dir
    wiki_dir = Path(args.wiki_dir)
    validate_path(str(wiki_dir), "--wiki-dir")
    src_root = validate_source_root(
        src_dir,
        "--src-dir",
        allow_external=getattr(args, "allow_external_src", False),
    )
    openapi_file = getattr(args, "openapi_file", None)
    api_contracts = bool(getattr(args, "api_contracts", False) or openapi_file)
    depth = "full" if api_contracts else getattr(args, "depth", "full")
    json_mode = getattr(args, "format", "text") == "json"
    return _BootstrapRunOptions(
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        src_dir_for_scan=str(src_root),
        depth=depth,
        deep=depth == "full",
        skip_workflows=getattr(args, "skip_workflows", False),
        skip_flows=getattr(args, "skip_flows", False),
        skip_data_flow=getattr(args, "skip_data_flow", False),
        skip_dependencies=getattr(args, "skip_dependencies", False),
        api_contracts=api_contracts,
        openapi_file=openapi_file,
        dependency_graph_detail=getattr(args, "dependency_graph_detail", "auto"),
        overwrite=args.overwrite,
        json_mode=json_mode,
        source_adapter=getattr(args, "source_adapter", False),
        helper_cache_dir=getattr(args, "helper_cache_dir", None),
        include_tests=getattr(args, "include_tests", None),
        trust_source_plugins=True,
        progress_stream=sys.stderr if json_mode else sys.stdout,
    )


def _bootstrap_run_options_from_request(
    request: BootstrapRequest,
    *,
    progress_stream: TextIO,
) -> _BootstrapRunOptions:
    source_root = Path(request.source_root).expanduser().resolve()
    if not source_root.is_dir():
        raise BootstrapContractError(
            f"Bootstrap source root does not exist: {source_root}"
        )
    wiki_root = Path(request.wiki_root).expanduser().resolve()
    if (
        wiki_root == source_root
        or source_root in wiki_root.parents
        or wiki_root in source_root.parents
    ):
        raise BootstrapContractError(
            "Bootstrap wiki output must not overlap the read-only source root."
        )
    if request.depth not in {"shallow", "full"}:
        raise BootstrapContractError("Bootstrap depth must be shallow or full.")
    api_contracts = bool(request.api_contracts or request.openapi_file)
    depth = "full" if api_contracts else request.depth
    return _BootstrapRunOptions(
        src_dir=str(source_root),
        wiki_dir=wiki_root,
        src_dir_for_scan=str(source_root),
        depth=depth,
        deep=depth == "full",
        skip_workflows=request.skip_workflows,
        skip_flows=request.skip_flows,
        skip_data_flow=request.skip_data_flow,
        skip_dependencies=request.skip_dependencies,
        api_contracts=api_contracts,
        openapi_file=request.openapi_file,
        dependency_graph_detail=request.dependency_graph_detail,
        overwrite=request.overwrite,
        json_mode=False,
        source_adapter=request.source_adapter,
        helper_cache_dir=request.helper_cache_dir,
        include_tests=request.include_tests,
        trust_source_plugins=request.trust_source_plugins,
        progress_stream=progress_stream,
    )


def _path_text(path: Path) -> str:
    return str(path).replace("\\", "/")


def _emit_bootstrap(
    state: _BootstrapRunState, message: str = "", *, flush: bool = False
) -> None:
    print(message, file=state.options.progress_stream, flush=flush)


def _emit_bootstrap_warnings(state: _BootstrapRunState, warnings: list[str]) -> None:
    state.warnings.extend(warnings)
    for warning in warnings:
        _emit_bootstrap(state, f"Warning: {warning}", flush=True)


def _record_bootstrap_write(
    state: _BootstrapRunState, path: Path, existed: bool
) -> None:
    target = state.updated_files if existed else state.created_files
    target.append(_path_text(path))


def _bootstrap_plugin_roots(
    state: _BootstrapRunState,
) -> tuple[str | Path, str | Path | None]:
    if state.options.trust_source_plugins:
        return state.options.src_dir_for_scan, Path.cwd()
    # A new workspace wiki contains no installed plugins.  Pointing plugin
    # discovery there keeps the deterministic service path inert without
    # changing the managed bootstrap default.
    return state.options.wiki_dir, None


def _write_bootstrap_file(state: _BootstrapRunState, path: Path, text: str) -> None:
    existed = path.exists()
    write_md(path, text)
    _record_bootstrap_write(state, path, existed)


def _start_bootstrap(state: _BootstrapRunState) -> None:
    options = state.options
    _emit_bootstrap(
        state,
        f"Bootstrapping wiki from source: {options.src_dir_for_scan} (depth={options.depth})",
        flush=True,
    )
    _emit_bootstrap(state, f"Wiki output directory: {options.wiki_dir}", flush=True)
    for subdir in [
        "entities",
        "modules",
        "workflows",
        "guides",
        "infrastructure",
        "flows",
    ]:
        (options.wiki_dir / subdir).mkdir(parents=True, exist_ok=True)


def _extract_bootstrap_inventory(state: _BootstrapRunState):
    options = state.options
    _emit_bootstrap(state, "Extracting source inventory...", flush=True)
    state.source_snapshot = build_source_snapshot(
        options.src_dir_for_scan,
        include_tests=options.include_tests,
    )
    inventory_result = get_inventory_result(
        options.src_dir_for_scan,
        deep=options.deep,
        source_snapshot=state.source_snapshot,
        helper_cache_dir=options.helper_cache_dir,
        include_tests=options.include_tests,
        include_plugins=options.trust_source_plugins,
        capture_data_effect_observations=options.deep,
        capture_import_observations=options.deep,
    )
    if inventory_result.failed:
        print_inventory_failures(inventory_result, file=options.progress_stream)
        details = "; ".join(
            f"{status.language}: {status.message or 'extraction failed'}"
            for status in inventory_result.failed
        )
        raise BootstrapExtractionError(details or "Source extraction failed.")
    state.source_snapshot = inventory_result.source_snapshot or state.source_snapshot
    state.unsupported_sources = unsupported_source_summary(
        state.source_snapshot, supported_languages=inventory_result.statuses
    )
    unsupported_message = format_unsupported_source_summary(state.unsupported_sources)
    if unsupported_message:
        _emit_bootstrap(state, unsupported_message, flush=True)
    _emit_bootstrap(
        state,
        f"Extracted source inventory: {len(inventory_result.inventory)} file(s).",
        flush=True,
    )
    return inventory_result


def _finish_if_empty_bootstrap_inventory(
    state: _BootstrapRunState, inventory: dict
) -> bool:
    if inventory:
        return False

    options = state.options
    _emit_bootstrap(
        state,
        "No supported source files with documentable inventory found. Nothing to bootstrap.",
    )
    state.summary = _with_unsupported_sources(
        {
            "schema_version": BOOTSTRAP_SUMMARY_SCHEMA_VERSION,
            "src_dir": options.src_dir_for_scan,
            "generated_wiki_path": _path_text(options.wiki_dir),
            "depth": options.depth,
            "source_files": len(state.source_snapshot.all_source_paths),
            "classes": 0,
            "functions": 0,
            "docker_files": 0,
            "workflows": 0,
            "flows": 0,
            "dependencies": {"generated": False},
            "cross_references": 0,
            "created_files": state.created_files,
            "updated_files": state.updated_files,
            "skipped_files": state.skipped_files,
            "manifest_path": None,
            "knowledge_path": None,
            "knowledge_status": None,
            "knowledge_schema_version": KNOWLEDGE_SCHEMA_VERSION,
        },
        state.unsupported_sources,
    )
    if options.json_mode:
        print(json.dumps(state.summary, indent=2))
    return True


def _prepare_bootstrap_page_maps(inventory: dict) -> _BootstrapPageMaps:
    module_page_map = build_module_page_map(inventory)
    entity_occurrence_page_map = build_entity_occurrence_page_map(
        inventory, module_page_map
    )
    return _BootstrapPageMaps(
        module_page_map=module_page_map,
        entity_page_name_cache=_legacy_entity_page_map(entity_occurrence_page_map),
        entity_occurrence_page_name_cache=entity_occurrence_page_map,
    )


def _build_bootstrap_relationships(
    state: _BootstrapRunState,
    inventory: dict,
    module_page_map: dict[str, str],
) -> tuple[dict, int]:
    if state.options.deep:
        _emit_bootstrap(state, "Building cross-reference relationships...", flush=True)
    relationships = (
        _build_relationships(inventory, module_page_map) if state.options.deep else {}
    )
    cross_reference_count = sum(len(v) for v in relationships.values())
    if state.options.deep:
        _emit_bootstrap(
            state,
            f"Built cross-reference relationships: {cross_reference_count}.",
            flush=True,
        )
    return relationships, cross_reference_count


def _build_entity_relationship_summary_map(
    inventory: dict, call_edges: Sequence[Mapping]
) -> dict[tuple[str, str], Mapping]:
    summaries = build_entity_relationship_summaries(inventory, call_edges=call_edges)
    return {
        (str(summary["name"]), str(summary["file"])): summary
        for summary in summaries.get("classes", [])
        if summary.get("name") and summary.get("file")
    }


def _build_bootstrap_dependency_analysis(
    state: _BootstrapRunState, inventory: dict
) -> dict | None:
    if not state.options.deep or state.options.skip_dependencies:
        return None
    return analyze_dependencies(
        inventory,
        state.options.src_dir_for_scan,
        source_snapshot=state.source_snapshot,
    )


def _write_bootstrap_entity_pages(
    state: _BootstrapRunState,
    filepath: str,
    file_data: dict,
    relationships: dict,
    mod_page_name: str,
    module_page_map: Mapping[str, str],
    entity_relationship_summaries: Mapping[tuple[str, str], Mapping] | None,
    entity_occurrence_page_map: Mapping[EntityOccurrenceKey, str],
    seen_entity_pages: set[str],
    all_entity_names: list[str],
) -> int:
    entities_created = 0
    seen_names: defaultdict[str, int] = defaultdict(int)
    for cls in file_data.get("classes", []):
        seen_names[cls["name"]] += 1
        entity_page_name = entity_occurrence_page_map[
            (cls["name"], filepath, seen_names[cls["name"]])
        ]
        entity_path = state.options.wiki_dir / "entities" / f"{entity_page_name}.md"
        relationship_summary = (entity_relationship_summaries or {}).get(
            (cls["name"], filepath)
        )
        diagram_style = None
        if relationship_summary is not None:
            plugin_root, plugin_fallback = _bootstrap_plugin_roots(state)
            diagram_style = _generated_diagram_style(
                "relationships",
                root=plugin_root,
                fallback_root=plugin_fallback,
                entity=relationship_summary.get("name"),
                file=relationship_summary.get("file"),
            )
        if entity_path.exists() and not state.options.overwrite:
            state.skipped_files.append(_path_text(entity_path))
            _emit_bootstrap(state, f"  SKIP entity (exists): {entity_page_name}")
        else:
            _write_bootstrap_file(
                state,
                entity_path,
                _generate_entity_md(
                    cls,
                    filepath,
                    relationships,
                    mod_page_name,
                    relationship_summary=relationship_summary,
                    module_page_map=module_page_map,
                    diagram_style=diagram_style,
                ),
            )
            state.written_structural_page_paths.add(f"entities/{entity_page_name}.md")
            entities_created += 1
            _emit_bootstrap(state, f"  CREATE entity: {entity_page_name}")
        if entity_page_name not in seen_entity_pages:
            all_entity_names.append(entity_page_name)
            seen_entity_pages.add(entity_page_name)
    return entities_created


def _write_bootstrap_module_page(
    state: _BootstrapRunState,
    filepath: str,
    file_data: dict,
    mod_page_name: str,
    file_entity_page_map: dict[str, str],
    entity_occurrence_page_map: Mapping[EntityOccurrenceKey, str],
    module_dependency_map: Mapping | None,
    module_page_map: Mapping[str, str],
) -> bool:
    module_path = state.options.wiki_dir / "modules" / f"{mod_page_name}.md"
    if module_path.exists() and not state.options.overwrite:
        state.skipped_files.append(_path_text(module_path))
        _emit_bootstrap(state, f"  SKIP module (exists): {mod_page_name}")
        return False

    plugin_root, plugin_fallback = _bootstrap_plugin_roots(state)
    _write_bootstrap_file(
        state,
        module_path,
        _generate_module_md(
            filepath,
            file_data,
            file_entity_page_map,
            module_dependency_map=module_dependency_map,
            module_page_map=module_page_map,
            entity_occurrence_page_map=entity_occurrence_page_map,
            diagram_style=_generated_diagram_style(
                "module_dependency",
                root=plugin_root,
                fallback_root=plugin_fallback,
                file=filepath,
            )
            if module_dependency_map is not None
            else None,
        ),
    )
    state.written_structural_page_paths.add(f"modules/{mod_page_name}.md")
    _emit_bootstrap(state, f"  CREATE module: {mod_page_name}")
    return True


def _file_entity_page_map_from_occurrences(
    filepath: str,
    file_data: Mapping,
    entity_occurrence_page_map: Mapping[EntityOccurrenceKey, str],
) -> dict[str, str]:
    page_map: dict[str, str] = {}
    seen_names: defaultdict[str, int] = defaultdict(int)
    for cls in file_data.get("classes", []):
        name = cls["name"]
        seen_names[name] += 1
        page_map.setdefault(
            name,
            entity_occurrence_page_map[(name, filepath, seen_names[name])],
        )
    return page_map


def _write_entity_and_module_pages(
    state: _BootstrapRunState,
    inventory: dict,
    page_maps: _BootstrapPageMaps,
    relationships: dict,
    entity_relationship_summaries: Mapping[tuple[str, str], Mapping] | None,
    module_dependency_maps: Mapping[str, Mapping] | None,
) -> _EntityModuleResult:
    all_entity_names: list[str] = []
    module_entries: list[dict] = []
    seen_entity_pages: set[str] = set()
    entities_created = 0
    modules_created = 0

    _emit_bootstrap(state, "Generating entity and module pages...", flush=True)
    for filepath, file_data in inventory.items():
        mod_page_name = page_maps.module_page_map[filepath]
        file_entity_page_map = _file_entity_page_map_from_occurrences(
            filepath, file_data, page_maps.entity_occurrence_page_name_cache
        )
        entities_created += _write_bootstrap_entity_pages(
            state,
            filepath,
            file_data,
            relationships,
            mod_page_name,
            page_maps.module_page_map,
            entity_relationship_summaries,
            page_maps.entity_occurrence_page_name_cache,
            seen_entity_pages,
            all_entity_names,
        )
        if _write_bootstrap_module_page(
            state,
            filepath,
            file_data,
            mod_page_name,
            file_entity_page_map,
            page_maps.entity_occurrence_page_name_cache,
            (module_dependency_maps or {}).get(filepath)
            if module_dependency_maps is not None
            else None,
            page_maps.module_page_map,
        ):
            modules_created += 1
        module_entries.append(
            {
                "name": mod_page_name,
                "path": filepath,
                "docstring": file_data.get("module_docstring", ""),
            }
        )

    _emit_bootstrap(
        state,
        f"Generated entity/module pages: {entities_created} entities, {modules_created} modules.",
        flush=True,
    )
    return _EntityModuleResult(
        all_entity_names=all_entity_names,
        module_entries=module_entries,
        entities_created=entities_created,
        modules_created=modules_created,
    )


def _write_bootstrap_workflow_pages(
    state: _BootstrapRunState,
    inventory: dict,
    module_page_map: dict[str, str],
) -> _WorkflowResult:
    workflow_entries: list[dict] = []
    workflows_created = 0
    if not state.options.deep or state.options.skip_workflows:
        return _WorkflowResult(workflow_entries, workflows_created)

    call_graph = get_call_graph(inventory)
    for wf_name, wf_data in call_graph.items():
        wf_path = state.options.wiki_dir / "workflows" / f"{wf_name}.md"
        if wf_path.exists() and not state.options.overwrite:
            state.skipped_files.append(_path_text(wf_path))
            _emit_bootstrap(state, f"  SKIP workflow (exists): {wf_name}")
        else:
            _write_bootstrap_file(
                state,
                wf_path,
                _generate_workflow_md(wf_name, wf_data, module_page_map),
            )
            workflows_created += 1
            _emit_bootstrap(state, f"  CREATE workflow: {wf_name}")
        workflow_entries.append({"name": wf_name, "entry": wf_data["entry"]})
    return _WorkflowResult(workflow_entries, workflows_created)


def _build_bootstrap_api_contracts(
    state: _BootstrapRunState, inventory: dict
) -> dict | None:
    if not state.options.api_contracts:
        return None
    _emit_bootstrap(state, "Assembling API contracts...", flush=True)
    contracts = build_api_contracts(
        inventory,
        openapi_file=state.options.openapi_file,
        source_root=state.options.src_dir_for_scan,
    )
    _emit_bootstrap(
        state,
        f"Assembled API contracts: {len(contracts.get('operations', []))} operation(s).",
        flush=True,
    )
    return contracts


def _write_bootstrap_api_contract_page(
    state: _BootstrapRunState,
    contracts: dict | None,
    page_maps: _BootstrapPageMaps,
) -> _ApiContractResult:
    page_path = state.options.wiki_dir / canonical_path(PageKind.API_CONTRACTS)
    if contracts is None:
        return _ApiContractResult(None, page_path.is_file(), 0)

    generated = render_api_contracts_markdown(
        contracts,
        module_page_map=page_maps.module_page_map,
        entity_page_map=page_maps.entity_page_name_cache,
    )
    if page_path.exists() and not state.options.overwrite:
        state.skipped_files.append(_path_text(page_path))
        _emit_bootstrap(state, "  SKIP API contracts (exists): api-contracts.md")
        return _ApiContractResult(contracts, True, 0)
    if page_path.exists():
        generated = _preserve_level_two_section(read_md(page_path), generated, "Notes")
    _write_bootstrap_file(state, page_path, generated)
    _emit_bootstrap(state, "  CREATE API contracts: api-contracts.md")
    return _ApiContractResult(contracts, True, 1)


def _api_operations_for_entry_point(
    contracts: Mapping[str, Any] | None, entry_point: Mapping[str, Any]
) -> list[Mapping[str, Any]]:
    if not contracts:
        return []
    filepath = str(entry_point.get("file") or "")
    symbol = str(entry_point.get("symbol") or "").rsplit(".", 1)[-1]
    matches = []
    for operation in contracts.get("operations", []):
        handler = operation.get("handler")
        if not isinstance(handler, Mapping):
            continue
        if str(handler.get("file") or "") != filepath:
            continue
        if str(handler.get("symbol") or "") != symbol:
            continue
        matches.append(operation)
    return matches


def _write_bootstrap_flow_pages(
    state: _BootstrapRunState,
    inventory: dict,
    module_page_map: dict[str, str],
    call_edges: Sequence[Mapping] | None = None,
    api_contracts: Mapping[str, Any] | None = None,
    data_effect_observations: Mapping | None = None,
) -> _FlowResult:
    flow_entries: list[dict] = []
    flows: list[dict] = []
    data_flows: list[dict] = []
    flows_created = 0
    data_flow_summary = _data_flow_summary(generated=False)
    if not state.options.deep or state.options.skip_flows:
        return _FlowResult(flow_entries, flows_created, data_flow_summary)

    _emit_bootstrap(state, "Generating user-flow pages...", flush=True)
    console_scripts = read_console_scripts(state.options.src_dir_for_scan)
    entrypoint_observations = get_detailed_entry_points(
        inventory,
        console_scripts=console_scripts,
        root=state.options.src_dir_for_scan,
        fallback_root=Path.cwd(),
        include_plugins=state.options.trust_source_plugins,
        include_warnings=True,
    )
    _emit_bootstrap_warnings(
        state,
        list(entrypoint_observations.pop("warnings", [])),
    )
    entry_points = attach_routes_to_entry_points(
        entry_points_from_detailed_observations(
            entrypoint_observations,
            include_provenance=True,
        ),
        api_contracts or {},
    )
    for entry_point in entry_points:
        for operation in _api_operations_for_entry_point(api_contracts, entry_point):
            if isinstance(operation, dict):
                operation["flow_id"] = entry_point["id"]
    edges: list[dict]
    if not entry_points:
        edges = []
    elif call_edges is not None:
        edges = [dict(edge) for edge in call_edges]
    else:
        edges = resolve_call_edges(inventory)
    data_flow_enabled = not state.options.skip_data_flow
    data_flow_context = (
        build_data_flow_context(
            inventory,
            edges,
            data_effect_observations=data_effect_observations,
        )
        if data_flow_enabled and entry_points
        else None
    )
    if not data_flow_enabled:
        _emit_bootstrap(state, "  SKIP data flow (--skip-data-flow)")
    analyzed = 0
    boundary_effects = 0
    gaps = 0
    for entry_point in entry_points:
        flow = build_flow(entry_point, edges)
        detailed_flow = build_flow_detailed(entry_point, edges)
        flows.append(detailed_flow)
        data_flow = None
        if data_flow_enabled:
            # Keep the historical projection for Markdown rendering. The
            # detailed observation deliberately represents unknown locations
            # as ``None`` and must not leak that additive contract into the
            # byte-compatible legacy page surface.
            data_flow = analyze_data_flow(
                inventory, flow, edges, context=data_flow_context
            )
            data_flows.append(
                analyze_data_flow_detailed(
                    inventory,
                    detailed_flow,
                    edges,
                    context=data_flow_context,
                )
            )
            analyzed += 1
            boundary_effects += len(data_flow.get("boundaries", []))
            gaps += len(data_flow.get("gaps", []))
        flow_path = state.options.wiki_dir / "flows" / f"{entry_point['id']}.md"
        if flow_path.exists() and not state.options.overwrite:
            state.skipped_files.append(_path_text(flow_path))
            _emit_bootstrap(state, f"  SKIP flow (exists): {entry_point['id']}")
        else:
            plugin_root, plugin_fallback = _bootstrap_plugin_roots(state)
            flow_markdown = _generate_flow_md(
                flow,
                module_page_map,
                data_flow=data_flow,
                diagram_style=_generated_diagram_style(
                    "data_flow",
                    root=plugin_root,
                    fallback_root=plugin_fallback,
                    flow_id=entry_point.get("id"),
                    category=entry_point.get("category"),
                )
                if data_flow is not None
                else None,
                api_contract_operations=_api_operations_for_entry_point(
                    api_contracts, entry_point
                ),
            )
            if flow_path.exists():
                flow_markdown = _preserve_level_two_section(
                    read_md(flow_path), flow_markdown, "Behavior"
                )
            _write_bootstrap_file(
                state,
                flow_path,
                flow_markdown,
            )
            flows_created += 1
            _emit_bootstrap(state, f"  CREATE flow: {entry_point['id']}")
        flow_entry = {
            "id": entry_point["id"],
            "category": entry_point["category"],
            "entry": entry_point["symbol"],
            "file": entry_point.get("file"),
            "label": entry_point.get("label"),
            "detector": entry_point.get("detector", "unknown"),
            "language": (
                inventory.get(entry_point.get("file"), {}).get("language") or "unknown"
            ),
            "evidence": {
                "flow": {
                    "step_count": len(flow.get("steps", [])),
                    "truncated": bool(flow.get("truncated")),
                    "modules_touched": list(flow.get("modules_touched", [])),
                },
                "data_flow": (
                    {
                        "generated": True,
                        "step_count": len(data_flow.get("steps", [])),
                        "transfer_count": len(data_flow.get("transfers", [])),
                        "truncated": bool(data_flow.get("truncated")),
                        "boundary_effects": list(data_flow.get("boundaries", [])),
                        "gaps": list(data_flow.get("gaps", [])),
                    }
                    if data_flow is not None
                    else None
                ),
            },
        }
        if entry_point.get("routes"):
            flow_entry["routes"] = entry_point["routes"]
        flow_entries.append(flow_entry)
    _emit_bootstrap(state, f"Generated user-flow pages: {flows_created}.", flush=True)
    data_flow_summary = _data_flow_summary(
        generated=data_flow_enabled,
        analyzed=analyzed,
        boundary_effects=boundary_effects,
        gaps=gaps,
    )
    return _FlowResult(
        flow_entries,
        flows_created,
        data_flow_summary,
        entrypoint_observations,
        flows,
        data_flows,
    )


def _write_bootstrap_infrastructure_pages(
    state: _BootstrapRunState,
    module_page_map: dict[str, str],
) -> _InfrastructureResult:
    infra_entries: list[dict] = []
    infra_created = 0
    _emit_bootstrap(state, "Generating infrastructure pages...", flush=True)
    docker_inventory = get_docker_inventory(
        state.options.src_dir_for_scan,
        source_snapshot=state.source_snapshot,
    )
    yaml_inventory = get_yaml_infrastructure_inventory(
        state.options.src_dir_for_scan,
        source_snapshot=state.source_snapshot,
    )
    infrastructure_inventory = dict(docker_inventory)
    for yaml_file, yaml_info in yaml_inventory.items():
        if yaml_file not in infrastructure_inventory:
            infrastructure_inventory[yaml_file] = yaml_info

    advisory_warnings: list[str] = []
    for source_file, info in sorted(infrastructure_inventory.items()):
        page_name = infrastructure_page_name(source_file)
        infra_path = state.options.wiki_dir / "infrastructure" / f"{page_name}.md"
        if infra_path.exists() and not state.options.overwrite:
            state.skipped_files.append(_path_text(infra_path))
            _emit_bootstrap(state, f"  SKIP infrastructure (exists): {page_name}")
        else:
            _write_bootstrap_file(
                state,
                infra_path,
                _generate_infrastructure_md(
                    source_file,
                    info,
                    module_page_map,
                    state.unsupported_sources,
                ),
            )
            infra_created += 1
            _emit_bootstrap(state, f"  CREATE infrastructure: {page_name}")
        infra_entries.append(
            {
                "name": page_name,
                "type": info["type"],
                "label": infrastructure_display_label(source_file, info),
            }
        )
        for advisory in info.get("advisories") or []:
            advisory_warnings.append(f"{source_file}: {advisory}")
    if advisory_warnings:
        _emit_bootstrap_warnings(state, advisory_warnings)
    _emit_bootstrap(
        state, f"Generated infrastructure pages: {infra_created}.", flush=True
    )
    return _InfrastructureResult(
        infra_entries,
        infra_created,
        docker_inventory,
        yaml_inventory,
        infrastructure_inventory,
    )


def _dependency_counts(analysis: dict) -> dict:
    """Scalar counts about *analysis* for the bootstrap JSON summary."""
    graph = analysis["graph"]
    recon_summary = analysis["reconciliation"]["summary"]
    return {
        "modules": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "cycles": len(analysis["cycles"]),
        "external": recon_summary["external_count"],
        "undeclared": recon_summary["undeclared_count"],
        "unused": recon_summary["unused_count"],
    }


def _infrastructure_type_count(
    infrastructure_result: _InfrastructureResult, entry_type: str
) -> int:
    return sum(
        1
        for info in infrastructure_result.infrastructure_inventory.values()
        if info.get("type") == entry_type
    )


def _runtime_config_type_counts(
    infrastructure_result: _InfrastructureResult,
) -> dict[str, int]:
    counts = {
        entry_type: _infrastructure_type_count(infrastructure_result, entry_type)
        for entry_type in sorted(RUNTIME_CONFIG_TYPES)
    }
    return {entry_type: count for entry_type, count in counts.items() if count}


def _runtime_config_count(infrastructure_result: _InfrastructureResult) -> int:
    return sum(_runtime_config_type_counts(infrastructure_result).values())


def _write_bootstrap_dependency_pages(
    state: _BootstrapRunState,
    inventory: dict,
    module_page_map: dict[str, str],
    *,
    analysis: dict | None = None,
) -> _DependencyResult:
    if not state.options.deep or state.options.skip_dependencies:
        return _DependencyResult([], 0, {"generated": False}, {})

    _emit_bootstrap(state, "Generating architecture pages...", flush=True)
    analysis = analysis or analyze_dependencies(
        inventory,
        state.options.src_dir_for_scan,
        source_snapshot=state.source_snapshot,
    )
    if not analysis["graph"]["nodes"]:
        _emit_bootstrap(
            state,
            "Generated architecture pages: 0 (no dependency graph nodes).",
            flush=True,
        )
        return _DependencyResult(
            [],
            0,
            {"generated": False, "pages_created": 0, **_dependency_counts(analysis)},
            analysis.get("metrics", {}),
        )
    plugin_root, plugin_fallback = _bootstrap_plugin_roots(state)
    pages = (
        (
            "dependencies",
            "Dependencies",
            _generate_dependencies_md(
                analysis,
                module_page_map,
                detail=state.options.dependency_graph_detail,
                diagram_style=_generated_diagram_style(
                    "dependencies",
                    root=plugin_root,
                    fallback_root=plugin_fallback,
                    detail=state.options.dependency_graph_detail,
                ),
            ),
        ),
        (
            "load-order",
            "Load order",
            _generate_load_order_md(analysis, module_page_map),
        ),
    )

    architecture_entries: list[dict] = []
    created = 0
    for stem, label, content in pages:
        page_path = state.options.wiki_dir / f"{stem}.md"
        if page_path.exists() and not state.options.overwrite:
            state.skipped_files.append(_path_text(page_path))
            _emit_bootstrap(state, f"  SKIP architecture (exists): {stem}")
        else:
            _write_bootstrap_file(state, page_path, content)
            created += 1
            _emit_bootstrap(state, f"  CREATE architecture: {stem}")
        # Linked from the index regardless of skip so existing pages are not
        # orphaned by lint.
        architecture_entries.append({"name": label, "page": stem})

    _emit_bootstrap(state, f"Generated architecture pages: {created}.", flush=True)
    summary = {
        "generated": True,
        "pages_created": created,
        **_dependency_counts(analysis),
    }
    return _DependencyResult(
        architecture_entries,
        created,
        summary,
        analysis.get("metrics", {}),
    )


def _write_bootstrap_index(
    state: _BootstrapRunState,
    entity_result: _EntityModuleResult,
    workflow_result: _WorkflowResult,
    flow_result: _FlowResult,
    infrastructure_result: _InfrastructureResult,
    dependency_result: _DependencyResult,
    api_contract_result: _ApiContractResult,
) -> None:
    index_path = state.options.wiki_dir / "index.md"
    _write_bootstrap_file(
        state,
        index_path,
        _generate_index_md(
            entity_result.all_entity_names,
            entity_result.module_entries,
            workflow_entries=workflow_result.entries or None,
            guide_entries=None,
            infra_entries=infrastructure_result.entries or None,
            flow_entries=flow_result.entries or None,
            architecture_entries=dependency_result.architecture_entries or None,
            api_contracts_present=api_contract_result.present,
        ),
    )
    _emit_bootstrap(state, "  WRITE index.md")


def _append_bootstrap_log(
    state: _BootstrapRunState,
    inventory: dict,
    entity_result: _EntityModuleResult,
    workflow_result: _WorkflowResult,
    flow_result: _FlowResult,
    infrastructure_result: _InfrastructureResult,
    dependency_result: _DependencyResult,
    api_contract_result: _ApiContractResult,
    cross_reference_count: int,
) -> None:
    log_path = state.options.wiki_dir / "log.md"
    github_actions_count = _infrastructure_type_count(
        infrastructure_result, "github_actions"
    )
    kubernetes_count = _infrastructure_type_count(infrastructure_result, "kubernetes")
    runtime_config_count = _runtime_config_count(infrastructure_result)
    log_entry = (
        f"\n## {date.today().isoformat()}\n\n"
        f"### feat: bootstrap wiki from existing codebase\n"
        f"- Source: `{state.options.src_dir_for_scan}`\n"
        f"- Depth: `{state.options.depth}`\n"
        f"- Entities created: {entity_result.entities_created}\n"
        f"- Modules created: {entity_result.modules_created}\n"
        f"- Workflows created: {workflow_result.created}\n"
        f"- User flows created: {flow_result.created}\n"
        f"- Infrastructure created: {infrastructure_result.created}\n"
        f"- Architecture pages created: {dependency_result.created}\n"
        f"- API contract pages created: {api_contract_result.created}\n"
        f"- API operations tracked: "
        f"{len((api_contract_result.contracts or {}).get('operations', []))}\n"
        f"- Total classes tracked: {len(entity_result.all_entity_names)}\n"
        f"- Total files scanned: {len(inventory)}\n"
        f"- Docker/Compose files: {len(infrastructure_result.docker_inventory)}\n"
        f"- GitHub Actions files: {github_actions_count}\n"
        f"- Kubernetes files: {kubernetes_count}\n"
        f"- Runtime/config YAML files: {runtime_config_count}\n"
        f"- Cross-references resolved: {cross_reference_count}\n"
    )
    if log_path.exists():
        existing_log = read_md(log_path)
        _write_bootstrap_file(state, log_path, existing_log + log_entry)
    else:
        _write_bootstrap_file(
            state,
            log_path,
            "# Architectural Log\n\nAppend-only chronological log.\n" + log_entry,
        )


def _emit_bootstrap_complete(
    state: _BootstrapRunState,
    inventory: dict,
    entity_result: _EntityModuleResult,
    workflow_result: _WorkflowResult,
    flow_result: _FlowResult,
    infrastructure_result: _InfrastructureResult,
    dependency_result: _DependencyResult,
    api_contract_result: _ApiContractResult,
    cross_reference_count: int,
) -> None:
    _emit_bootstrap(
        state,
        f"\nBootstrap complete: {entity_result.entities_created} entities, "
        f"{entity_result.modules_created} modules, {workflow_result.created} workflows, "
        f"{flow_result.created} flows, "
        f"{infrastructure_result.created} infrastructure, "
        f"{dependency_result.created} architecture "
        f"and {api_contract_result.created} API contract pages "
        f"created from {len(inventory)} source files "
        f"({cross_reference_count} cross-references).",
    )


def _update_bootstrap_agent_constraints(state: _BootstrapRunState) -> None:
    if not state.options.source_adapter:
        _update_agent_constraints(
            str(state.options.wiki_dir), file=state.options.progress_stream
        )


def _bootstrap_manifest_generation_state(
    state: _BootstrapRunState,
    api_contract_result: _ApiContractResult,
) -> tuple[dict[str, dict[str, object]], dict[str, object]]:
    surfaces: dict[str, dict[str, object]] = {
        "flows": {
            "enabled": bool(state.options.deep and not state.options.skip_flows),
            "categories": None,
            "exclude_tests": False,
        },
        "dependencies": {
            "enabled": bool(state.options.deep and not state.options.skip_dependencies),
            "exclude_tests": False,
        },
        "api_contracts": {
            "enabled": bool(state.options.api_contracts or api_contract_result.present)
        },
    }
    generation_inputs = persist_runtime_generation_policy(
        {},
        data_flow_enabled=bool(
            state.options.deep
            and not state.options.skip_flows
            and not state.options.skip_data_flow
        ),
        dependency_graph_detail=state.options.dependency_graph_detail,
        workflows_enabled=bool(state.options.deep and not state.options.skip_workflows),
    )
    openapi = (api_contract_result.contracts or {}).get("openapi")
    if isinstance(openapi, Mapping):
        generation_inputs["openapi"] = {
            key: openapi[key] for key in ("path", "sha256", "format") if key in openapi
        }
    return surfaces, generation_inputs


def _load_previous_bootstrap_manifest(wiki_dir: Path) -> SyncManifest | None:
    try:
        return SyncManifest.load(wiki_dir)
    except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _record_bootstrap_artifact(
    state: _BootstrapRunState,
    *,
    path: Path,
    write_state: ArtifactWriteState,
) -> None:
    if write_state is ArtifactWriteState.UNCHANGED:
        state.skipped_files.append(_path_text(path))
        _emit_bootstrap(state, f"  SKIP {path} (unchanged)")
        return
    _record_bootstrap_write(
        state,
        path,
        write_state is ArtifactWriteState.UPDATED,
    )
    action = "CREATE" if write_state is ArtifactWriteState.CREATED else "UPDATE"
    _emit_bootstrap(state, f"  {action} {path}")


def _finalize_bootstrap_artifacts(
    state: _BootstrapRunState,
    inventory_result: InventoryResult,
    page_maps: _BootstrapPageMaps,
    result: _BootstrapGenerationResult,
) -> KnowledgeCommitResult:
    inventory = inventory_result.inventory
    surface = evaluate_surface_index(
        state.options.wiki_dir,
        inventory,
        src_dir=state.options.src_dir_for_scan,
        entity_page_cache=page_maps.entity_page_name_cache,
        entity_occurrence_page_cache=page_maps.entity_occurrence_page_name_cache,
        module_page_map=page_maps.module_page_map,
        entry_points=result.flow.entries,
    )
    surfaces, generation_inputs = _bootstrap_manifest_generation_state(
        state,
        result.api_contract,
    )
    _emit_bootstrap(state, "Writing generated knowledge artifacts...", flush=True)
    _emit_bootstrap(state, "Writing sync manifest...", flush=True)
    committed = finalize_runtime_knowledge(
        RuntimeKnowledgeInputs(
            target_wiki_dir=state.options.wiki_dir,
            inventory=inventory,
            surface=surface,
            source_snapshot=state.source_snapshot,
            module_page_map=page_maps.module_page_map,
            entity_occurrence_page_map=(page_maps.entity_occurrence_page_name_cache),
            repository_evidence=collect_runtime_repository_evidence(
                state.options.src_dir_for_scan,
                state.options.wiki_dir,
            ),
            inventory_complete=state.options.deep,
            previous_manifest=_load_previous_bootstrap_manifest(state.options.wiki_dir),
            manifest_surfaces=surfaces,
            manifest_generation_inputs=generation_inputs,
            untrusted_evidence_page_paths={
                page.relative_path
                for page in surface.pages
                if page.kind in {PageKind.ENTITIES, PageKind.MODULES}
                and page.relative_path not in state.written_structural_page_paths
            },
            regenerated_evidence_page_paths=frozenset(
                state.written_structural_page_paths
            ),
            extractor_registry=inventory_result.extractor_registry,
            plugin_extractor_components=inventory_result.plugin_components,
            plugin_components=inventory_result.producer_plugin_components,
            plugin_lock_path=inventory_result.plugin_lock_path,
            plugin_lock_hash=inventory_result.plugin_lock_hash,
            generation_options=runtime_generation_options(
                surfaces=surfaces,
                generation_inputs=generation_inputs,
                include_tests=state.options.include_tests,
                preserve_semantic=True,
            ),
            generation_option_defaults=RUNTIME_GENERATION_OPTION_DEFAULTS,
            generation_option_allowlist=tuple(RUNTIME_GENERATION_OPTION_DEFAULTS),
            call_edges=result.call_observations,
            dependency_observations=result.dependency_observations,
            entrypoint_observations=result.flow.entrypoint_observations,
            flows=result.flow.flows,
            data_flows=result.flow.data_flows,
            external_dependencies=result.external_dependencies,
            graph_analyzer_limitations=result.graph_analyzer_limitations,
        )
    )
    for artifact in (
        committed.surface_index,
        committed.knowledge_index,
        committed.manifest,
    ):
        _record_bootstrap_artifact(
            state,
            path=artifact.path,
            write_state=artifact.state,
        )
    return committed


def _emit_bootstrap_json_summary(
    state: _BootstrapRunState,
    inventory: dict,
    workflow_result: _WorkflowResult,
    flow_result: _FlowResult,
    infrastructure_result: _InfrastructureResult,
    dependency_result: _DependencyResult,
    api_contract_result: _ApiContractResult,
    cross_reference_count: int,
    artifacts: KnowledgeCommitResult,
) -> dict[str, Any]:
    summary = _with_unsupported_sources(
        {
            "schema_version": BOOTSTRAP_SUMMARY_SCHEMA_VERSION,
            "src_dir": state.options.src_dir_for_scan,
            "generated_wiki_path": _path_text(state.options.wiki_dir),
            "depth": state.options.depth,
            "source_files": len(state.source_snapshot.all_source_paths),
            "classes": sum(len(data.get("classes", [])) for data in inventory.values()),
            "functions": sum(
                len(data.get("functions", [])) for data in inventory.values()
            ),
            "docker_files": len(infrastructure_result.docker_inventory),
            "infrastructure_files": len(infrastructure_result.infrastructure_inventory),
            "github_actions_files": _infrastructure_type_count(
                infrastructure_result, "github_actions"
            ),
            "kubernetes_files": _infrastructure_type_count(
                infrastructure_result, "kubernetes"
            ),
            "runtime_config_files": _runtime_config_count(infrastructure_result),
            "runtime_config_by_type": _runtime_config_type_counts(
                infrastructure_result
            ),
            "workflows": len(workflow_result.entries),
            "flows": len(flow_result.entries),
            "flow_evidence": flow_result.entries,
            "data_flows": flow_result.data_flow_summary,
            "dependencies": dependency_result.summary,
            "dependency_evidence": dependency_result.evidence,
            "api_contracts": {
                "generated": api_contract_result.present,
                "source": (api_contract_result.contracts or {}).get("source"),
                "operations": len(
                    (api_contract_result.contracts or {}).get("operations", [])
                ),
            },
            "cross_references": cross_reference_count,
            "created_files": state.created_files,
            "updated_files": state.updated_files,
            "skipped_files": state.skipped_files,
            "manifest_path": _path_text(artifacts.manifest.path),
            "knowledge_path": _path_text(artifacts.knowledge_index.path),
            "knowledge_status": artifacts.knowledge_index.state.value,
            "knowledge_schema_version": KNOWLEDGE_SCHEMA_VERSION,
        },
        state.unsupported_sources,
    )
    if state.warnings:
        summary["warnings"] = state.warnings
    state.summary = summary
    if state.options.json_mode:
        print(json.dumps(summary, indent=2))
    return summary


def _generate_bootstrap_content(
    state: _BootstrapRunState,
    inventory: dict,
    page_maps: _BootstrapPageMaps,
    *,
    data_effect_observations: Mapping | None = None,
    import_observations: Mapping | None = None,
) -> _BootstrapGenerationResult:
    api_contracts = _build_bootstrap_api_contracts(state, inventory)
    call_edges = resolve_call_edges(inventory) if state.options.deep else []
    call_observations = (
        resolve_call_observations(inventory) if state.options.deep else {}
    )
    dependency_observations = (
        build_dependency_observations(
            inventory,
            state.options.src_dir_for_scan,
            source_snapshot=state.source_snapshot,
            import_observations=import_observations,
        )
        if state.options.deep
        else {}
    )
    entity_relationship_summaries = (
        _build_entity_relationship_summary_map(inventory, call_edges)
        if state.options.deep
        else None
    )
    dependency_analysis = _build_bootstrap_dependency_analysis(state, inventory)
    external_dependencies = (
        build_external_dependency_observations(dependency_analysis)
        if dependency_analysis is not None
        else []
    )
    graph_analyzer_limitations: dict[str, tuple[str, ...]] = {}
    if not state.options.deep:
        for analyzer in (
            "calls",
            "dependencies",
            "entrypoints",
            "flows",
            "data-flows",
            "external-dependencies",
        ):
            graph_analyzer_limitations[analyzer] = (
                "deep-analysis-disabled",
            )
    elif dependency_analysis is None:
        graph_analyzer_limitations["external-dependencies"] = (
            "dependency-analysis-disabled",
        )
    if state.options.deep and state.options.skip_flows:
        graph_analyzer_limitations["entrypoints"] = ("flow-analysis-disabled",)
        graph_analyzer_limitations["flows"] = ("flow-analysis-disabled",)
        graph_analyzer_limitations["data-flows"] = ("flow-analysis-disabled",)
    elif state.options.deep and state.options.skip_data_flow:
        graph_analyzer_limitations["data-flows"] = ("data-flow-analysis-disabled",)
    module_dependency_maps = (
        build_module_dependency_maps(dependency_analysis)
        if dependency_analysis is not None
        else None
    )
    relationships, cross_reference_count = _build_bootstrap_relationships(
        state,
        inventory,
        page_maps.module_page_map,
    )
    entity_result = _write_entity_and_module_pages(
        state,
        inventory,
        page_maps,
        relationships,
        entity_relationship_summaries,
        module_dependency_maps,
    )
    workflow_result = _write_bootstrap_workflow_pages(
        state, inventory, page_maps.module_page_map
    )
    flow_result = _write_bootstrap_flow_pages(
        state,
        inventory,
        page_maps.module_page_map,
        call_edges=call_edges,
        api_contracts=api_contracts,
        data_effect_observations=data_effect_observations,
    )
    api_contract_result = _write_bootstrap_api_contract_page(
        state, api_contracts, page_maps
    )
    infrastructure_result = _write_bootstrap_infrastructure_pages(
        state, page_maps.module_page_map
    )
    dependency_result = _write_bootstrap_dependency_pages(
        state,
        inventory,
        page_maps.module_page_map,
        analysis=dependency_analysis,
    )
    return _BootstrapGenerationResult(
        entity=entity_result,
        workflow=workflow_result,
        flow=flow_result,
        infrastructure=infrastructure_result,
        dependency=dependency_result,
        api_contract=api_contract_result,
        cross_reference_count=cross_reference_count,
        call_observations=call_observations,
        dependency_observations=dependency_observations,
        external_dependencies=external_dependencies,
        graph_analyzer_limitations=graph_analyzer_limitations,
    )


def _finalize_bootstrap(
    state: _BootstrapRunState,
    inventory_result: InventoryResult,
    page_maps: _BootstrapPageMaps,
    result: _BootstrapGenerationResult,
) -> BootstrapResult:
    inventory = inventory_result.inventory
    _write_bootstrap_index(
        state,
        result.entity,
        result.workflow,
        result.flow,
        result.infrastructure,
        result.dependency,
        result.api_contract,
    )
    _append_bootstrap_log(
        state,
        inventory,
        result.entity,
        result.workflow,
        result.flow,
        result.infrastructure,
        result.dependency,
        result.api_contract,
        result.cross_reference_count,
    )
    _update_bootstrap_agent_constraints(state)
    artifacts = _finalize_bootstrap_artifacts(
        state,
        inventory_result,
        page_maps,
        result,
    )
    _emit_bootstrap_complete(
        state,
        inventory,
        result.entity,
        result.workflow,
        result.flow,
        result.infrastructure,
        result.dependency,
        result.api_contract,
        result.cross_reference_count,
    )
    _emit_bootstrap_json_summary(
        state,
        inventory,
        result.workflow,
        result.flow,
        result.infrastructure,
        result.dependency,
        result.api_contract,
        result.cross_reference_count,
        artifacts,
    )
    return _bootstrap_result(state)


def _bootstrap_result(state: _BootstrapRunState) -> BootstrapResult:
    if state.summary is None:
        raise BootstrapContractError("Bootstrap completed without a summary payload.")
    return BootstrapResult(
        summary=dict(state.summary),
        created_files=tuple(state.created_files),
        updated_files=tuple(state.updated_files),
        skipped_files=tuple(state.skipped_files),
        warnings=tuple(state.warnings),
    )


def _execute_bootstrap_options(options: _BootstrapRunOptions) -> BootstrapResult:
    state = _BootstrapRunState(options)
    _start_bootstrap(state)

    inventory_result = _extract_bootstrap_inventory(state)
    inventory = inventory_result.inventory
    if not state.options.openapi_file and _finish_if_empty_bootstrap_inventory(
        state, inventory
    ):
        return _bootstrap_result(state)

    page_maps = _prepare_bootstrap_page_maps(inventory)
    try:
        result = _generate_bootstrap_content(
            state,
            inventory,
            page_maps,
            data_effect_observations=inventory_result.data_effect_observations,
            import_observations=inventory_result.import_observations,
        )
    except ApiContractError as exc:
        raise BootstrapContractError(str(exc)) from exc
    return _finalize_bootstrap(state, inventory_result, page_maps, result)


def execute_bootstrap(
    request: BootstrapRequest,
    *,
    progress_stream: TextIO | None = None,
) -> BootstrapResult:
    """Execute deterministic bootstrap without argparse, printing, or exits."""

    stream = progress_stream if progress_stream is not None else io.StringIO()
    options = _bootstrap_run_options_from_request(request, progress_stream=stream)
    return _execute_bootstrap_options(options)


def run(args):
    options = _bootstrap_run_options_from_args(args)
    try:
        _execute_bootstrap_options(options)
    except BootstrapExtractionError:
        raise SystemExit(1)
    except BootstrapContractError as exc:
        print(f"Error: {exc}", file=options.progress_stream)
        raise SystemExit(2) from exc


def _update_agent_constraints(wiki_dir: str, *, file=None) -> None:
    """Replace docs/llm_wiki path references inside the constraint block
    in any existing agent schema files to match the actual wiki_dir."""
    stream = file or sys.stdout
    # Normalize: treat both as Path to allow absolute/relative comparison
    wiki_path = Path(wiki_dir)
    default_path = Path(_DEFAULT_WIKI_DIR)
    # Nothing to do if the resolved paths are the same or wiki_dir already
    # contains the default string (handles the relative == relative case)
    if wiki_path == default_path or wiki_dir == _DEFAULT_WIKI_DIR:
        return
    # Also skip if the resolved absolute paths are equivalent
    try:
        if wiki_path.resolve() == default_path.resolve():
            return
    except OSError:
        pass

    updated = []
    for filename in _AGENT_SCHEMA_FILES:
        p = Path(filename)
        if not p.exists():
            continue
        text = read_md(p)
        if _CONSTRAINT_START not in text or _CONSTRAINT_END not in text:
            continue

        # Replace only within the constraint block to avoid touching user content
        start_idx = text.index(_CONSTRAINT_START)
        end_idx = text.index(_CONSTRAINT_END, start_idx) + len(_CONSTRAINT_END)
        block = text[start_idx:end_idx]
        new_block = block.replace(_DEFAULT_WIKI_DIR, wiki_dir)
        if new_block != block:
            write_md(p, text[:start_idx] + new_block + text[end_idx:])
            updated.append(filename)

    if updated:
        print(
            f"\nUpdated wiki path to `{wiki_dir}` in: {', '.join(updated)}", file=stream
        )
