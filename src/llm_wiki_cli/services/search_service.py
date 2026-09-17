"""Shared read-only wiki search, independent of transport and optional SDKs."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from ..config import validate_path, validate_source_root
from . import wiki_surface
from .documentation_query_builder import (
    normalize_documentation_query_limit,
    validate_live_query_source_selection,
)
from .io import read_md
from .search_rank import MAX_SEARCH_BYTES, MAX_SEARCH_PAGES, rank_pages
from .source_selection import resolve_source_selection
from .source_snapshot import build_source_snapshot, capture_source_selection_inputs

SEARCH_KINDS = frozenset(entry.mcp_uri_kind for entry in wiki_surface.iter_page_kinds())


def normalize_search(query: object, kinds: object, limit: object, mode: object):
    """Validate before discovering source or wiki inputs."""
    if not isinstance(query, str) or not query.strip() or len(query) > 4096:
        raise ValueError("query must be a non-empty string of at most 4096 characters")
    limit = normalize_documentation_query_limit(limit)
    if not isinstance(mode, str) or mode not in {"ranked", "substring"}:
        raise ValueError("Search mode must be ranked or substring")
    if kinds is not None and (
        not isinstance(kinds, (list, tuple))
        or len(kinds) > len(SEARCH_KINDS)
        or any(not isinstance(kind, str) for kind in kinds)
    ):
        raise ValueError("kinds must be an array of wiki search kinds")
    selected = set(kinds or SEARCH_KINDS)
    if selected - SEARCH_KINDS:
        raise ValueError(f"Unknown wiki search kind: {sorted(selected - SEARCH_KINDS)[0]}")
    return query, selected, limit, mode


def search_records(records: Iterable[dict[str, Any]], query: str, *, limit: int, mode: str):
    """Apply the same ranking and legacy substring contracts to captured pages."""
    if mode == "ranked":
        return rank_pages(records, query, limit=limit)
    matches = []
    total = scanned = pages = 0
    for record in records:
        content = record["content"]
        scanned += len(content.encode("utf-8"))
        pages += 1
        if scanned > MAX_SEARCH_BYTES or pages > MAX_SEARCH_PAGES:
            raise ValueError("Search exceeds page or byte limit; restrict the wiki or kinds")
        position = content.casefold().find(query.casefold())
        if position < 0:
            continue
        total += 1
        if len(matches) < limit:
            start, end = max(0, position - 80), min(len(content), position + len(query) + 80)
            snippet = re.sub(r"\s+", " ", content[start:end]).strip()
            matches.append({**{k: v for k, v in record.items() if k != "content"}, "snippet": snippet})
    returned = len(matches)
    bounds = {"total": total, "returned": returned, "truncated": total > returned}
    return {"query": query, "mode": mode, "total": total, "returned": returned,
            "count": returned, "truncated": bounds["truncated"],
            "bounds": {"results": bounds}, "results": matches}


def page_records(wiki_root: Path, kinds: set[str], *, reader: Callable = read_md):
    wiki_root = wiki_root.resolve()
    kind_map = {entry.kind: entry.mcp_uri_kind for entry in wiki_surface.iter_page_kinds()}
    for page in wiki_surface.collect_wiki_pages(wiki_root):
        kind = kind_map[page.kind]
        if kind not in kinds:
            continue
        if page.path.stat().st_size > MAX_SEARCH_BYTES:
            raise ValueError("Page exceeds search byte limit; restrict the wiki or kinds")
        content = reader(page.path)
        title = next((line.strip().lstrip("#").strip() or page.page_id
                      for line in content.splitlines() if line.strip().startswith("#")), page.page_id)
        yield {"kind": kind, "id": page.page_id, "uri": page.mcp_uri,
               "path": page.path.relative_to(wiki_root).as_posix(),
               "title": title, "content": content}


def search_wiki(query, *, src_dir=".", wiki_dir="docs/llm_wiki", kinds=None,
                limit=20, mode="ranked", source_selection=None, allow_external_src=False):
    query, kinds, limit, mode = normalize_search(query, kinds, limit, mode)
    source_root = validate_source_root(src_dir, "--src-dir", allow_external=allow_external_src)
    wiki_root = validate_path(wiki_dir, "--wiki-dir")
    policy = resolve_source_selection(source_root, source_selection)
    inputs = capture_source_selection_inputs(source_root, source_selection=source_selection,
                                             selection_policy=policy)
    validate_live_query_source_selection(source_root=source_root, wiki_root=wiki_root,
                                        live_identity=policy.identity if policy else None,
                                        live_selection_inputs=inputs, operation="wiki search")
    snapshot = build_source_snapshot(source_root, source_selection=source_selection,
                                     selection_policy=policy, expected_selection_inputs=inputs)
    validate_live_query_source_selection(source_root=source_root, wiki_root=wiki_root,
                                        live_identity=snapshot.source_selection_identity,
                                        live_selection_inputs=snapshot.source_selection_inputs,
                                        operation="wiki search")
    return search_records(page_records(wiki_root, kinds), query, limit=limit, mode=mode)
