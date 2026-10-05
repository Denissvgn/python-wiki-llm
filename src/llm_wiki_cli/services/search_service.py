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
from .source_snapshot import (
    build_source_snapshot, capture_source_selection_inputs, source_snapshot_matches_current_files,
)

SEARCH_KINDS = frozenset(entry.mcp_uri_kind for entry in wiki_surface.iter_page_kinds())


def normalize_search(query: object, kinds: object, limit: object, mode: object):
    """Validate before discovering source or wiki inputs."""
    if not isinstance(query, str) or not query.strip() or len(query) > 4096:
        raise ValueError("query must be a non-empty string of at most 4096 characters")
    limit = normalize_documentation_query_limit(limit)
    if not isinstance(mode, str) or mode not in {"ranked", "ranked-v1", "ranked-v2", "substring"}:
        raise ValueError("Search mode must be ranked, ranked-v1, ranked-v2 or substring")
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
    if mode == "ranked-v1":
        result = rank_pages(records, query, limit=limit)
        result["mode"] = mode
        return result
    if mode in {"ranked", "ranked-v2"}:
        from .search_lexical import rank_pages as rank_candidate
        result = rank_candidate(records, query, limit=limit)
        result.update(mode=mode, experimental=False, definitive_answer=False)
        return result
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


def page_records(wiki_root: Path, kinds: set[str], *, reader: Callable = read_md,
                 eligible: Callable | None = None):
    wiki_root = wiki_root.resolve()
    kind_map = {entry.kind: entry.mcp_uri_kind for entry in wiki_surface.iter_page_kinds()}
    for page in wiki_surface.collect_wiki_pages(wiki_root):
        kind = kind_map[page.kind]
        if kind not in kinds:
            continue
        if eligible is not None and not eligible(page.path.relative_to(wiki_root).as_posix()):
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
                limit=20, mode="ranked", source_selection=None, allow_external_src=False,
                include_source=False, reader=read_md):
    query, kinds, limit, mode = normalize_search(query, kinds, limit, mode)
    if type(include_source) is not bool or (include_source and mode != "ranked-v2"):
        raise ValueError("Explicit source indexing requires ranked-v2 and a boolean include_source")
    source_root = validate_source_root(src_dir, "--src-dir", allow_external=allow_external_src)
    wiki_root = validate_path(wiki_dir, "--wiki-dir")
    return search_prevalidated_roots(query, source_root=source_root, wiki_root=wiki_root,
        kinds=sorted(kinds), limit=limit, mode=mode, source_selection=source_selection,
        include_source=include_source, reader=reader)


def search_prevalidated_roots(query, *, source_root: Path, wiki_root: Path, kinds=None,
                             limit=20, mode="ranked", source_selection=None,
                             include_source=False, reader=read_md):
    """Share capture/ranking while preserving trusted MCP configured-root boundaries."""
    query, kinds, limit, mode = normalize_search(query, kinds, limit, mode)
    if type(include_source) is not bool or (include_source and mode != "ranked-v2"):
        raise ValueError("Explicit source indexing requires ranked-v2 and a boolean include_source")
    policy = resolve_source_selection(source_root, source_selection)
    inputs = capture_source_selection_inputs(source_root, source_selection=source_selection,
                                             selection_policy=policy)
    validate_live_query_source_selection(source_root=source_root, wiki_root=wiki_root,
                                        live_identity=policy.identity if policy else None,
                                        live_selection_inputs=inputs, operation="wiki search")
    capture_options = {} if not include_source else {
        "max_files": MAX_SEARCH_PAGES, "max_bytes": 16_777_216, "respect_ignores": True, "coherent": True,
    }
    snapshot = build_source_snapshot(source_root, source_selection=source_selection,
                                     selection_policy=policy, expected_selection_inputs=inputs, **capture_options)
    validate_live_query_source_selection(source_root=source_root, wiki_root=wiki_root,
                                        live_identity=snapshot.source_selection_identity,
                                        live_selection_inputs=snapshot.source_selection_inputs,
                                        operation="wiki search")
    if not include_source:
        return search_records(page_records(wiki_root, kinds, reader=reader), query, limit=limit, mode=mode)
    from .knowledge_storage_io import StorageReadSession
    from .search_source import MAX_SOURCE_INDEX_BYTES, capture_source_index, captured_manifest, source_page_selected

    wiki_reads = StorageReadSession(wiki_root, max_bytes=MAX_SEARCH_BYTES * 2)
    source_reads = StorageReadSession(source_root, max_bytes=MAX_SOURCE_INDEX_BYTES * 2)
    membership = _page_membership(wiki_root, kinds)
    with wiki_reads.phase(), source_reads.phase():
        manifest = captured_manifest(wiki_reads)
        records = page_records(wiki_root, kinds,
            reader=lambda path: wiki_reads.read(path.relative_to(wiki_root).as_posix(), MAX_SEARCH_BYTES).decode("utf-8"),
            eligible=lambda path: source_page_selected(path, snapshot, manifest))
        indexed, accounting = capture_source_index(records, snapshot, wiki_reads, source_reads, manifest=manifest)
        result = search_records(indexed, query, limit=limit, mode=mode)
    wiki_reads.recheck()
    source_reads.recheck()
    validation_metrics: dict[str, int] = {}
    if not source_snapshot_matches_current_files(snapshot, metrics=validation_metrics):
        raise ValueError("Source indexing capture changed before publication")
    validate_live_query_source_selection(source_root=source_root, wiki_root=wiki_root,
        live_identity=snapshot.source_selection_identity, live_selection_inputs=snapshot.source_selection_inputs,
        operation="source-indexed wiki search")
    if _page_membership(wiki_root, kinds) != membership:
        raise ValueError("Wiki search membership changed before publication")
    accounting.update(
        source_read_bytes_including_rechecks=source_reads.bytes_read,
        wiki_read_bytes_including_rechecks=wiki_reads.bytes_read,
        source_snapshot_captured_input_bytes=sum(item.size for item in snapshot.captured_file_integrity.values()),
        final_source_validation=validation_metrics,
        read_work_scope="unique indexed bytes exclude capture hashes and required rechecks",
    )
    result["source_indexing"] = accounting
    return result


def _page_membership(wiki_root: Path, kinds: set[str]) -> tuple[str, ...]:
    kind_map = {entry.kind: entry.mcp_uri_kind for entry in wiki_surface.iter_page_kinds()}
    return tuple(page.path.relative_to(wiki_root).as_posix()
                 for page in wiki_surface.collect_wiki_pages(wiki_root) if kind_map[page.kind] in kinds)
