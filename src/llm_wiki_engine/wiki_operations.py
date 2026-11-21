"""Bootstrap, sync and lint a wiki through a domain pack alone.

These use cases need nothing but the active
:class:`~.pack_interfaces.DomainPack`: its classifier picks the sources, its
extractors (in-process ``"module:attribute"`` entry points) read them, and its
page namer and renderer name and write the pages. Pages start from a generic
built-in Markdown that the renderer may adjust. Each page's ``Description``
section is reviewed text: sync keeps what people wrote there.

A wiki written here holds module and entity pages, ``index.md``, ``log.md``
and the sync manifest. Applications with richer analysis (call graphs,
infrastructure, knowledge bundles) run their own use cases instead.
"""

from __future__ import annotations

import hashlib
import importlib
import os
import tempfile
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePath
from typing import Any

from .gitignore import build_gitignore_matcher
from .host import current_host, emit
from .markdown_sections import replace_section_body, section_body
from .pack_interfaces import DomainPack, EntityPageRequest, ModulePageRequest, active_pack
from .path_policy import EXCLUDED_DIRS
from .sync_manifest import MANIFEST_FILENAME, SyncManifest, SyncManifestError

INDEX_PAGE = "index.md"
LOG_PAGE = "log.md"
_PLACEHOLDER_PREFIX = "_Auto-generated from "
_REVIEWED_SECTION = "Description"


class WikiOperationError(Exception):
    """A wiki use case cannot complete; the message says why."""


@dataclass(frozen=True)
class BootstrapRequest:
    """Create a wiki at ``wiki_root`` from the sources under ``source_root``."""

    source_root: str | os.PathLike[str]
    wiki_root: str | os.PathLike[str]


@dataclass(frozen=True)
class SyncRequest:
    """Bring the wiki at ``wiki_root`` up to date with ``source_root``."""

    source_root: str | os.PathLike[str]
    wiki_root: str | os.PathLike[str]


@dataclass(frozen=True)
class LintRequest:
    """Check the wiki at ``wiki_root`` against ``source_root``."""

    source_root: str | os.PathLike[str]
    wiki_root: str | os.PathLike[str]


@dataclass(frozen=True)
class BootstrapResult:
    sources: int
    pages: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"sources": self.sources, "pages": list(self.pages)}


@dataclass(frozen=True)
class SyncResult:
    status: str
    written: tuple[str, ...] = ()
    removed: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"status": self.status, "written": list(self.written), "removed": list(self.removed)}


@dataclass(frozen=True)
class LintIssue:
    category: str
    page: str
    message: str


@dataclass(frozen=True)
class LintReport:
    issues: tuple[LintIssue, ...] = field(default_factory=tuple)

    @property
    def passed(self) -> bool:
        return not self.issues

    @property
    def issue_count(self) -> int:
        return len(self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [
                {"category": issue.category, "page": issue.page, "message": issue.message}
                for issue in self.issues
            ],
        }


# ── Sources ────────────────────────────────────────────────────────────


def _pack() -> DomainPack:
    pack = active_pack()
    if pack is None:
        raise WikiOperationError("no domain pack is active; run inside an engine operation")
    return pack


def _roots(request: Any) -> tuple[Path, Path]:
    source = Path(request.source_root)
    wiki = Path(request.wiki_root)
    if not source.is_dir():
        raise WikiOperationError(f"source root {source} is not a directory")
    return source, wiki


def _classified_sources(source: Path, wiki: Path, pack: DomainPack) -> dict[str, str]:
    """Return ``{relative path: source kind}`` for every source the pack accepts."""
    ignored = build_gitignore_matcher(source)
    wiki_resolved = wiki.resolve()
    found: dict[str, str] = {}
    for root, directories, files in os.walk(source, followlinks=False):
        current = Path(root)
        directories[:] = sorted(
            name for name in directories
            if not name.startswith(".") and name not in EXCLUDED_DIRS
            and not (current / name).is_symlink()
            and (current / name).resolve() != wiki_resolved
        )
        for name in sorted(files):
            path = current / name
            if path.is_symlink() or name.startswith("."):
                continue
            relative = path.relative_to(source).as_posix()
            if ignored.is_ignored(relative):
                continue
            kind, exclusion = pack.classifier.classify(PurePath(relative), frozenset())
            if kind is not None and exclusion is None:
                found[relative] = kind
    return found


def _extract(source: Path, sources: Mapping[str, str], pack: DomainPack) -> dict[str, dict]:
    by_kind: dict[str, list[str]] = {}
    for relative, kind in sources.items():
        by_kind.setdefault(kind, []).append(relative)
    inventory: dict[str, dict] = {}
    for kind, files in sorted(by_kind.items()):
        entry_point = pack.extractors.get(kind)
        if entry_point is None:
            raise WikiOperationError(f"the pack has no extractor for source kind {kind!r}")
        module_name, _, attribute = entry_point.partition(":")
        extractor = getattr(importlib.import_module(module_name), attribute)
        if isinstance(extractor, type):
            extractor = extractor()
        extracted = extractor.extract(os.fspath(source), only_files=sorted(files))
        if not isinstance(extracted, Mapping):
            raise WikiOperationError(f"extractor {entry_point} must return an inventory mapping")
        for relative in files:
            data = extracted.get(relative)
            if not isinstance(data, Mapping):
                raise WikiOperationError(f"extractor {entry_point} returned nothing for {relative}")
            inventory[relative] = dict(data)
    return inventory


def _file_hash(path: Path) -> str:
    # The manifest's canonical ``sha256:<hex>`` form.
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _content_hashes(source: Path, inventory: Mapping[str, Any]) -> dict[str, str]:
    return {relative: _file_hash(source / relative) for relative in inventory}


# ── Pages ──────────────────────────────────────────────────────────────


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _module_markdown(page: str, source_path: str, data: Mapping[str, Any],
                     entity_links: Mapping[str, str]) -> str:
    lines = [
        f"# {page}", "", f"**Path:** `{source_path}`", "",
        f"## {_REVIEWED_SECTION}", "", f"{_PLACEHOLDER_PREFIX}`{source_path}`._", "",
    ]
    classes = [item for item in data.get("classes", ()) if isinstance(item, Mapping)]
    if classes:
        lines += ["## Classes", "", "| Class | Line | Bases | Description |",
                  "|-------|------|-------|-------------|"]
        for item in classes:
            name = str(item.get("name", ""))
            target = entity_links.get(name)
            label = f"[{_cell(name)}](../entities/{target}.md)" if target else _cell(name)
            bases = ", ".join(str(base) for base in item.get("bases", ()) or ()) or "—"
            lines.append(f"| {label} | {item.get('line', '—')} | {_cell(bases)} | — |")
        lines.append("")
    functions = [item for item in data.get("functions", ()) if isinstance(item, Mapping)]
    if functions:
        lines += ["## Functions", "", "| Function | Line | Description |",
                  "|----------|------|-------------|"]
        for item in functions:
            lines.append(f"| `{_cell(item.get('name', ''))}` | {item.get('line', '—')} | — |")
        lines.append("")
    return "\n".join(lines)


def _entity_markdown(entity: Mapping[str, Any], source_path: str, module_page: str | None) -> str:
    name = str(entity.get("name", ""))
    bases = ", ".join(str(base) for base in entity.get("bases", ()) or ()) or "—"
    module = f"[{module_page}](../modules/{module_page}.md)" if module_page else "—"
    lines = [
        f"# {name}", "", f"**Location:** `{source_path}:{entity.get('line', '?')}`",
        f"**Kind:** {str(entity.get('kind', 'class')).capitalize()}", f"**Bases:** {bases}",
        f"**Module:** {module}", "",
        f"## {_REVIEWED_SECTION}", "", f"{_PLACEHOLDER_PREFIX}`{name}` in `{source_path}`._", "",
    ]
    methods = [item for item in entity.get("methods", ()) if isinstance(item, Mapping)]
    lines += ["## Methods", ""]
    if methods:
        lines += ["| Method | Line | Description |", "|--------|------|-------------|"]
        lines += [f"| `{_cell(item.get('name', ''))}` | {item.get('line', '—')} | — |" for item in methods]
    else:
        lines.append("*No declared methods.*")
    lines.append("")
    return "\n".join(lines)


def _render(inventory: Mapping[str, dict], pack: DomainPack) -> tuple[dict[str, str], dict, dict]:
    """Return ``{wiki-relative page path: Markdown}``, the module and entity page maps."""
    module_pages = pack.page_namer.module_pages(inventory)
    entity_pages = pack.page_namer.entity_pages(inventory, module_pages)
    pages: dict[str, str] = {}
    for source_path, data in sorted(inventory.items()):
        page = module_pages[source_path]
        seen: dict[str, int] = {}
        links: dict[str, str] = {}
        for entity in data.get("classes", ()):
            name = str(entity.get("name", ""))
            seen[name] = seen.get(name, 0) + 1
            target = entity_pages.get((name, source_path, seen[name]))
            if target is not None:
                links.setdefault(name, target)
                pages[f"entities/{target}.md"] = _rendered_entity(
                    pack, entity, source_path, page, module_pages,
                )
        builtin = _module_markdown(page, source_path, data, links)
        request = ModulePageRequest(
            source_path=source_path, file_data=data, entity_pages=links,
            module_pages=module_pages, entity_occurrence_pages=entity_pages,
            module_dependencies=None, diagram_style=None, _builtin=lambda builtin=builtin: builtin,
        )
        pages[f"modules/{page}.md"] = _text(pack.page_renderer.render_module(request))
    return pages, module_pages, entity_pages


def _rendered_entity(pack: DomainPack, entity: Mapping[str, Any], source_path: str,
                     module_page: str, module_pages: Mapping[str, str]) -> str:
    builtin = _entity_markdown(entity, source_path, module_page)
    request = EntityPageRequest(
        entity=entity, source_path=source_path, module_page=module_page,
        relationships={}, relationship_summary={}, module_pages=module_pages,
        diagram_style=None, _builtin=lambda: builtin,
    )
    return _text(pack.page_renderer.render_entity(request))


def _text(markdown: object) -> str:
    if not isinstance(markdown, str):
        raise WikiOperationError("the page renderer must return Markdown text")
    return markdown if markdown.endswith("\n") else markdown + "\n"


def _index_markdown(pages: Iterable[str]) -> str:
    modules = sorted(page for page in pages if page.startswith("modules/"))
    entities = sorted(page for page in pages if page.startswith("entities/"))
    lines = ["# Wiki Index", ""]
    for heading, group in (("Modules", modules), ("Entities", entities)):
        lines += [f"## {heading}", ""]
        lines += [f"- [{PurePath(page).stem}]({page})" for page in group] or ["*None.*"]
        lines.append("")
    return "\n".join(lines)


def _keep_reviewed_text(new: str, old: str | None) -> str:
    if old is None:
        return new
    body = section_body(old, _REVIEWED_SECTION)
    if not body or body.startswith(_PLACEHOLDER_PREFIX):
        return new
    return replace_section_body(new, _REVIEWED_SECTION, body)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".llm-wiki-", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(text)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _append_log(wiki: Path, line: str) -> None:
    path = wiki / LOG_PAGE
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Wiki Log\n"
    heading = f"## {current_host().today().isoformat()}"
    text = existing.rstrip("\n") + "\n"
    if heading not in text.splitlines():
        text += f"\n{heading}\n\n"
    _write(path, text + f"- {line}\n")


def _manifest(inventory, source: Path, module_pages, entity_pages, hashes) -> SyncManifest:
    return SyncManifest.build_from_inventory(
        inventory, os.fspath(source), {}, dict(module_pages),
        entity_occurrence_page_cache=dict(entity_pages), source_content_hashes=hashes,
    )


# ── Use cases ──────────────────────────────────────────────────────────


def bootstrap(request: BootstrapRequest) -> BootstrapResult:
    """Write a new wiki; refuses a wiki that already has a manifest."""
    pack = _pack()
    source, wiki = _roots(request)
    if (wiki / MANIFEST_FILENAME).exists():
        raise WikiOperationError(f"{wiki} already holds a wiki; sync it instead")
    inventory = _extract(source, _classified_sources(source, wiki, pack), pack)
    pages, module_pages, entity_pages = _render(inventory, pack)
    for relative, markdown in sorted(pages.items()):
        _write(wiki / relative, markdown)
    _write(wiki / INDEX_PAGE, _index_markdown(pages))
    _manifest(inventory, source, module_pages, entity_pages, _content_hashes(source, inventory)).save(wiki)
    _append_log(wiki, f"Bootstrap: {len(pages)} pages from {len(inventory)} sources.")
    emit(f"Wrote {len(pages)} pages from {len(inventory)} sources.")
    return BootstrapResult(len(inventory), tuple(sorted(pages)))


def _owned_pages(manifest: SyncManifest) -> set[str]:
    return set(manifest.page_source_mappings)


def sync(request: SyncRequest) -> SyncResult:
    """Rewrite pages whose sources changed, keep reviewed text, retire removed pages."""
    pack = _pack()
    source, wiki = _roots(request)
    try:
        previous = SyncManifest.load(wiki)
    except FileNotFoundError as exc:
        raise WikiOperationError(f"{wiki} has no wiki to sync; bootstrap it first") from exc
    except SyncManifestError as exc:
        raise WikiOperationError(f"{wiki} has an unreadable sync manifest: {exc}") from exc
    inventory = _extract(source, _classified_sources(source, wiki, pack), pack)
    pages, module_pages, entity_pages = _render(inventory, pack)
    written: list[str] = []
    for relative, markdown in sorted(pages.items()):
        path = wiki / relative
        old = path.read_text(encoding="utf-8") if path.exists() else None
        text = _keep_reviewed_text(markdown, old)
        if text != old:
            _write(path, text)
            written.append(relative)
    removed = sorted(_owned_pages(previous) - set(pages))
    for relative in removed:
        (wiki / relative).unlink(missing_ok=True)
    index = _index_markdown(pages)
    index_path = wiki / INDEX_PAGE
    if not index_path.exists() or index_path.read_text(encoding="utf-8") != index:
        _write(index_path, index)
    manifest = _manifest(inventory, source, module_pages, entity_pages, _content_hashes(source, inventory))
    if not written and not removed and manifest.sources == previous.sources:
        emit("Wiki is up to date.")
        return SyncResult("up-to-date")
    manifest.save(wiki)
    _append_log(wiki, f"Sync: {len(written)} pages written, {len(removed)} removed.")
    emit(f"Wrote {len(written)} pages, removed {len(removed)}.")
    return SyncResult("synced", tuple(written), tuple(removed))


def lint(request: LintRequest) -> LintReport:
    """Report missing, unowned, stale and broken-link pages; never writes."""
    pack = _pack()
    source, wiki = _roots(request)
    issues: list[LintIssue] = []
    try:
        manifest = SyncManifest.load(wiki)
    except (FileNotFoundError, SyncManifestError) as exc:
        return LintReport((LintIssue("manifest", MANIFEST_FILENAME, f"no usable sync manifest: {exc}"),))
    owned = _owned_pages(manifest)
    on_disk = {
        path.relative_to(wiki).as_posix()
        for folder in ("modules", "entities") if (wiki / folder).is_dir()
        for path in (wiki / folder).glob("*.md")
    }
    issues += [LintIssue("missing-page", page, "the manifest names a page that does not exist")
               for page in sorted(owned - on_disk)]
    issues += [LintIssue("unowned-page", page, "no source in the manifest owns this page")
               for page in sorted(on_disk - owned)]
    current = _classified_sources(source, wiki, pack)
    for relative in sorted(set(manifest.sources) - set(current)):
        issues.append(LintIssue("stale-source", relative, "the source was removed; sync the wiki"))
    for relative in sorted(set(current) - set(manifest.sources)):
        issues.append(LintIssue("stale-source", relative, "a new source is not in the wiki; sync it"))
    for relative in sorted(set(current) & set(manifest.sources)):
        recorded = manifest.sources[relative].get("hash")
        if recorded and recorded != _file_hash(source / relative):
            issues.append(LintIssue("stale-source", relative, "the source changed; sync the wiki"))
    for page in sorted(on_disk | ({INDEX_PAGE} if (wiki / INDEX_PAGE).exists() else set())):
        issues += _broken_links(wiki, page)
    return LintReport(tuple(issues))


def _broken_links(wiki: Path, page: str) -> list[LintIssue]:
    import re

    text = (wiki / page).read_text(encoding="utf-8")
    found = []
    for target in re.findall(r"\]\(([^)#\s]+\.md)(?:#[^)]*)?\)", text):
        if "://" in target:
            continue
        resolved = (wiki / page).parent / target
        if not resolved.exists():
            found.append(LintIssue("broken-link", page, f"links to missing page {target}"))
    return found


__all__ = [
    "BootstrapRequest",
    "BootstrapResult",
    "LintIssue",
    "LintReport",
    "LintRequest",
    "SyncRequest",
    "SyncResult",
    "WikiOperationError",
    "bootstrap",
    "lint",
    "sync",
]
