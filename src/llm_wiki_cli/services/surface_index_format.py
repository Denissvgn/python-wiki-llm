"""Format checks for the ``llm-wiki-surface-index/v1`` wiki surface index.

The surface index (``.llm-wiki-surface.json``) lists every canonical wiki
page with its kind, coordinates, source file and internal links, plus page
counts, media assets and user-flow entry points. These checks read no wiki or
source files: they confirm a decoded index is internally consistent with the
canonical page registry. ``source_hash`` commits the source inventory, which
the index does not carry, so only its shape is checked.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from .validation import SharedValidationError, require_portable_relative_path
from .wiki_surface import (
    WikiSurfaceError,
    canonical_path,
    is_safe_page_id,
    iter_page_kinds,
    mcp_uri,
)
from .wiki_surface_index import (
    SURFACE_INDEX_FILENAME as SURFACE_INDEX_FILENAME,
    WIKI_SURFACE_INDEX_SCHEMA_VERSION,
)

#: The format this module checks, written to ``SURFACE_INDEX_FILENAME``.
SURFACE_INDEX_SCHEMA_VERSION = WIKI_SURFACE_INDEX_SCHEMA_VERSION

#: Page kinds in the order the index lists them, with each kind's role.
SURFACE_PAGE_KINDS = tuple(entry.kind.value for entry in iter_page_kinds())
SURFACE_PAGE_ROLES = {entry.kind.value: entry.role.value for entry in iter_page_kinds()}
#: Kinds with a single fixed page; its id is the kind itself.
SURFACE_ROOT_KINDS = frozenset(
    entry.kind.value for entry in iter_page_kinds() if not entry.requires_page_id
)
SURFACE_MEDIA_TYPES = ("image", "video", "other")

_TOP_FIELDS = frozenset({
    "schema_version", "counts", "dependency_pages", "assets", "flows", "pages", "source_hash",
})
_PAGE_FIELDS = frozenset({
    "kind", "id", "title", "canonical_path", "source_path", "role", "mcp_uri",
    "outgoing_internal_links",
})
_COUNT_FIELDS = frozenset({"total", "by_kind", "dependency_architecture", "assets"})
_ASSET_COUNT_FIELDS = frozenset({"total", "referenced", "unreferenced", "by_media_type"})
_FLOW_REQUIRED = frozenset({"id", "category", "entry_point"})
_FLOW_OPTIONAL = frozenset({"detector", "language", "routes", "evidence"})
_ENTRY_POINT_FIELDS = frozenset({"symbol", "source_path", "label"})
_SOURCE_HASH = re.compile(r"sha256:[0-9a-f]{64}")
_KIND_ORDER = {kind: index for index, kind in enumerate(SURFACE_PAGE_KINDS)}


class SurfaceIndexError(ValueError):
    """A surface index does not follow its format."""


def validate_surface_index(document: object) -> None:
    """Raise ``SurfaceIndexError`` unless *document* is a valid surface index."""
    data = _object(document, "surface_index")
    _exact(data, _TOP_FIELDS, frozenset(), "surface_index")
    if data["schema_version"] != SURFACE_INDEX_SCHEMA_VERSION:
        raise SurfaceIndexError(
            f"surface_index.schema_version: must be {SURFACE_INDEX_SCHEMA_VERSION!r}"
        )
    source_hash = data["source_hash"]
    if not isinstance(source_hash, str) or not _SOURCE_HASH.fullmatch(source_hash):
        raise SurfaceIndexError("surface_index.source_hash: must be a sha256: digest")
    pages = _pages(data["pages"])
    by_kind = _counts(data["counts"], pages)
    _dependency_pages(data["dependency_pages"], by_kind, data["counts"]["dependency_architecture"])
    _assets(data["assets"], data["counts"]["assets"], set(pages))
    _flows(data["flows"], {page["id"] for page in pages.values() if page["kind"] == "flows"})


def _pages(value: object) -> dict[str, Mapping[str, Any]]:
    pages = _list(value, "surface_index.pages")
    by_path: dict[str, Mapping[str, Any]] = {}
    previous: tuple[int, str, str] | None = None
    for index, raw in enumerate(pages):
        field = f"surface_index.pages[{index}]"
        page = _object(raw, field)
        _exact(page, _PAGE_FIELDS, frozenset(), field)
        kind = page["kind"]
        if kind not in _KIND_ORDER:
            raise SurfaceIndexError(f"{field}.kind: unsupported page kind {kind!r}")
        page_id = page["id"]
        if kind in SURFACE_ROOT_KINDS:
            if page_id != kind:
                raise SurfaceIndexError(f"{field}.id: must be {kind!r}")
            coordinate = None
        else:
            if not isinstance(page_id, str) or not is_safe_page_id(page_id):
                raise SurfaceIndexError(f"{field}.id: must be a safe page id")
            coordinate = page_id
        try:
            path, uri = canonical_path(kind, coordinate), mcp_uri(kind, coordinate)
        except WikiSurfaceError as exc:  # pragma: no cover - guarded above
            raise SurfaceIndexError(f"{field}.id: {exc}") from exc
        if page["canonical_path"] != path:
            raise SurfaceIndexError(f"{field}.canonical_path: must be {path!r}")
        if page["mcp_uri"] != uri:
            raise SurfaceIndexError(f"{field}.mcp_uri: must be {uri!r}")
        if page["role"] != SURFACE_PAGE_ROLES[kind]:
            raise SurfaceIndexError(f"{field}.role: must be {SURFACE_PAGE_ROLES[kind]!r}")
        if not isinstance(page["title"], str) or not page["title"]:
            raise SurfaceIndexError(f"{field}.title: must be a non-empty string")
        if page["source_path"] is not None:
            _portable(page["source_path"], f"{field}.source_path")
        _sorted_unique(
            _strings(page["outgoing_internal_links"], f"{field}.outgoing_internal_links"),
            f"{field}.outgoing_internal_links",
        )
        name = path.rsplit("/", 1)[-1]
        order = (_KIND_ORDER[kind], name.casefold(), name)
        if previous is not None and order <= previous:
            raise SurfaceIndexError(f"{field}: pages must follow kind order, then file name")
        previous = order
        by_path[path] = page
    for path, page in by_path.items():
        unknown = [link for link in page["outgoing_internal_links"] if link not in by_path]
        if unknown:
            raise SurfaceIndexError(
                f"surface_index.pages[{path}].outgoing_internal_links: "
                f"{unknown[0]!r} is not an indexed page"
            )
    return by_path


def _counts(value: object, pages: Mapping[str, Mapping[str, Any]]) -> dict[str, int]:
    counts = _object(value, "surface_index.counts")
    _exact(counts, _COUNT_FIELDS, frozenset(), "surface_index.counts")
    if _count(counts["total"], "surface_index.counts.total") != len(pages):
        raise SurfaceIndexError("surface_index.counts.total: must count the indexed pages")
    by_kind = _object(counts["by_kind"], "surface_index.counts.by_kind")
    _exact(by_kind, frozenset(SURFACE_PAGE_KINDS), frozenset(), "surface_index.counts.by_kind")
    for kind in SURFACE_PAGE_KINDS:
        actual = sum(1 for page in pages.values() if page["kind"] == kind)
        if _count(by_kind[kind], f"surface_index.counts.by_kind.{kind}") != actual:
            raise SurfaceIndexError(f"surface_index.counts.by_kind.{kind}: must count its pages")
    dependency = _count(counts["dependency_architecture"], "surface_index.counts.dependency_architecture")
    if dependency != by_kind["dependencies"] + by_kind["load-order"]:
        raise SurfaceIndexError(
            "surface_index.counts.dependency_architecture: must count dependency and load-order pages"
        )
    assets = _object(counts["assets"], "surface_index.counts.assets")
    _exact(assets, _ASSET_COUNT_FIELDS, frozenset(), "surface_index.counts.assets")
    total = _count(assets["total"], "surface_index.counts.assets.total")
    referenced = _count(assets["referenced"], "surface_index.counts.assets.referenced")
    unreferenced = _count(assets["unreferenced"], "surface_index.counts.assets.unreferenced")
    if total != referenced + unreferenced:
        raise SurfaceIndexError(
            "surface_index.counts.assets.total: must be referenced plus unreferenced"
        )
    media = _object(assets["by_media_type"], "surface_index.counts.assets.by_media_type")
    _exact(media, frozenset(SURFACE_MEDIA_TYPES), frozenset(), "surface_index.counts.assets.by_media_type")
    if sum(_count(media[name], f"surface_index.counts.assets.by_media_type.{name}")
           for name in SURFACE_MEDIA_TYPES) != total:
        raise SurfaceIndexError(
            "surface_index.counts.assets.by_media_type: must add up to the asset total"
        )
    return dict(by_kind)


def _dependency_pages(value: object, by_kind: Mapping[str, int], count: int) -> None:
    pages = _object(value, "surface_index.dependency_pages")
    _exact(pages, {"dependencies", "load_order", "count"}, frozenset(), "surface_index.dependency_pages")
    for name, kind in (("dependencies", "dependencies"), ("load_order", "load-order")):
        if pages[name] is not (by_kind[kind] > 0):
            raise SurfaceIndexError(
                f"surface_index.dependency_pages.{name}: must say whether the page is indexed"
            )
    if pages["count"] != count or isinstance(pages["count"], bool):
        raise SurfaceIndexError(
            "surface_index.dependency_pages.count: must equal counts.dependency_architecture"
        )


def _assets(value: object, counts: Mapping[str, Any], page_paths: set[str]) -> None:
    assets = _object(value, "surface_index.assets")
    _exact(assets, {"by_page", "referenced", "unreferenced"}, frozenset(), "surface_index.assets")
    by_page = _object(assets["by_page"], "surface_index.assets.by_page")
    used: set[str] = set()
    for page, paths in by_page.items():
        field = f"surface_index.assets.by_page[{page}]"
        if page not in page_paths:
            raise SurfaceIndexError(f"{field}: is not an indexed page")
        paths = _strings(paths, field)
        if not paths:
            raise SurfaceIndexError(f"{field}: must list at least one asset")
        _sorted_unique(paths, field)
        for path in paths:
            _asset_path(path, field)
        used.update(paths)
    referenced = _strings(assets["referenced"], "surface_index.assets.referenced")
    _sorted_unique(referenced, "surface_index.assets.referenced")
    if set(referenced) != used:
        raise SurfaceIndexError(
            "surface_index.assets.referenced: must list exactly the assets in by_page"
        )
    unreferenced = _strings(assets["unreferenced"], "surface_index.assets.unreferenced")
    _sorted_unique(unreferenced, "surface_index.assets.unreferenced")
    for path in unreferenced:
        _asset_path(path, "surface_index.assets.unreferenced")
    if set(unreferenced) & used:
        raise SurfaceIndexError("surface_index.assets.unreferenced: overlaps referenced assets")
    if len(unreferenced) != counts["unreferenced"]:
        raise SurfaceIndexError(
            "surface_index.assets.unreferenced: must match counts.assets.unreferenced"
        )
    if counts["referenced"] > len(referenced):
        raise SurfaceIndexError(
            "surface_index.counts.assets.referenced: exceeds the referenced assets"
        )


def _flows(value: object, flow_pages: set[str]) -> None:
    flows = _list(value, "surface_index.flows")
    seen: list[str] = []
    for index, raw in enumerate(flows):
        field = f"surface_index.flows[{index}]"
        flow = _object(raw, field)
        _exact(flow, _FLOW_REQUIRED, _FLOW_OPTIONAL, field)
        if flow["id"] not in flow_pages:
            raise SurfaceIndexError(f"{field}.id: is not an indexed flow page")
        if not isinstance(flow["category"], str):
            raise SurfaceIndexError(f"{field}.category: must be a string")
        entry = _object(flow["entry_point"], f"{field}.entry_point")
        _exact(entry, _ENTRY_POINT_FIELDS, frozenset(), f"{field}.entry_point")
        for name in ("symbol", "label"):
            if entry[name] is not None and not isinstance(entry[name], str):
                raise SurfaceIndexError(f"{field}.entry_point.{name}: must be a string or null")
        if entry["source_path"] is not None:
            _portable(entry["source_path"], f"{field}.entry_point.source_path")
        seen.append(flow["id"])
    _sorted_unique(seen, "surface_index.flows")
    if set(seen) != flow_pages:
        raise SurfaceIndexError("surface_index.flows: must describe every indexed flow page")


def _sorted_unique(values: Sequence[str], field: str) -> None:
    keys = [(value.casefold(), value) for value in values]
    if any(left >= right for left, right in zip(keys, keys[1:])):
        raise SurfaceIndexError(f"{field}: must be unique and sorted case-insensitively")


def _asset_path(value: str, field: str) -> None:
    parts = value.split("/")
    if (
        len(parts) < 2 or parts[0] != "assets" or "\\" in value
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise SurfaceIndexError(f"{field}: {value!r} is not a path under assets/")


def _portable(value: object, field: str) -> None:
    try:
        if require_portable_relative_path(value) == value:
            return
    except SharedValidationError:
        pass
    raise SurfaceIndexError(f"{field}: must be a portable repository-relative path")


def _count(value: object, field: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise SurfaceIndexError(f"{field}: must be a non-negative integer")
    return value


def _strings(value: object, field: str) -> list[str]:
    items = _list(value, field)
    if any(not isinstance(item, str) for item in items):
        raise SurfaceIndexError(f"{field}: must contain only strings")
    return items


def _list(value: object, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise SurfaceIndexError(f"{field}: must be an array")
    return value


def _object(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise SurfaceIndexError(f"{field}: must be a JSON object")
    return value


def _exact(
    value: Mapping[str, Any], required: set[str] | frozenset[str],
    optional: set[str] | frozenset[str], field: str,
) -> None:
    missing = sorted(set(required) - set(value))
    if missing:
        raise SurfaceIndexError(f"{field}.{missing[0]}: is required")
    unknown = sorted(set(value) - set(required) - set(optional))
    if unknown:
        raise SurfaceIndexError(f"{field}.{unknown[0]}: is not supported")
