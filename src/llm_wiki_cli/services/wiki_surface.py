"""Canonical wiki page surface registry.

This module only describes and collects pages that already exist under a wiki
directory. It intentionally avoids source inventory and command-module imports.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, Union
from urllib.parse import quote


RESOURCE_SCHEME = "llm-wiki"
_PAGE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


class WikiSurfaceError(ValueError):
    """Raised for invalid wiki surface lookups."""


class PageKind(str, Enum):
    INDEX = "index"
    LOG = "log"
    ENTITIES = "entities"
    MODULES = "modules"
    WORKFLOWS = "workflows"
    GUIDES = "guides"
    FLOWS = "flows"
    INFRASTRUCTURE = "infrastructure"
    DEPENDENCIES = "dependencies"
    LOAD_ORDER = "load-order"


class SurfaceRole(str, Enum):
    GENERATED = "generated"
    SEMANTIC = "semantic"
    MIXED = "mixed"


@dataclass(frozen=True)
class WikiSurfaceKind:
    kind: PageKind
    label: str
    path_pattern: str
    mcp_uri_kind: str
    obsidian_mirror_dir: Optional[str]
    role: SurfaceRole

    @property
    def requires_page_id(self) -> bool:
        return "{page_id}" in self.path_pattern

    @property
    def directory(self) -> Optional[str]:
        if not self.requires_page_id:
            return None
        return self.path_pattern.split("/", 1)[0]


@dataclass(frozen=True)
class WikiSurfacePage:
    kind: PageKind
    page_id: str
    label: str
    path: Path
    relative_path: str
    mcp_uri: str
    obsidian_mirror_dir: Optional[str]
    role: SurfaceRole


_PAGE_KINDS = (
    WikiSurfaceKind(
        kind=PageKind.INDEX,
        label="Index",
        path_pattern="index.md",
        mcp_uri_kind="index",
        obsidian_mirror_dir=None,
        role=SurfaceRole.MIXED,
    ),
    WikiSurfaceKind(
        kind=PageKind.LOG,
        label="Log",
        path_pattern="log.md",
        mcp_uri_kind="log",
        obsidian_mirror_dir=None,
        role=SurfaceRole.GENERATED,
    ),
    WikiSurfaceKind(
        kind=PageKind.ENTITIES,
        label="Entities",
        path_pattern="entities/{page_id}.md",
        mcp_uri_kind="entities",
        obsidian_mirror_dir="Entities",
        role=SurfaceRole.SEMANTIC,
    ),
    WikiSurfaceKind(
        kind=PageKind.MODULES,
        label="Modules",
        path_pattern="modules/{page_id}.md",
        mcp_uri_kind="modules",
        obsidian_mirror_dir="Modules",
        role=SurfaceRole.SEMANTIC,
    ),
    WikiSurfaceKind(
        kind=PageKind.WORKFLOWS,
        label="Workflows",
        path_pattern="workflows/{page_id}.md",
        mcp_uri_kind="workflows",
        obsidian_mirror_dir="Workflows",
        role=SurfaceRole.MIXED,
    ),
    WikiSurfaceKind(
        kind=PageKind.GUIDES,
        label="Guides",
        path_pattern="guides/{page_id}.md",
        mcp_uri_kind="guides",
        obsidian_mirror_dir="Guides",
        role=SurfaceRole.SEMANTIC,
    ),
    WikiSurfaceKind(
        kind=PageKind.FLOWS,
        label="User flows",
        path_pattern="flows/{page_id}.md",
        mcp_uri_kind="flows",
        obsidian_mirror_dir="Flows",
        role=SurfaceRole.MIXED,
    ),
    WikiSurfaceKind(
        kind=PageKind.INFRASTRUCTURE,
        label="Infrastructure",
        path_pattern="infrastructure/{page_id}.md",
        mcp_uri_kind="infrastructure",
        obsidian_mirror_dir="Infrastructure",
        role=SurfaceRole.MIXED,
    ),
    WikiSurfaceKind(
        kind=PageKind.DEPENDENCIES,
        label="Dependencies",
        path_pattern="dependencies.md",
        mcp_uri_kind="dependencies",
        obsidian_mirror_dir=None,
        role=SurfaceRole.MIXED,
    ),
    WikiSurfaceKind(
        kind=PageKind.LOAD_ORDER,
        label="Load order",
        path_pattern="load-order.md",
        mcp_uri_kind="load-order",
        obsidian_mirror_dir=None,
        role=SurfaceRole.MIXED,
    ),
)

_KINDS_BY_KIND = {entry.kind: entry for entry in _PAGE_KINDS}


def iter_page_kinds() -> tuple[WikiSurfaceKind, ...]:
    """Return all canonical page kinds in display/collection order."""
    return _PAGE_KINDS


def iter_root_pages() -> tuple[WikiSurfaceKind, ...]:
    """Return top-level page kinds in canonical order."""
    return tuple(entry for entry in _PAGE_KINDS if not entry.requires_page_id)


def iter_directory_kinds() -> tuple[WikiSurfaceKind, ...]:
    """Return directory-backed page kinds in canonical order."""
    return tuple(entry for entry in _PAGE_KINDS if entry.requires_page_id)


def is_safe_page_id(page_id: str) -> bool:
    """Return True when a page id can safely map to one Markdown filename."""
    return (
        isinstance(page_id, str)
        and bool(page_id)
        and not page_id.startswith(".")
        and ".." not in page_id
        and bool(_PAGE_ID_RE.fullmatch(page_id))
    )


def canonical_path(kind: Union[PageKind, str], page_id: Optional[str] = None) -> str:
    """Return the canonical POSIX relative path for a wiki page."""
    entry = _entry_for(kind)
    if entry.requires_page_id:
        page_id = _validate_page_id(page_id, required=True)
        return entry.path_pattern.format(page_id=page_id)
    if page_id is not None:
        raise WikiSurfaceError(f"{entry.kind.value} does not accept a page id.")
    return entry.path_pattern


def mcp_uri(kind: Union[PageKind, str], page_id: Optional[str] = None) -> str:
    """Return the canonical MCP URI for a wiki page."""
    entry = _entry_for(kind)
    if entry.requires_page_id:
        page_id = _validate_page_id(page_id, required=True)
        return f"{RESOURCE_SCHEME}://{entry.mcp_uri_kind}/{quote(page_id, safe='._-')}"
    if page_id is not None:
        raise WikiSurfaceError(f"{entry.kind.value} does not accept a page id.")
    return f"{RESOURCE_SCHEME}://{entry.mcp_uri_kind}"


def collect_wiki_pages(wiki_dir: Union[str, Path]) -> list[WikiSurfacePage]:
    """Collect active canonical wiki pages in deterministic registry order."""
    wiki = Path(wiki_dir)
    pages: list[WikiSurfacePage] = []

    for entry in _PAGE_KINDS:
        if entry.requires_page_id:
            pages.extend(_collect_directory_pages(wiki, entry))
            continue

        path = wiki / entry.path_pattern
        if path.is_file():
            page_id = entry.kind.value
            pages.append(_surface_page(wiki, path, entry, page_id))

    return pages


def _collect_directory_pages(
    wiki: Path, entry: WikiSurfaceKind
) -> list[WikiSurfacePage]:
    directory = entry.directory
    if directory is None:
        return []
    root = wiki / directory
    if not root.is_dir():
        return []

    pages: list[WikiSurfacePage] = []
    for path in sorted(
        root.glob("*.md"),
        key=lambda candidate: (candidate.name.casefold(), candidate.name),
    ):
        if not path.is_file() or _is_legacy_path(path, wiki):
            continue
        page_id = path.stem
        if not is_safe_page_id(page_id):
            continue
        pages.append(_surface_page(wiki, path, entry, page_id))
    return pages


def _surface_page(
    wiki: Path,
    path: Path,
    entry: WikiSurfaceKind,
    page_id: str,
) -> WikiSurfacePage:
    relative_path = path.relative_to(wiki).as_posix()
    return WikiSurfacePage(
        kind=entry.kind,
        page_id=page_id,
        label=entry.label,
        path=path.resolve(),
        relative_path=relative_path,
        mcp_uri=mcp_uri(entry.kind, page_id if entry.requires_page_id else None),
        obsidian_mirror_dir=entry.obsidian_mirror_dir,
        role=entry.role,
    )


def _entry_for(kind: Union[PageKind, str]) -> WikiSurfaceKind:
    try:
        page_kind = kind if isinstance(kind, PageKind) else PageKind(kind)
    except ValueError as exc:
        raise WikiSurfaceError(f"Unknown wiki page kind: {kind}") from exc
    return _KINDS_BY_KIND[page_kind]


def _validate_page_id(page_id: Optional[str], *, required: bool) -> str:
    if page_id is None:
        if required:
            raise WikiSurfaceError("page id is required for directory-backed pages.")
        raise WikiSurfaceError("page id is not supported for this page kind.")
    if not is_safe_page_id(page_id):
        raise WikiSurfaceError(f"Unsafe wiki page id: {page_id}")
    return page_id


def _is_legacy_path(path: Path, wiki: Path) -> bool:
    try:
        return path.relative_to(wiki).parts[:1] == ("legacy",)
    except ValueError:
        try:
            return path.resolve().relative_to(wiki.resolve()).parts[:1] == ("legacy",)
        except ValueError:
            return False
