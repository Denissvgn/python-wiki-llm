from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from ..config import DEFAULT_WIKI_DIR, validate_path
from .bootstrap_cmd import (
    build_entity_occurrence_page_map,
    build_entity_page_map,
    build_module_page_map,
)
from .extract_cmd import get_inventory
from ..services.entrypoints import get_entry_points, read_console_scripts
from ..services.wiki_surface import PageKind, collect_wiki_pages
from ..services.wiki_surface_index import (
    SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
    build_surface_index,
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
_ARCHITECTURE_PAGE_PATHS = {"dependencies.md", "load-order.md"}
_SYMBOL_REFERENCE_KINDS = {
    PageKind.WORKFLOWS,
    PageKind.FLOWS,
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


def _read_patch(args) -> str:
    patch = getattr(args, "patch", None)
    if patch:
        if patch == "-":
            return sys.stdin.read()
        validate_path(patch, "--patch")
        return Path(patch).read_text(encoding="utf-8")

    base = getattr(args, "base", None)
    head = getattr(args, "head", None)
    if base or head:
        if not base or not head:
            print(
                "Error: --base and --head must be provided together.", file=sys.stderr
            )
            sys.exit(1)
        cmd = ["git", "diff", f"{base}..{head}"]
    else:
        cmd = ["git", "diff"]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, timeout=30
        )
        return result.stdout
    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
    ) as exc:
        print(f"Error: failed to read git diff: {exc}", file=sys.stderr)
        sys.exit(1)


def _changed_paths(diff_text: str) -> list[str]:
    paths: list[str] = []
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            path = line[6:]
        elif line.startswith("rename to "):
            path = line.split(" ", 2)[-1]
        else:
            continue
        if path != "/dev/null" and path not in paths:
            paths.append(path)
    return paths


def _added_imports_by_file(diff_text: str) -> dict[str, list[str]]:
    current: str | None = None
    imports: dict[str, list[str]] = {}
    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
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
) -> list[dict]:
    console_scripts = read_console_scripts(src_dir)
    entry_points = get_entry_points(
        inventory,
        console_scripts=console_scripts,
        root=src_dir,
        fallback_root=Path.cwd(),
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
    )


def _flow_pages_by_source(
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    module_page_map: dict[str, str],
    entity_page_map: dict[tuple[str, str], str],
    entity_occurrence_page_map: dict[tuple[str, str, int], str],
) -> dict[str, list[str]]:
    pages_by_source: dict[str, list[str]] = {}
    for page in _surface_index_pages(
        wiki_dir,
        inventory,
        src_dir,
        module_page_map,
        entity_page_map,
        entity_occurrence_page_map,
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


def build_findings(
    diff_text: str, *, src_dir: str = ".", wiki_dir: str = DEFAULT_WIKI_DIR
) -> list[ReviewFinding]:
    wiki_path = Path(wiki_dir)
    changed = _changed_paths(diff_text)
    changed_set = {path.replace("\\", "/") for path in changed}
    wiki_changed = {
        path[len(f"{wiki_path.as_posix()}/") :]
        for path in changed_set
        if path.startswith(f"{wiki_path.as_posix()}/")
    }

    inventory = get_inventory(src_dir, deep=True)
    module_page_map = build_module_page_map(inventory)
    entity_page_map = build_entity_page_map(inventory)
    entity_occurrence_page_map = build_entity_occurrence_page_map(
        inventory, module_page_map
    )
    flow_pages = _flow_pages_by_source(
        wiki_path,
        inventory,
        src_dir,
        module_page_map,
        entity_page_map,
        entity_occurrence_page_map,
    )
    symbol_pages = _symbol_reference_pages(wiki_path)
    imports_by_file = _added_imports_by_file(diff_text)
    known_modules = {Path(path).stem: path for path in inventory}
    reference_pages = sorted(symbol_pages.keys())

    findings: list[ReviewFinding] = []

    for path in changed:
        normalized = path.replace("\\", "/")
        if normalized.startswith(f"{wiki_path.as_posix()}/"):
            continue
        if not normalized.endswith(_SOURCE_EXTS):
            continue

        pages = _related_pages_for_source(
            normalized,
            inventory,
            module_page_map,
            entity_page_map,
            entity_occurrence_page_map,
            flow_pages,
        )
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
                        wiki_pages=reference_pages,
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
                    wiki_pages=["infrastructure/", "dependencies.md", "load-order.md"],
                    reason="Dependency or infrastructure file changed without infrastructure or architecture wiki updates.",
                    suggested_follow_up="Update infrastructure notes or dependency architecture pages for compatibility, dependency, or runtime changes.",
                )
            )

    return findings


def render_markdown(findings: list[ReviewFinding]) -> str:
    lines = ["# LLM Wiki Review", ""]
    if not findings:
        lines.append("No wiki-aware review findings.")
        return "\n".join(lines) + "\n"
    for finding in findings:
        pages = ", ".join(f"`{page}`" for page in finding.wiki_pages) or "none"
        lines.extend(
            [
                f"## {finding.severity.upper()}: {finding.source_path}",
                "",
                f"- Related wiki pages: {pages}",
                f"- Reason: {finding.reason}",
                f"- Suggested follow-up: {finding.suggested_follow_up}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def render_json(findings: list[ReviewFinding]) -> str:
    return (
        json.dumps(
            {"ok": True, "findings": [asdict(finding) for finding in findings]},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def run(args) -> None:
    src_dir: str = getattr(args, "src_dir", ".")
    wiki_dir: str = getattr(args, "wiki_dir", DEFAULT_WIKI_DIR)
    output_format: str = getattr(args, "format", "markdown")
    validate_path(src_dir, "--src-dir")
    validate_path(wiki_dir, "--wiki-dir")

    diff_text = _read_patch(args)
    findings = build_findings(diff_text, src_dir=src_dir, wiki_dir=wiki_dir)
    if output_format == "json":
        print(render_json(findings), end="")
    else:
        print(render_markdown(findings), end="")
