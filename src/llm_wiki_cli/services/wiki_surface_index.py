"""Machine-readable index for generated wiki surfaces."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence, Union
from urllib.parse import unquote

from .io import write_bytes_atomic
from .paths import normalize_source_path
from .wiki_media import (
    build_asset_index,
    iter_markdown_link_targets,
    normalize_markdown_link_target,
)
from .wiki_surface import (
    PageKind,
    WikiSurfaceError,
    WikiSurfacePage,
    collect_wiki_pages,
    iter_page_kinds,
)


SURFACE_INDEX_FILENAME = ".llm-wiki-surface.json"
WIKI_SURFACE_INDEX_SCHEMA_VERSION = "llm-wiki-surface-index/v1"

_MERMAID_CLICK_RE = re.compile(r'^\s*click\s+\S+\s+"([^"]+)"', re.MULTILINE)
_MARKDOWN_PATH_RE = re.compile(r"\*\*Path:\*\*\s+`([^`]+)`")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:/")


@dataclass(frozen=True)
class SurfaceIndexEvaluation:
    """One collected canonical-page view reused by M1 projection builders."""

    pages: tuple[WikiSurfacePage, ...]
    content_by_path: Mapping[str, str]
    payload: Mapping[str, Any]
    serialized_bytes: bytes
    existing_asset_paths: frozenset[str]


def build_surface_index(
    wiki_dir: Union[str, Path],
    inventory: Mapping[str, Mapping[str, Any]],
    *,
    src_dir: Union[str, Path] = ".",
    entity_page_cache: Optional[Mapping[tuple[str, str], str]] = None,
    entity_occurrence_page_cache: Optional[Mapping[tuple[str, str, int], str]] = None,
    module_page_map: Optional[Mapping[str, str]] = None,
    entry_points: Optional[Sequence[Mapping[str, Any]]] = None,
    page_source_overrides: Optional[Mapping[str, Optional[str]]] = None,
) -> dict[str, Any]:
    """Build the deterministic wiki surface index payload."""
    return dict(
        evaluate_surface_index(
            wiki_dir,
            inventory,
            src_dir=src_dir,
            entity_page_cache=entity_page_cache,
            entity_occurrence_page_cache=entity_occurrence_page_cache,
            module_page_map=module_page_map,
            entry_points=entry_points,
            page_source_overrides=page_source_overrides,
        ).payload
    )


def evaluate_surface_index(
    wiki_dir: Union[str, Path],
    inventory: Mapping[str, Mapping[str, Any]],
    *,
    src_dir: Union[str, Path] = ".",
    entity_page_cache: Optional[Mapping[tuple[str, str], str]] = None,
    entity_occurrence_page_cache: Optional[Mapping[tuple[str, str, int], str]] = None,
    module_page_map: Optional[Mapping[str, str]] = None,
    entry_points: Optional[Sequence[Mapping[str, Any]]] = None,
    page_source_overrides: Optional[Mapping[str, Optional[str]]] = None,
) -> SurfaceIndexEvaluation:
    """Collect pages/assets once and build exact surface-index v1 bytes."""

    wiki = Path(wiki_dir)
    src_root = Path(src_dir)
    pages = collect_wiki_pages(wiki)
    content_by_path = _read_page_content(pages)
    page_entries = _page_entries(
        pages,
        content_by_path,
        _source_maps(
            inventory,
            src_root,
            entity_page_cache=entity_page_cache,
            entity_occurrence_page_cache=entity_occurrence_page_cache,
            module_page_map=module_page_map,
            entry_points=entry_points,
        ),
        src_root,
        page_source_overrides=page_source_overrides,
    )
    counts = _counts(page_entries)
    assets = build_asset_index(wiki, content_by_path)
    counts["assets"] = assets.counts
    dependency_pages = {
        "dependencies": counts["by_kind"][PageKind.DEPENDENCIES.value] > 0,
        "load_order": counts["by_kind"][PageKind.LOAD_ORDER.value] > 0,
        "count": counts["dependency_architecture"],
    }
    flows = _flow_entries(pages, entry_points or [], src_root)

    payload = {
        "schema_version": WIKI_SURFACE_INDEX_SCHEMA_VERSION,
        "counts": counts,
        "dependency_pages": dependency_pages,
        "assets": {
            "by_page": assets.by_page,
            "referenced": assets.referenced,
            "unreferenced": assets.unreferenced,
        },
        "flows": flows,
        "pages": page_entries,
    }
    payload["source_hash"] = _stable_hash(
        {
            "inventory": _inventory_fingerprint(inventory, src_root),
            "counts": counts,
            "dependency_pages": dependency_pages,
            "assets": {
                "counts": assets.counts,
                "by_page": assets.by_page,
                "referenced": assets.referenced,
                "unreferenced": assets.unreferenced,
            },
            "flows": flows,
            "pages": page_entries,
        }
    )
    serialized = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return SurfaceIndexEvaluation(
        pages=tuple(pages),
        content_by_path=content_by_path,
        payload=payload,
        serialized_bytes=serialized,
        existing_asset_paths=assets.existing_paths,
    )


def write_surface_index(
    wiki_dir: Union[str, Path],
    inventory: Mapping[str, Mapping[str, Any]],
    *,
    src_dir: Union[str, Path] = ".",
    entity_page_cache: Optional[Mapping[tuple[str, str], str]] = None,
    entity_occurrence_page_cache: Optional[Mapping[tuple[str, str, int], str]] = None,
    module_page_map: Optional[Mapping[str, str]] = None,
    entry_points: Optional[Sequence[Mapping[str, Any]]] = None,
    page_source_overrides: Optional[Mapping[str, Optional[str]]] = None,
) -> tuple[Path, str]:
    """Write the surface index artifact and return ``(path, state)``."""
    wiki = Path(wiki_dir)
    path = wiki / SURFACE_INDEX_FILENAME
    existed = path.exists()
    evaluation = evaluate_surface_index(
        wiki,
        inventory,
        src_dir=src_dir,
        entity_page_cache=entity_page_cache,
        entity_occurrence_page_cache=entity_occurrence_page_cache,
        module_page_map=module_page_map,
        entry_points=entry_points,
        page_source_overrides=page_source_overrides,
    )
    if existed and path.read_bytes() == evaluation.serialized_bytes:
        return path, "unchanged"

    write_bytes_atomic(path, evaluation.serialized_bytes)
    return path, "updated" if existed else "created"


def _read_page_content(pages: list[WikiSurfacePage]) -> dict[str, str]:
    content: dict[str, str] = {}
    for page in pages:
        content[page.relative_path] = page.path.read_text(encoding="utf-8")
    return content


def _page_entries(
    pages: list[WikiSurfacePage],
    content_by_path: Mapping[str, str],
    sources: Mapping[tuple[PageKind, str], Optional[str]],
    src_root: Path,
    *,
    page_source_overrides: Optional[Mapping[str, Optional[str]]] = None,
) -> list[dict[str, Any]]:
    canonical_by_path = {page.path.resolve(): page.relative_path for page in pages}
    overrides = _validated_page_source_overrides(
        pages,
        page_source_overrides,
        src_root,
    )
    entries = []
    for page in pages:
        content = content_by_path.get(page.relative_path, "")
        source_path = overrides.get(
            page.relative_path,
            sources.get((page.kind, page.page_id)),
        )
        if source_path is None and page.kind is PageKind.INFRASTRUCTURE:
            source_path = _source_path_from_markdown(content, src_root)
        entries.append(
            {
                "kind": page.kind.value,
                "id": page.page_id,
                "title": _markdown_title(content, page.page_id),
                "canonical_path": page.relative_path,
                "source_path": source_path,
                "role": page.role.value,
                "mcp_uri": page.mcp_uri,
                "outgoing_internal_links": _outgoing_internal_links(
                    page,
                    content,
                    canonical_by_path,
                ),
            }
        )
    return entries


def _validated_page_source_overrides(
    pages: Sequence[WikiSurfacePage],
    overrides: Optional[Mapping[str, Optional[str]]],
    src_root: Path,
) -> dict[str, Optional[str]]:
    """Validate explicit source mappings for already active canonical pages."""

    if overrides is None:
        return {}
    if not isinstance(overrides, Mapping):
        raise WikiSurfaceError("page_source_overrides must be an object")
    active = {page.relative_path for page in pages}
    normalized: dict[str, Optional[str]] = {}
    for page_path, source_path in overrides.items():
        if not isinstance(page_path, str) or page_path not in active:
            raise WikiSurfaceError(
                "page_source_overrides must identify active canonical pages"
            )
        if source_path is None:
            normalized[page_path] = None
            continue
        safe_source_path = _safe_source_path(source_path, src_root)
        if safe_source_path is None:
            raise WikiSurfaceError(
                f"page_source_overrides[{page_path!r}] must contain a safe "
                "repository-relative source path or null"
            )
        normalized[page_path] = safe_source_path
    return normalized


def _source_maps(
    inventory: Mapping[str, Mapping[str, Any]],
    src_root: Path,
    *,
    entity_page_cache: Optional[Mapping[tuple[str, str], str]],
    entity_occurrence_page_cache: Optional[Mapping[tuple[str, str, int], str]],
    module_page_map: Optional[Mapping[str, str]],
    entry_points: Optional[Sequence[Mapping[str, Any]]],
) -> dict[tuple[PageKind, str], Optional[str]]:
    sources: dict[tuple[PageKind, str], Optional[str]] = {}
    for filepath, file_data in inventory.items():
        source_path = _safe_source_path(str(filepath), src_root)
        module_page = (module_page_map or {}).get(
            filepath,
            Path(str(filepath)).stem,
        )
        sources[(PageKind.MODULES, module_page)] = source_path
        seen_names: dict[str, int] = {}
        for cls in file_data.get("classes", []):
            name = cls.get("name")
            if not name:
                continue
            name_text = str(name)
            seen_names[name_text] = seen_names.get(name_text, 0) + 1
            entity_page = (entity_page_cache or {}).get(
                (name_text, str(filepath)),
                name_text,
            )
            if entity_occurrence_page_cache is not None:
                entity_page = entity_occurrence_page_cache.get(
                    (name_text, str(filepath), seen_names[name_text]),
                    entity_page,
                )
            sources[(PageKind.ENTITIES, entity_page)] = source_path

    for entry in entry_points or []:
        flow_id = entry.get("id")
        if flow_id:
            sources[(PageKind.FLOWS, str(flow_id))] = _safe_source_path(
                entry.get("file") or entry.get("source_path"),
                src_root,
            )
    return sources


def _flow_entries(
    pages: list[WikiSurfacePage],
    entry_points: Sequence[Mapping[str, Any]],
    src_root: Path,
) -> list[dict[str, Any]]:
    flow_pages = {page.page_id for page in pages if page.kind is PageKind.FLOWS}
    metadata = {
        str(entry.get("id")): entry for entry in entry_points if entry.get("id")
    }
    flows = []
    for flow_id in sorted(flow_pages, key=lambda value: (value.casefold(), value)):
        entry = metadata.get(flow_id, {})
        category = str(entry.get("category") or flow_id.split("-", 1)[0])
        record = {
            "id": flow_id,
            "category": category,
            "entry_point": {
                "symbol": entry.get("symbol") or entry.get("entry"),
                "source_path": _safe_source_path(
                    entry.get("file") or entry.get("source_path"),
                    src_root,
                ),
                "label": entry.get("label") or entry.get("entry"),
            },
        }
        for key in ("detector", "language", "routes", "evidence"):
            if key in entry:
                record[key] = json.loads(json.dumps(entry[key], sort_keys=True))
        flows.append(record)
    return flows


def _counts(page_entries: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    by_kind = {entry.kind.value: 0 for entry in iter_page_kinds()}
    for page in page_entries:
        by_kind[str(page["kind"])] += 1
    dependency_count = (
        by_kind[PageKind.DEPENDENCIES.value] + by_kind[PageKind.LOAD_ORDER.value]
    )
    return {
        "total": len(page_entries),
        "by_kind": by_kind,
        "dependency_architecture": dependency_count,
    }


def _outgoing_internal_links(
    page: WikiSurfacePage,
    content: str,
    canonical_by_path: Mapping[Path, str],
) -> list[str]:
    links = set()
    for link in iter_markdown_link_targets(content):
        target = _resolve_internal_target(page, link.raw_target, canonical_by_path)
        if target is not None:
            links.add(target)
    for raw_link in _MERMAID_CLICK_RE.findall(content):
        target = _resolve_internal_target(page, raw_link, canonical_by_path)
        if target is not None:
            links.add(target)
    return sorted(links, key=lambda value: (value.casefold(), value))


def _resolve_internal_target(
    page: WikiSurfacePage,
    raw_link: str,
    canonical_by_path: Mapping[Path, str],
) -> Optional[str]:
    link = normalize_markdown_link_target(raw_link)
    if link.startswith(("http://", "https://", "mailto:", "#")):
        return None
    base, _sep, _anchor = link.partition("#")
    if not base:
        return None
    normalized = unquote(base).replace("\\", "/")
    target_path = (page.path.parent / normalized).resolve()
    return canonical_by_path.get(target_path)


def _source_path_from_markdown(content: str, src_root: Path) -> Optional[str]:
    match = _MARKDOWN_PATH_RE.search(content)
    if not match:
        return None
    return _safe_source_path(match.group(1), src_root)


def _safe_source_path(value: object, src_root: Path) -> Optional[str]:
    if not isinstance(value, str) or not value:
        return None
    normalized = normalize_source_path(value, str(src_root))
    if not normalized:
        return None
    normalized = normalized.replace("\\", "/")
    if normalized.startswith("/") or _WINDOWS_ABSOLUTE_RE.match(normalized):
        return None
    return normalized


def _markdown_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
    return fallback


def _inventory_fingerprint(
    inventory: Mapping[str, Mapping[str, Any]],
    src_root: Path,
) -> list[dict[str, Any]]:
    entries = []
    for filepath, file_data in sorted(
        inventory.items(),
        key=lambda item: _safe_source_path(str(item[0]), src_root) or str(item[0]),
    ):
        entries.append(
            {
                "path": _safe_source_path(str(filepath), src_root),
                "language": file_data.get("language"),
                "classes": sorted(
                    str(cls["name"])
                    for cls in file_data.get("classes", [])
                    if cls.get("name")
                ),
                "functions": sorted(
                    str(fn["name"])
                    for fn in file_data.get("functions", [])
                    if fn.get("name")
                ),
            }
        )
    return entries


def _stable_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()
