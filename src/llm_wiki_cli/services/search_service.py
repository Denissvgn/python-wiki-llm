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
from .io import read_md, decode_markdown_bytes
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


def normalize_discovery(discovery):
    if discovery is not None and discovery != "qualified-v1":
        raise ValueError("discovery must be None or qualified-v1")
    return discovery


def search_wiki(query, *, src_dir=".", wiki_dir="docs/llm_wiki", kinds=None,
                limit=20, mode="ranked", source_selection=None, allow_external_src=False,
                include_source=False, reader=read_md, discovery=None):
    normalize_discovery(discovery)
    query, kinds, limit, mode = normalize_search(query, kinds, limit, mode)
    if type(include_source) is not bool or (include_source and mode not in {"ranked", "ranked-v2"}):
        raise ValueError("Explicit source indexing requires current ranked mode and a boolean include_source")
    source_root = validate_source_root(src_dir, "--src-dir", allow_external=allow_external_src)
    wiki_root = validate_path(wiki_dir, "--wiki-dir")
    return search_prevalidated_roots(query, source_root=source_root, wiki_root=wiki_root,
        kinds=sorted(kinds), limit=limit, mode=mode, source_selection=source_selection,
        include_source=include_source, reader=reader, discovery=discovery)


def search_prevalidated_roots(query, *, source_root: Path, wiki_root: Path, kinds=None,
                             limit=20, mode="ranked", source_selection=None,
                             include_source=False, reader=read_md, discovery=None):
    """Share capture/ranking while preserving trusted MCP configured-root boundaries."""
    normalize_discovery(discovery)
    query, kinds, limit, mode = normalize_search(query, kinds, limit, mode)
    if type(include_source) is not bool or (include_source and mode not in {"ranked", "ranked-v2"}):
        raise ValueError("Explicit source indexing requires current ranked mode and a boolean include_source")
    def root_stamp(path):
        try:
            value = path.lstat()
        except FileNotFoundError:
            return None
        return value.st_dev, value.st_ino, value.st_mode
    roots = root_stamp(source_root), root_stamp(wiki_root)
    policy = resolve_source_selection(source_root, source_selection)
    inputs = capture_source_selection_inputs(source_root, source_selection=source_selection,
                                             selection_policy=policy)
    guarded = include_source or discovery is not None or policy is not None
    if not guarded:
        validate_live_query_source_selection(source_root=source_root, wiki_root=wiki_root,
            live_identity=policy.identity if policy else None,
            live_selection_inputs=inputs, operation="wiki search")
    bounded_source_capture = include_source or discovery is not None
    capture_options = {} if not bounded_source_capture else {
        "max_files": MAX_SEARCH_PAGES, "max_bytes": 16_777_216, "respect_ignores": True, "coherent": True,
    }
    snapshot = build_source_snapshot(source_root, source_selection=source_selection,
                                     selection_policy=policy, expected_selection_inputs=inputs, **capture_options)
    if not guarded:
        validate_live_query_source_selection(source_root=source_root, wiki_root=wiki_root,
            live_identity=snapshot.source_selection_identity,
            live_selection_inputs=snapshot.source_selection_inputs,
            operation="wiki search")
    if not guarded:
        return search_records(page_records(wiki_root, kinds, reader=reader), query, limit=limit, mode=mode)
    from .knowledge_storage import KnowledgeStorageError
    from .knowledge_storage_io import StorageReadSession
    from .search_source import MAX_SOURCE_INDEX_BYTES, capture_source_index, captured_manifest, source_page_selected
    from .source_selection import path_is_selected, validate_persisted_source_selection_identity
    from .workflow_profile import canonical_json

    wiki_reads = StorageReadSession(wiki_root, max_bytes=MAX_SEARCH_BYTES * 2)
    source_reads = StorageReadSession(source_root, max_bytes=MAX_SOURCE_INDEX_BYTES * 2)
    membership = _page_membership(wiki_root, kinds)
    if len(membership) > MAX_SEARCH_PAGES:
        raise ValueError("Search exceeds page membership limit; restrict wiki kinds")
    exclusions = {"excluded_source_pages": 0, "unknown_source_ownership_pages": 0}
    captured = None
    with wiki_reads.phase(), source_reads.phase():
        manifest = None
        try:
            manifest = captured_manifest(wiki_reads)
        except KnowledgeStorageError as exc:
            if exc.code != "storage-missing" or (wiki_root / ".llm-wiki-manifest.json").exists():
                raise
            if policy is not None or include_source:
                raise ValueError("Selected search requires a valid committed ownership manifest") from exc
        if manifest is not None:
            validate_persisted_source_selection_identity(manifest.generation_inputs,
                snapshot.source_selection_identity, live_selection_inputs=snapshot.source_selection_inputs,
                operation="wiki search")
        def eligible(path):
            if include_source and manifest is not None and not source_page_selected(path, snapshot, manifest):
                key = "unknown_source_ownership_pages" if path not in manifest.page_source_mappings else "excluded_source_pages"
                exclusions[key] += 1
                return False
            if policy is None:
                return True
            owner = manifest.page_source_mappings.get(path) if manifest is not None else None
            if owner is None:
                if path.startswith(("modules/", "entities/")):
                    exclusions["unknown_source_ownership_pages"] += 1
                    return False
                return True
            accepted = path_is_selected(policy, owner.source_path) and snapshot.path_is_effectively_selected(owner.source_path)
            if not accepted:
                exclusions["excluded_source_pages"] += 1
            return accepted
        original_pages = []
        captured_bytes = 0
        for page in page_records(wiki_root, kinds,
                reader=lambda path: decode_markdown_bytes(wiki_reads.read(path.relative_to(wiki_root).as_posix(), max(0, MAX_SEARCH_BYTES - captured_bytes))),
                eligible=eligible):
            captured_bytes += len(page["content"].encode("utf-8"))
            if len(original_pages) >= MAX_SEARCH_PAGES or captured_bytes > MAX_SEARCH_BYTES:
                raise ValueError("Search exceeds captured wiki limits")
            original_pages.append(page)
        pages_by_path = {page["path"]: page for page in original_pages}
        accounting = None
        if include_source:
            assert manifest is not None
            ranked_pages, accounting = capture_source_index(original_pages, snapshot, wiki_reads, source_reads, manifest=manifest)
        else:
            ranked_pages = original_pages
        result = search_records(ranked_pages, query, limit=limit, mode=mode)
        if discovery is not None:
            from .search_discovery_capture import capture_discovery
            from .search_discovery import DiscoveryError, enrich_search
            returned = {match["path"]: pages_by_path[match["path"]] for match in result["results"]}
            captured = capture_discovery(wiki_root, wiki_reads, returned, manifest=manifest)
            owners = {}
            if captured.manifest is not None:
                for path, owner in captured.manifest.page_source_mappings.items():
                    if path not in returned:
                        continue
                    stored = captured.manifest.sources.get(owner.source_path, {})
                    recorded_source = {"basis": "manifest-snapshot", "source_content_hash": stored.get("hash"),
                        "availability": "recorded" if stored.get("hash") else "unrecorded",
                        "live_comparison_performed": False}
                    tombstone = captured.manifest.tombstones.get(path)
                    if tombstone is not None:
                        recorded_source["tombstone"] = {"reason": tombstone.reason, "unknown_reason": tombstone.unknown_reason}
                    owners[path] = {**owner.to_payload(), "recorded_source": recorded_source}
            result = enrich_search(result, pages_by_path=returned, owner_mappings=owners,
                native_payload=captured.native_payload, recorded_reviews=captured.recorded_reviews)
            result["discovery"]["selection"] = {"identity": snapshot.source_selection_identity,
                "policy_active": policy is not None, "ownership_filter_complete": True,
                "scope": "captured-source-selection", **exclusions}
            result["discovery"]["limits"].update(source_snapshot_bytes=16_777_216, source_snapshot_files=10_000,
                native_root_bytes=262_144, native_read_bytes=8_388_608, native_records=1000, native_expanded_bytes=16_777_216, native_selectors=100)
            # Count the actual enrichment after caller-owned selection metadata.
            required_bytes = len(canonical_json(result["discovery"]))
            if required_bytes > 262_144:
                raise DiscoveryError("discovery-output-limit", "discovery", required_bytes=required_bytes)
    # Receipt acquisition itself rechecks native inputs. Freeze all published
    # metadata and count it before the final independent publication checks.
    native_receipt = captured.native.session.receipt() if captured is not None and captured.native is not None else None
    if discovery is not None:
        result["discovery"]["capture_work"] = {"wiki_capture_bytes_through_metadata": wiki_reads.bytes_read,
            "source_snapshot_input_bytes": sum(item.size for item in snapshot.captured_file_integrity.values()),
            "guard_marker_bytes_through_metadata": captured.guard_marker_bytes if captured is not None else 0,
            "selected_native": native_receipt,
            "scope": "observed captures through metadata; excludes final independent publication rechecks"}
        required_bytes = len(canonical_json(result["discovery"]))
        if required_bytes > 262_144:
            raise DiscoveryError("discovery-output-limit", "discovery", required_bytes=required_bytes)
    # No callback/serialization work or payload updates below this boundary.
    if captured is not None:
        captured.finish()
    wiki_reads.recheck()
    source_reads.recheck()
    validation_metrics: dict[str, int] = {}
    if not source_snapshot_matches_current_files(snapshot, metrics=validation_metrics):
        raise ValueError("Search capture changed before publication")
    if manifest is not None:
        validate_persisted_source_selection_identity(manifest.generation_inputs,
            snapshot.source_selection_identity, live_selection_inputs=snapshot.source_selection_inputs,
            operation="qualified wiki search")
    if _page_membership(wiki_root, kinds) != membership:
        raise ValueError("Wiki search membership changed before publication")

    if roots != (root_stamp(source_root), root_stamp(wiki_root)):
        raise ValueError("Search root ownership changed before publication")
    if accounting is not None:
        accounting.update(source_read_bytes_including_rechecks=source_reads.bytes_read,
            wiki_read_bytes_including_rechecks=wiki_reads.bytes_read,
            source_snapshot_captured_input_bytes=sum(item.size for item in snapshot.captured_file_integrity.values()),
            final_source_validation=validation_metrics,
            read_work_scope="unique indexed bytes exclude capture hashes and required rechecks")
        result["source_indexing"] = accounting

    return result


def _page_membership(wiki_root: Path, kinds: set[str]) -> tuple[str, ...]:
    kind_map = {entry.kind: entry.mcp_uri_kind for entry in wiki_surface.iter_page_kinds()}
    return tuple(page.path.relative_to(wiki_root).as_posix()
                 for page in wiki_surface.collect_wiki_pages(wiki_root) if kind_map[page.kind] in kinds)
