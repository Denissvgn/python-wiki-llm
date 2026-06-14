from __future__ import annotations

import json
import shlex
import sys
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, TextIO

from .extract_cmd import (
    get_call_graph,
    get_docker_inventory,
    get_inventory_result,
    print_inventory_failures,
)
from ..config import (
    DEFAULT_WIKI_DIR as _DEFAULT_WIKI_DIR,
    validate_path,
    validate_source_root,
)
from ..services.contracts import BOOTSTRAP_SUMMARY_SCHEMA_VERSION
from ..services.imports import ModulePathResolver, build_module_path_resolver
from ..services.io import read_md, write_md
from ..services.paths import normalize_source_path
from ..services.schema import (
    ALL_SCHEMA_FILES as _AGENT_SCHEMA_FILES,
    CONSTRAINT_END as _CONSTRAINT_END,
    CONSTRAINT_START as _CONSTRAINT_START,
)
from ..services.source_snapshot import build_source_snapshot


def _module_name_from_path(filepath: str) -> str:
    """Derive a short module name from a file path."""
    return Path(filepath).stem


def _page_name_for_module(filepath: str) -> str:
    """Return the wiki page stem for a module.

    For collision-aware naming use :func:`build_module_page_map` instead.
    """
    return Path(filepath).stem


def _page_name_for_entity(cls_name: str) -> str:
    """Return the wiki page stem for an entity.

    For collision-aware naming use :func:`build_entity_page_map` instead.
    """
    return cls_name


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


def build_module_page_map(inventory: dict) -> dict[str, str]:
    """Return ``{filepath: page_stem}`` qualifying colliding stems.

    When two files share the same stem (e.g. ``pkg_a/cli.py`` and
    ``pkg_b/cli.py``) parent directory components are prepended to
    disambiguate.  Non-colliding stems keep their short name.
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
    return page_map


def build_entity_page_map(inventory: dict) -> dict[tuple[str, str], str]:
    """Return ``{(class_name, filepath): page_stem}`` qualifying collisions.

    Uses the already-disambiguated module page name as prefix when two
    classes share the same name across different files.  This guarantees
    uniqueness because module page names are themselves unique.
    """
    from collections import Counter

    cls_count: Counter[str] = Counter()
    for fp, data in inventory.items():
        for cls in data.get("classes", []):
            cls_count[cls["name"]] += 1

    mod_page_map = build_module_page_map(inventory)

    page_map: dict[tuple[str, str], str] = {}
    for fp, data in inventory.items():
        for cls in data.get("classes", []):
            name = cls["name"]
            if cls_count[name] > 1:
                page_map[(name, fp)] = f"{mod_page_map[fp]}_{name}"
            else:
                page_map[(name, fp)] = name
    return page_map


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
    params = []
    for p in fn.get("params", []):
        part = p["name"]
        if p.get("type"):
            part += f": {p['type']}"
        if p.get("default"):
            part += f" = {p['default']}"
        params.append(part)

    ret = fn.get("return_type", "")
    sig = f"({', '.join(params)})"
    if ret:
        sig += f" -> {ret}"
    return sig


def _generate_entity_md(
    class_info: dict,
    filepath: str,
    relationships: dict,
    mod_page_name: str | None = None,
) -> str:
    """Generate comprehensive markdown for a class entity."""
    name = class_info["name"]
    bases = class_info.get("bases", [])
    line = class_info.get("line", "?")
    docstring = class_info.get("docstring", "")
    decorators = class_info.get("decorators", [])
    attributes = class_info.get("attributes", [])
    methods = class_info.get("methods", [])
    mod_name = (
        mod_page_name if mod_page_name is not None else _module_name_from_path(filepath)
    )

    bases_str = ", ".join(f"`{b}`" for b in bases) if bases else "—"

    lines = [
        f"# {name}",
        "",
        f"**Location:** `{filepath}:{line}`",
        f"**Bases:** {bases_str}",
        f"**Module:** [{mod_name}](../modules/{mod_name}.md)",
        "",
    ]

    if decorators:
        lines.append(f"**Decorators:** {', '.join(f'`@{d}`' for d in decorators)}")
        lines.append("")

    # Description
    lines.append("## Description")
    lines.append("")
    if docstring:
        lines.append(docstring)
    else:
        lines.append(f"_Auto-generated from `{name}` in `{filepath}`._")
    lines.append("")

    # Attributes
    lines.append("## Attributes")
    lines.append("")
    if attributes:
        lines.append("| Name | Type | Default | Description |")
        lines.append("|------|------|---------|-------------|")
        for attr in attributes:
            default = f"`{attr['default']}`" if attr.get("default") else "*required*"
            lines.append(
                f"| `{attr['name']}` | `{attr.get('type', '—')}` | {default} | — |"
            )
    else:
        lines.append("*No annotated attributes found.*")
    lines.append("")

    # Methods
    lines.append("## Methods")
    lines.append("")
    if methods:
        lines.append("| Method | Signature | Decorators | Description |")
        lines.append("|--------|-----------|------------|-------------|")
        for m in methods:
            sig = _format_signature(m)
            decs = ", ".join(f"`@{d}`" for d in m.get("decorators", [])) or "—"
            doc = m.get("docstring", "").split("\n")[0] if m.get("docstring") else "—"
            async_tag = "*(async)* " if m.get("is_async") else ""
            lines.append(f"| `{m['name']}` | `{async_tag}{sig}` | {decs} | {doc} |")
    else:
        lines.append("*No public methods. Inherits from base classes.*")
    lines.append("")

    # Relationships
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

    return "\n".join(lines)


def _generate_module_md(
    filepath: str, file_data: dict, entity_page_map: dict | None = None
) -> str:
    """Generate comprehensive markdown for a module page."""
    mod_name = _module_name_from_path(filepath)
    classes = file_data.get("classes", [])
    functions = file_data.get("functions", [])
    imports = file_data.get("imports", [])
    module_docstring = file_data.get("module_docstring", "")

    lines = [
        f"# {mod_name} Module",
        "",
        f"**Path:** `{filepath}`",
        "",
    ]

    # Description
    lines.append("## Description")
    lines.append("")
    if module_docstring:
        lines.append(module_docstring)
    else:
        lines.append(f"_Auto-generated from `{filepath}`._")
    lines.append("")

    # Imports
    if imports:
        # Group imports by source module
        grouped: dict[str, list[str]] = defaultdict(list)
        for imp in imports:
            grouped[imp["module"]].append(imp["name"])

        lines.append("## Imports")
        lines.append("")
        lines.append("| Source | Symbols |")
        lines.append("|--------|---------|")
        for module, names in sorted(grouped.items()):
            lines.append(f"| `{module}` | {', '.join(f'`{n}`' for n in names)} |")
        lines.append("")

    # Classes
    if classes:
        lines.append("## Classes")
        lines.append("")
        lines.append("| Class | Line | Bases | Description |")
        lines.append("|-------|------|-------|-------------|")
        for c in classes:
            page_name = (entity_page_map or {}).get(c["name"], c["name"])
            entity_link = f"[{c['name']}](../entities/{page_name}.md)"
            bases = ", ".join(f"`{b}`" for b in c.get("bases", [])) or "—"
            doc = c.get("docstring", "").split("\n")[0] if c.get("docstring") else "—"
            lines.append(f"| {entity_link} | {c.get('line', '?')} | {bases} | {doc} |")
        lines.append("")

    # Functions
    if functions:
        lines.append("## Functions")
        lines.append("")
        lines.append("| Function | Signature | Decorators | Description |")
        lines.append("|----------|-----------|------------|-------------|")
        for fn in functions:
            sig = _format_signature(fn)
            decs = ", ".join(f"`@{d}`" for d in fn.get("decorators", [])) or "—"
            doc = fn.get("docstring", "").split("\n")[0] if fn.get("docstring") else "—"
            async_tag = "*(async)* " if fn.get("is_async") else ""
            lines.append(f"| `{fn['name']}` | `{async_tag}{sig}` | {decs} | {doc} |")
        lines.append("")

    return "\n".join(lines)


def _generate_index_md(
    entity_names: list[str],
    module_entries: list[dict],
    workflow_entries: list[dict] | None = None,
    infra_entries: list[dict] | None = None,
) -> str:
    """Generate the full index.md content."""
    lines = [
        "# LLM Wiki Index",
        "",
        "Catalog of project modules and entities.",
        "",
        "## Entities",
        "",
    ]

    for name in sorted(entity_names):
        lines.append(f"- [{name}](entities/{name}.md)")

    lines.append("")
    lines.append("## Modules")
    lines.append("")

    for entry in sorted(module_entries, key=lambda e: e["name"]):
        desc = entry.get("docstring", "")
        suffix = f" - {desc}" if desc else f" - `{entry['path']}`"
        lines.append(f"- [{entry['name']}](modules/{entry['name']}.md){suffix}")

    lines.append("")
    lines.append("## Workflows")
    lines.append("")

    if workflow_entries:
        for wf in sorted(workflow_entries, key=lambda w: w["name"]):
            entry_point = wf.get("entry", "")
            lines.append(
                f"- [{wf['name']}](workflows/{wf['name']}.md) - entry: `{entry_point}`"
            )
        lines.append("")

    lines.append("## Infrastructure")
    lines.append("")

    if infra_entries:
        for entry in sorted(infra_entries, key=lambda e: e["name"]):
            desc = entry.get("type", "")
            suffix = f" - {desc}" if desc else ""
            lines.append(
                f"- [{entry['name']}](infrastructure/{entry['name']}.md){suffix}"
            )
        lines.append("")

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
        lines.append(f"> {docstring}")
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


def _generate_docker_md(
    filename: str,
    info: dict,
    module_links: Mapping[str, str] | set[str] | None = None,
    *,
    module_stems: set[str] | None = None,
) -> str:
    """Generate a wiki page for a Dockerfile or docker-compose file."""
    if module_links is None and module_stems is not None:
        module_links = module_stems
    if info["type"] == "dockerfile":
        return _generate_dockerfile_md(filename, info, module_links)
    return _generate_compose_md(filename, info, module_links)


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
    filename: str, info: dict, module_links: Mapping[str, str] | set[str] | None = None
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
    overwrite: bool
    json_mode: bool
    source_adapter: bool
    progress_stream: TextIO


@dataclass
class _BootstrapRunState:
    options: _BootstrapRunOptions
    source_snapshot: Any = None
    created_files: list[str] = field(default_factory=list)
    updated_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class _BootstrapPageMaps:
    module_page_map: dict[str, str]
    entity_page_name_cache: dict[tuple[str, str], str]


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
class _InfrastructureResult:
    entries: list[dict]
    created: int
    docker_inventory: dict


@dataclass(frozen=True)
class _BootstrapGenerationResult:
    entity: _EntityModuleResult
    workflow: _WorkflowResult
    infrastructure: _InfrastructureResult
    cross_reference_count: int


def _bootstrap_run_options_from_args(args) -> _BootstrapRunOptions:
    src_dir = args.src_dir
    wiki_dir = Path(args.wiki_dir)
    validate_path(str(wiki_dir), "--wiki-dir")
    src_root = validate_source_root(
        src_dir,
        "--src-dir",
        allow_external=getattr(args, "allow_external_src", False),
    )
    depth = getattr(args, "depth", "full")
    json_mode = getattr(args, "format", "text") == "json"
    return _BootstrapRunOptions(
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        src_dir_for_scan=str(src_root),
        depth=depth,
        deep=depth == "full",
        skip_workflows=getattr(args, "skip_workflows", False),
        overwrite=args.overwrite,
        json_mode=json_mode,
        source_adapter=getattr(args, "source_adapter", False),
        progress_stream=sys.stderr if json_mode else sys.stdout,
    )


def _path_text(path: Path) -> str:
    return str(path).replace("\\", "/")


def _emit_bootstrap(
    state: _BootstrapRunState, message: str = "", *, flush: bool = False
) -> None:
    print(message, file=state.options.progress_stream, flush=flush)


def _record_bootstrap_write(
    state: _BootstrapRunState, path: Path, existed: bool
) -> None:
    target = state.updated_files if existed else state.created_files
    target.append(_path_text(path))


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
    for subdir in ["entities", "modules", "workflows", "infrastructure"]:
        (options.wiki_dir / subdir).mkdir(parents=True, exist_ok=True)


def _extract_bootstrap_inventory(state: _BootstrapRunState):
    options = state.options
    _emit_bootstrap(state, "Extracting source inventory...", flush=True)
    state.source_snapshot = build_source_snapshot(options.src_dir_for_scan)
    inventory_result = get_inventory_result(
        options.src_dir_for_scan,
        deep=options.deep,
        source_snapshot=state.source_snapshot,
    )
    if inventory_result.failed:
        print_inventory_failures(inventory_result, file=options.progress_stream)
        sys.exit(1)
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
        "No supported source files with classes or functions found. Nothing to bootstrap.",
    )
    if options.json_mode:
        print(
            json.dumps(
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
                    "cross_references": 0,
                    "created_files": state.created_files,
                    "updated_files": state.updated_files,
                    "skipped_files": state.skipped_files,
                    "manifest_path": None,
                },
                indent=2,
            )
        )
    return True


def _prepare_bootstrap_page_maps(inventory: dict) -> _BootstrapPageMaps:
    return _BootstrapPageMaps(
        module_page_map=build_module_page_map(inventory),
        entity_page_name_cache=build_entity_page_map(inventory),
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


def _write_bootstrap_entity_pages(
    state: _BootstrapRunState,
    filepath: str,
    file_data: dict,
    relationships: dict,
    mod_page_name: str,
    file_entity_page_map: dict[str, str],
    seen_entity_pages: set[str],
    all_entity_names: list[str],
) -> int:
    entities_created = 0
    for cls in file_data.get("classes", []):
        entity_page_name = file_entity_page_map[cls["name"]]
        entity_path = state.options.wiki_dir / "entities" / f"{entity_page_name}.md"
        if entity_path.exists() and not state.options.overwrite:
            state.skipped_files.append(_path_text(entity_path))
            _emit_bootstrap(state, f"  SKIP entity (exists): {entity_page_name}")
        else:
            _write_bootstrap_file(
                state,
                entity_path,
                _generate_entity_md(cls, filepath, relationships, mod_page_name),
            )
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
) -> bool:
    module_path = state.options.wiki_dir / "modules" / f"{mod_page_name}.md"
    if module_path.exists() and not state.options.overwrite:
        state.skipped_files.append(_path_text(module_path))
        _emit_bootstrap(state, f"  SKIP module (exists): {mod_page_name}")
        return False

    _write_bootstrap_file(
        state,
        module_path,
        _generate_module_md(filepath, file_data, file_entity_page_map),
    )
    _emit_bootstrap(state, f"  CREATE module: {mod_page_name}")
    return True


def _write_entity_and_module_pages(
    state: _BootstrapRunState,
    inventory: dict,
    page_maps: _BootstrapPageMaps,
    relationships: dict,
) -> _EntityModuleResult:
    all_entity_names: list[str] = []
    module_entries: list[dict] = []
    seen_entity_pages: set[str] = set()
    entities_created = 0
    modules_created = 0

    _emit_bootstrap(state, "Generating entity and module pages...", flush=True)
    for filepath, file_data in inventory.items():
        mod_page_name = page_maps.module_page_map[filepath]
        file_entity_page_map = {
            cls["name"]: page_maps.entity_page_name_cache[(cls["name"], filepath)]
            for cls in file_data.get("classes", [])
        }
        entities_created += _write_bootstrap_entity_pages(
            state,
            filepath,
            file_data,
            relationships,
            mod_page_name,
            file_entity_page_map,
            seen_entity_pages,
            all_entity_names,
        )
        if _write_bootstrap_module_page(
            state, filepath, file_data, mod_page_name, file_entity_page_map
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
    for docker_file, docker_info in docker_inventory.items():
        page_name = docker_file.replace("\\", "/").replace("/", "_").replace(".", "_")
        infra_path = state.options.wiki_dir / "infrastructure" / f"{page_name}.md"
        if infra_path.exists() and not state.options.overwrite:
            state.skipped_files.append(_path_text(infra_path))
            _emit_bootstrap(state, f"  SKIP infrastructure (exists): {page_name}")
        else:
            _write_bootstrap_file(
                state,
                infra_path,
                _generate_docker_md(docker_file, docker_info, module_page_map),
            )
            infra_created += 1
            _emit_bootstrap(state, f"  CREATE infrastructure: {page_name}")
        infra_entries.append({"name": page_name, "type": docker_info["type"]})
    _emit_bootstrap(
        state, f"Generated infrastructure pages: {infra_created}.", flush=True
    )
    return _InfrastructureResult(infra_entries, infra_created, docker_inventory)


def _write_bootstrap_index(
    state: _BootstrapRunState,
    entity_result: _EntityModuleResult,
    workflow_result: _WorkflowResult,
    infrastructure_result: _InfrastructureResult,
) -> None:
    index_path = state.options.wiki_dir / "index.md"
    _write_bootstrap_file(
        state,
        index_path,
        _generate_index_md(
            entity_result.all_entity_names,
            entity_result.module_entries,
            workflow_result.entries or None,
            infrastructure_result.entries or None,
        ),
    )
    _emit_bootstrap(state, "  WRITE index.md")


def _append_bootstrap_log(
    state: _BootstrapRunState,
    inventory: dict,
    entity_result: _EntityModuleResult,
    workflow_result: _WorkflowResult,
    infrastructure_result: _InfrastructureResult,
    cross_reference_count: int,
) -> None:
    log_path = state.options.wiki_dir / "log.md"
    log_entry = (
        f"\n## {date.today().isoformat()}\n\n"
        f"### feat: bootstrap wiki from existing codebase\n"
        f"- Source: `{state.options.src_dir_for_scan}`\n"
        f"- Depth: `{state.options.depth}`\n"
        f"- Entities created: {entity_result.entities_created}\n"
        f"- Modules created: {entity_result.modules_created}\n"
        f"- Workflows created: {workflow_result.created}\n"
        f"- Infrastructure created: {infrastructure_result.created}\n"
        f"- Total classes tracked: {len(entity_result.all_entity_names)}\n"
        f"- Total files scanned: {len(inventory)}\n"
        f"- Docker/Compose files: {len(infrastructure_result.docker_inventory)}\n"
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
    infrastructure_result: _InfrastructureResult,
    cross_reference_count: int,
) -> None:
    _emit_bootstrap(
        state,
        f"\nBootstrap complete: {entity_result.entities_created} entities, "
        f"{entity_result.modules_created} modules, {workflow_result.created} workflows, "
        f"{infrastructure_result.created} infrastructure "
        f"created from {len(inventory)} source files "
        f"({cross_reference_count} cross-references).",
    )


def _update_bootstrap_agent_constraints(state: _BootstrapRunState) -> None:
    if not state.options.source_adapter:
        _update_agent_constraints(
            str(state.options.wiki_dir), file=state.options.progress_stream
        )


def _write_bootstrap_manifest(
    state: _BootstrapRunState,
    inventory: dict,
    page_maps: _BootstrapPageMaps,
) -> Path:
    from .sync_cmd import SyncManifest  # local import to avoid circular dep

    manifest = SyncManifest.build_from_inventory(
        inventory,
        state.options.src_dir_for_scan,
        page_maps.entity_page_name_cache,
        page_maps.module_page_map,
    )
    _emit_bootstrap(state, "Writing sync manifest...", flush=True)
    manifest_path = state.options.wiki_dir / ".llm-wiki-manifest.json"
    manifest_existed = manifest_path.exists()
    manifest.save(state.options.wiki_dir)
    _record_bootstrap_write(state, manifest_path, manifest_existed)
    _emit_bootstrap(state, f"  WRITE {manifest_path}")
    return manifest_path


def _emit_bootstrap_json_summary(
    state: _BootstrapRunState,
    inventory: dict,
    workflow_result: _WorkflowResult,
    infrastructure_result: _InfrastructureResult,
    cross_reference_count: int,
    manifest_path: Path,
) -> None:
    if not state.options.json_mode:
        return

    print(
        json.dumps(
            {
                "schema_version": BOOTSTRAP_SUMMARY_SCHEMA_VERSION,
                "src_dir": state.options.src_dir_for_scan,
                "generated_wiki_path": _path_text(state.options.wiki_dir),
                "depth": state.options.depth,
                "source_files": len(state.source_snapshot.all_source_paths),
                "classes": sum(
                    len(data.get("classes", [])) for data in inventory.values()
                ),
                "functions": sum(
                    len(data.get("functions", [])) for data in inventory.values()
                ),
                "docker_files": len(infrastructure_result.docker_inventory),
                "workflows": len(workflow_result.entries),
                "cross_references": cross_reference_count,
                "created_files": state.created_files,
                "updated_files": state.updated_files,
                "skipped_files": state.skipped_files,
                "manifest_path": _path_text(manifest_path),
            },
            indent=2,
        )
    )


def _generate_bootstrap_content(
    state: _BootstrapRunState,
    inventory: dict,
    page_maps: _BootstrapPageMaps,
) -> _BootstrapGenerationResult:
    relationships, cross_reference_count = _build_bootstrap_relationships(
        state,
        inventory,
        page_maps.module_page_map,
    )
    entity_result = _write_entity_and_module_pages(
        state, inventory, page_maps, relationships
    )
    workflow_result = _write_bootstrap_workflow_pages(
        state, inventory, page_maps.module_page_map
    )
    infrastructure_result = _write_bootstrap_infrastructure_pages(
        state, page_maps.module_page_map
    )
    return _BootstrapGenerationResult(
        entity_result,
        workflow_result,
        infrastructure_result,
        cross_reference_count,
    )


def _finalize_bootstrap(
    state: _BootstrapRunState,
    inventory: dict,
    page_maps: _BootstrapPageMaps,
    result: _BootstrapGenerationResult,
) -> None:
    _write_bootstrap_index(state, result.entity, result.workflow, result.infrastructure)
    _append_bootstrap_log(
        state,
        inventory,
        result.entity,
        result.workflow,
        result.infrastructure,
        result.cross_reference_count,
    )
    _emit_bootstrap_complete(
        state,
        inventory,
        result.entity,
        result.workflow,
        result.infrastructure,
        result.cross_reference_count,
    )
    _update_bootstrap_agent_constraints(state)
    manifest_path = _write_bootstrap_manifest(state, inventory, page_maps)
    _emit_bootstrap_json_summary(
        state,
        inventory,
        result.workflow,
        result.infrastructure,
        result.cross_reference_count,
        manifest_path,
    )


def run(args):
    options = _bootstrap_run_options_from_args(args)
    state = _BootstrapRunState(options)
    _start_bootstrap(state)

    inventory_result = _extract_bootstrap_inventory(state)
    inventory = inventory_result.inventory
    if _finish_if_empty_bootstrap_inventory(state, inventory):
        return

    page_maps = _prepare_bootstrap_page_maps(inventory)
    result = _generate_bootstrap_content(state, inventory, page_maps)
    _finalize_bootstrap(state, inventory, page_maps, result)


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
