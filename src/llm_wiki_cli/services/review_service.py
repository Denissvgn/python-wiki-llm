"""Reusable source-to-wiki review analysis over one captured source basis."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR
from .bootstrap_runtime import (
    build_entity_occurrence_page_map,
    build_entity_page_map,
    build_module_page_map,
)
from .extraction_service import filter_source_diff, get_inventory_result
from .entrypoints import get_entry_points, read_console_scripts
from .plugins import (
    runtime_plugin_fallback_root,
    runtime_project_plugins_enabled,
)
from .source_selection import (
    resolve_source_selection,
    validate_persisted_source_selection_identity,
)
from .source_snapshot import (
    SourceSnapshot,
    build_source_snapshot,
    capture_source_selection_inputs,
)
from .sync_manifest import SyncManifest
from .wiki_surface import PageKind, collect_wiki_pages
from .wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
    build_surface_index,
)
from .change_selection import (
    _git,
    affected_page_map,
    patch_paths,
    select_changes,
    source_relative_paths,
)

_SOURCE_EXTS = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")
_DEPENDENCY_FILES = {
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "poetry.lock",
    "pdm.lock",
    "uv.lock",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
}
_ARCHITECTURE_PAGE_PATHS = {
    "api-contracts.md",
    "dependencies.md",
    "load-order.md",
}
_SYMBOL_REFERENCE_KINDS = {
    PageKind.WORKFLOWS,
    PageKind.FLOWS,
    PageKind.API_CONTRACTS,
    PageKind.DEPENDENCIES,
    PageKind.LOAD_ORDER,
}


@dataclass
class ReviewFinding:
    severity: str
    source_path: str
    wiki_pages: list[str]
    reason: str
    suggested_follow_up: str


@dataclass
class ReviewAnalysis:
    findings: list[ReviewFinding]
    changes: dict
    page_mapping: dict[str, list[str]]
    inventory: dict
    source_snapshot: SourceSnapshot


def _changed_paths(diff_text: str) -> list[str]:
    return patch_paths(diff_text)


def _added_imports_by_file(diff_text: str) -> dict[str, list[str]]:
    current: str | None = None
    imports: dict[str, list[str]] = {}
    for line in diff_text.splitlines():
        if line.startswith("+++ "):
            paths = patch_paths(line)
            current = paths[0] if paths else None
            continue
        if not current or not line.startswith("+") or line.startswith("+++"):
            continue
        stripped = line[1:].strip()
        if stripped.startswith("import "):
            module = stripped.split(" ", 1)[1].split(",", 1)[0].strip().split(".", 1)[0]
        elif stripped.startswith("from "):
            module = stripped.split(" ", 2)[1].split(".", 1)[0]
        else:
            continue
        if module:
            imports.setdefault(current, []).append(module)
    return imports


def _is_dependency_path(path: str) -> bool:
    name = Path(path).name
    normalized = path.replace("\\", "/")
    return (
        name in _DEPENDENCY_FILES
        or name.startswith("Dockerfile")
        or "docker-compose" in name
        or name.startswith("compose.")
        or normalized.endswith(".dockerfile")
    )


def _workflow_pages(wiki_dir: Path) -> dict[str, str]:
    workflows = wiki_dir / "workflows"
    if not workflows.exists():
        return {}
    result: dict[str, str] = {}
    for page in workflows.glob("*.md"):
        try:
            result[str(page.relative_to(wiki_dir))] = page.read_text(encoding="utf-8")
        except OSError:
            continue
    return result


def _surface_text_pages(wiki_dir: Path, kinds: set[PageKind]) -> dict[str, str]:
    result: dict[str, str] = {}
    for page in collect_wiki_pages(wiki_dir):
        if page.kind not in kinds:
            continue
        try:
            result[page.relative_path] = page.path.read_text(encoding="utf-8")
        except OSError:
            continue
    return result


def _symbol_reference_pages(wiki_dir: Path) -> dict[str, str]:
    pages = _workflow_pages(wiki_dir)
    pages.update(
        _surface_text_pages(
            wiki_dir,
            _SYMBOL_REFERENCE_KINDS - {PageKind.WORKFLOWS},
        )
    )
    return pages


def _workflow_symbol_index(
    workflows: dict[str, str], symbols: set[str]
) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {symbol: set() for symbol in symbols}
    if not workflows or not symbols:
        return index
    for page, content in workflows.items():
        for symbol in symbols:
            if symbol in content:
                index[symbol].add(page)
    return index


def _load_surface_index_pages(wiki_dir: Path) -> list[dict] | None:
    path = wiki_dir / SURFACE_INDEX_FILENAME
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if payload.get("schema_version") != WIKI_SURFACE_INDEX_SCHEMA_VERSION:
        return None
    pages = payload.get("pages")
    return pages if isinstance(pages, list) else None


def _build_surface_index_pages(
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    module_page_map: dict[str, str],
    entity_page_map: dict[tuple[str, str], str],
    entity_occurrence_page_map: dict[tuple[str, str, int], str],
    source_snapshot: SourceSnapshot | None = None,
    include_plugins: bool = True,
) -> list[dict]:
    console_scripts = read_console_scripts(
        src_dir,
        source_snapshot=source_snapshot,
    )
    entry_points = get_entry_points(
        inventory,
        console_scripts=console_scripts,
        root=src_dir,
        fallback_root=runtime_plugin_fallback_root(
            src_dir,
            source_selection_configured=(
                source_snapshot is not None
                and source_snapshot.source_selection_policy is not None
            ),
        ),
        include_plugins=include_plugins
        and runtime_project_plugins_enabled(
            src_dir,
            source_selection_configured=(
                source_snapshot is not None
                and source_snapshot.source_selection_policy is not None
            ),
        ),
    )
    payload = build_surface_index(
        wiki_dir,
        inventory,
        src_dir=src_dir,
        entity_page_cache=entity_page_map,
        entity_occurrence_page_cache=entity_occurrence_page_map,
        module_page_map=module_page_map,
        entry_points=entry_points,
    )
    pages = payload.get("pages", [])
    return pages if isinstance(pages, list) else []


def _surface_index_pages(
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    module_page_map: dict[str, str],
    entity_page_map: dict[tuple[str, str], str],
    entity_occurrence_page_map: dict[tuple[str, str, int], str],
    source_snapshot: SourceSnapshot | None = None,
    include_plugins: bool = True,
) -> list[dict]:
    pages = _load_surface_index_pages(wiki_dir)
    if pages is not None:
        return pages
    return _build_surface_index_pages(
        wiki_dir,
        inventory,
        src_dir,
        module_page_map,
        entity_page_map,
        entity_occurrence_page_map,
        source_snapshot,
        include_plugins,
    )


def _flow_pages_by_source(
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    module_page_map: dict[str, str],
    entity_page_map: dict[tuple[str, str], str],
    entity_occurrence_page_map: dict[tuple[str, str, int], str],
    source_snapshot: SourceSnapshot | None = None,
) -> dict[str, list[str]]:
    pages_by_source: dict[str, list[str]] = {}
    for page in _surface_index_pages(
        wiki_dir,
        inventory,
        src_dir,
        module_page_map,
        entity_page_map,
        entity_occurrence_page_map,
        source_snapshot,
    ):
        if page.get("kind") != PageKind.FLOWS.value:
            continue
        source_path = page.get("source_path")
        canonical_path = page.get("canonical_path")
        if not isinstance(source_path, str) or not isinstance(canonical_path, str):
            continue
        normalized_source = source_path.replace("\\", "/")
        normalized_page = canonical_path.replace("\\", "/")
        if not normalized_source or not normalized_page:
            continue
        if not (wiki_dir / normalized_page).exists():
            continue
        pages_by_source.setdefault(normalized_source, []).append(normalized_page)
    return {
        source: sorted(set(pages), key=lambda value: (value.casefold(), value))
        for source, pages in pages_by_source.items()
    }


def _related_pages_for_source(
    path: str,
    inventory: dict,
    module_page_map: dict[str, str],
    entity_page_map: dict[tuple[str, str], str],
    entity_occurrence_page_map: dict[tuple[str, str, int], str],
    flow_pages_by_source: dict[str, list[str]],
) -> list[str]:
    if path not in inventory:
        return []
    pages = [f"modules/{module_page_map[path]}.md"]
    seen_names: dict[str, int] = {}
    for cls in inventory[path].get("classes", []):
        name = cls["name"]
        seen_names[name] = seen_names.get(name, 0) + 1
        entity_page = entity_occurrence_page_map.get(
            (name, path, seen_names[name]),
            entity_page_map[(name, path)],
        )
        pages.append(f"entities/{entity_page}.md")
    pages.extend(flow_pages_by_source.get(path, []))
    return pages


def _preflight_review_source_selection(
    src_dir: str,
    wiki_dir: Path,
    source_selection: str | Path | None,
) -> SourceSnapshot:
    policy = resolve_source_selection(src_dir, source_selection)
    try:
        manifest = SyncManifest.load(wiki_dir)
    except FileNotFoundError:
        generation_inputs = (
            {}
            if wiki_dir.is_dir() and next(wiki_dir.iterdir(), None) is not None
            else None
        )
    else:
        generation_inputs = manifest.generation_inputs
    selection_inputs = capture_source_selection_inputs(
        src_dir,
        source_selection=source_selection,
        selection_policy=policy,
    )
    validate_persisted_source_selection_identity(
        generation_inputs,
        None if policy is None else policy.identity,
        operation="review",
        live_selection_inputs=selection_inputs,
    )
    source_snapshot = build_source_snapshot(
        src_dir,
        source_selection=source_selection,
        selection_policy=policy,
        expected_selection_inputs=selection_inputs,
    )
    return source_snapshot


def build_analysis(
    diff_text: str,
    *,
    src_dir: str = ".",
    wiki_dir: str = DEFAULT_WIKI_DIR,
    source_selection: str | Path | None = None,
    changes: dict | None = None,
    include_plugins: bool = True,
    helper_cache_dir: str | None = None,
) -> ReviewAnalysis:
    wiki_path = Path(wiki_dir)
    source_snapshot = _preflight_review_source_selection(
        src_dir,
        wiki_path,
        source_selection,
    )
    patch_changed = _changed_paths(diff_text)
    diff_text = filter_source_diff(
        diff_text,
        source_snapshot.source_selection_policy,
        retained_roots=(wiki_path.as_posix(),),
        source_snapshot=source_snapshot,
    )
    selected = select_changes(
        src_dir,
        changes
        or {
            "mode": "paths",
            "paths": source_relative_paths(patch_changed, src_dir),
        },
        snapshot=source_snapshot,
    )
    changed = selected["paths"]
    try:
        repository_root = Path(_git(src_dir, "rev-parse", "--show-toplevel").strip())
    except ValueError:
        repository_root = Path(src_dir).resolve()
    wiki_changed = set()
    for path in patch_changed:
        try:
            wiki_changed.add(
                (repository_root / path).relative_to(wiki_path.resolve()).as_posix()
            )
        except ValueError:
            continue

    extraction_options = {}
    if not include_plugins:
        extraction_options["include_plugins"] = False
    if helper_cache_dir is not None:
        extraction_options["helper_cache_dir"] = helper_cache_dir
    inventory_result = get_inventory_result(
        src_dir,
        deep=True,
        source_snapshot=source_snapshot,
        **extraction_options,
    )
    if inventory_result.failed:
        raise ValueError("Source extraction failed while computing review impact")
    inventory = inventory_result.inventory
    module_page_map = build_module_page_map(inventory)
    entity_page_map = build_entity_page_map(inventory)
    entity_occurrence_page_map = build_entity_occurrence_page_map(
        inventory, module_page_map
    )
    page_map = affected_page_map(
        changed,
        inventory,
        _surface_index_pages(
            wiki_path,
            inventory,
            src_dir,
            module_page_map,
            entity_page_map,
            entity_occurrence_page_map,
            source_snapshot,
            include_plugins,
        ),
    )
    symbol_pages = _symbol_reference_pages(wiki_path)
    imports_by_file = {}
    for path, imports in _added_imports_by_file(diff_text).items():
        relative = source_relative_paths([path], src_dir)
        if relative and relative[0] in changed:
            imports_by_file[relative[0]] = imports
    module_candidates: dict[str, list[str]] = {}
    for path in inventory:
        module_candidates.setdefault(Path(path).stem, []).append(path)
    known_modules = {
        stem: paths[0] for stem, paths in module_candidates.items() if len(paths) == 1
    }

    findings: list[ReviewFinding] = []

    for path in changed:
        normalized = path.replace("\\", "/")
        if normalized.startswith(f"{wiki_path.as_posix()}/"):
            continue
        if not normalized.endswith(_SOURCE_EXTS):
            continue

        pages = page_map.get(normalized, [])
        if not pages:
            findings.append(
                ReviewFinding(
                    severity="warning",
                    source_path=normalized,
                    wiki_pages=[],
                    reason="Changed source file has no module or entity wiki coverage.",
                    suggested_follow_up="Run `llm-wiki sync` or add the missing module/entity page before relying on the wiki.",
                )
            )
            continue

        missing_pages = [page for page in pages if not (wiki_path / page).exists()]
        if missing_pages:
            findings.append(
                ReviewFinding(
                    severity="warning",
                    source_path=normalized,
                    wiki_pages=missing_pages,
                    reason="Changed source file maps to missing wiki page(s).",
                    suggested_follow_up="Generate or restore the listed wiki page(s).",
                )
            )

        existing_pages = [page for page in pages if (wiki_path / page).exists()]
        changed_related_pages = [
            page for page in existing_pages if page in wiki_changed
        ]
        if existing_pages and not changed_related_pages:
            findings.append(
                ReviewFinding(
                    severity="info",
                    source_path=normalized,
                    wiki_pages=existing_pages,
                    reason="Documented source changed, but related wiki page(s) were not changed in this patch.",
                    suggested_follow_up="Confirm these pages are still accurate or update them with the code change.",
                )
            )

    imports_to_review: list[tuple[str, str, list[str]]] = []
    workflow_symbols: set[str] = set()
    for path, imported_modules in imports_by_file.items():
        normalized = path.replace("\\", "/")
        if normalized.startswith(f"{wiki_path.as_posix()}/") or not normalized.endswith(
            _SOURCE_EXTS
        ):
            continue
        source_stem = Path(normalized).stem
        review_imports: list[str] = []
        for imported in sorted(set(imported_modules)):
            imported_path = known_modules.get(imported)
            if not imported_path or Path(imported_path).stem == source_stem:
                continue
            review_imports.append(imported)
        if review_imports:
            imports_to_review.append((normalized, source_stem, review_imports))
            workflow_symbols.add(source_stem)
            workflow_symbols.update(review_imports)

    workflow_symbol_index = _workflow_symbol_index(symbol_pages, workflow_symbols)
    for normalized, source_stem, imported_modules in imports_to_review:
        source_workflows = workflow_symbol_index[source_stem]
        for imported in imported_modules:
            represented = not source_workflows.isdisjoint(
                workflow_symbol_index[imported]
            )
            if not represented:
                findings.append(
                    ReviewFinding(
                        severity="info",
                        source_path=normalized,
                        wiki_pages=sorted(source_workflows),
                        reason=f"New cross-module import `{imported}` is not represented by a workflow, flow, or architecture page.",
                        suggested_follow_up="Add or update a workflow, flow, or architecture page if this import creates a meaningful cross-module relationship.",
                    )
                )

    infra_changed = [path for path in changed if _is_dependency_path(path)]
    infra_wiki_changed = any(
        path.startswith("infrastructure/") or path in _ARCHITECTURE_PAGE_PATHS
        for path in wiki_changed
    )
    if infra_changed and not infra_wiki_changed:
        for path in infra_changed:
            findings.append(
                ReviewFinding(
                    severity="warning",
                    source_path=path,
                    wiki_pages=sorted(
                        page.relative_path
                        for page in collect_wiki_pages(wiki_path)
                        if page.kind
                        in {
                            PageKind.INFRASTRUCTURE,
                            PageKind.DEPENDENCIES,
                            PageKind.LOAD_ORDER,
                        }
                    ),
                    reason="Dependency or infrastructure file changed without infrastructure or architecture wiki updates.",
                    suggested_follow_up="Update infrastructure notes or dependency architecture pages for compatibility, dependency, or runtime changes.",
                )
            )

    findings.sort(
        key=lambda finding: (
            finding.source_path,
            finding.severity,
            finding.reason,
            finding.wiki_pages,
        )
    )
    return ReviewAnalysis(findings, selected, page_map, inventory, source_snapshot)


def build_findings(diff_text: str, **kwargs) -> list[ReviewFinding]:
    return build_analysis(diff_text, **kwargs).findings
