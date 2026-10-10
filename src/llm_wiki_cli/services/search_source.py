"""Explicit bounded static-source text indexing for canonical module candidates."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Mapping
from typing import Any

from .knowledge_artifacts import _decode_json_object
from .knowledge_storage import MAX_EXPANDED_BYTES
from .knowledge_storage_io import StorageReadSession
from .search_rank import MAX_SEARCH_BYTES, MAX_SEARCH_PAGES
from .source_snapshot import SourceSnapshot
from .sync_manifest import MANIFEST_FILENAME, SyncManifest

MAX_SOURCE_FILE_BYTES = 1_048_576
MAX_SOURCE_INDEX_BYTES = 16_777_216
SOURCE_INDEX_VERSION = "uniform-selected-static-source/v1"


def augment_module_page(page: Mapping[str, Any], source_path: str, raw: bytes) -> dict[str, Any]:
    """Preserve wiki identity separately from the derived searchable text."""
    if len(raw) > MAX_SOURCE_FILE_BYTES:
        raise ValueError("Source file exceeds indexing byte limit; narrow the source selection")
    text = raw.decode("utf-8")
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    fence = "`" * max(3, longest + 1)
    content = page["content"]
    addition = ("\n\n## Selected source indexing evidence\n\n"
                "Static source text; runtime behavior has not been evaluated.\n\n"
                f"{fence}python\n{text}" + ("" if text.endswith("\n") else "\n") + f"{fence}\n")
    result = dict(page, content=content + addition)
    def digest(value):
        return hashlib.sha256(value).hexdigest()
    result["indexing"] = {
        "treatment": SOURCE_INDEX_VERSION,
        "original_wiki_content_sha256": digest(content.encode("utf-8")),
        "source_path": source_path, "source_sha256": digest(raw), "source_bytes": len(raw),
        "indexed_content_sha256": digest(result["content"].encode("utf-8")),
        "runtime_behavior_evaluated": False,
    }
    return result


def capture_source_index(
    pages: Iterable[dict[str, Any]], snapshot: SourceSnapshot,
    wiki_reads: StorageReadSession, source_reads: StorageReadSession,
    *, manifest: SyncManifest | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Index only manifest-owned module sources inside the captured live boundary."""
    if manifest is None:
        manifest = captured_manifest(wiki_reads)
    selected = set(snapshot.all_source_paths) & set(snapshot.captured_content_hashes)
    indexed, sources = [], {}
    total_bytes = 0
    for page in pages:
        if len(indexed) >= MAX_SEARCH_PAGES:
            raise ValueError("Search exceeds page limit; restrict wiki kinds")
        result = page
        if page["kind"] == "modules":
            owner = manifest.page_source_mappings.get(page["path"])
            if owner is None or owner.scope != "module":
                raise ValueError("Source indexing requires an exact committed module owner")
            source = owner.source_path
            if source not in selected or not snapshot.path_is_effectively_selected(source):
                # This file is outside the actual capture; no content or source claim is admitted.
                continue
            if source not in sources:
                value = source_reads.read(source, MAX_SOURCE_FILE_BYTES)
                if "sha256:" + hashlib.sha256(value).hexdigest() != snapshot.captured_content_hashes.get(source):
                    raise ValueError("Source indexing input changed during capture")
                sources[source] = value
                if sum(len(item) for item in sources.values()) > MAX_SOURCE_INDEX_BYTES:
                    raise ValueError("Source indexing exceeds unique byte limit; narrow selection")
            result = augment_module_page(page, source, sources[source])
        total_bytes += len(result["content"].encode("utf-8"))
        if total_bytes > MAX_SEARCH_BYTES:
            raise ValueError("Combined wiki/source indexing exceeds byte limit; restrict scope")
        indexed.append(result)
    return indexed, {"schema_version": "llm-wiki-source-search-index/v1",
                     "treatment": SOURCE_INDEX_VERSION, "source_files": len(sources),
                     "source_bytes": sum(len(value) for value in sources.values()),
                     "indexed_bytes": total_bytes, "max_source_file_bytes": MAX_SOURCE_FILE_BYTES,
                     "max_source_bytes": MAX_SOURCE_INDEX_BYTES,
                     "runtime_behavior_evaluated": False, "source_selection_scope": "captured-selected-files"}


def captured_manifest(reads: StorageReadSession) -> SyncManifest:
    raw = reads.read(MANIFEST_FILENAME, MAX_EXPANDED_BYTES)
    return SyncManifest.from_payload(
        _decode_json_object(raw, "manifest"), object_reader=reads.read)


def source_page_selected(path: str, snapshot: SourceSnapshot, manifest: SyncManifest) -> bool:
    if not path.startswith(("modules/", "entities/")):
        return True
    owner = manifest.page_source_mappings.get(path)
    return bool(owner and owner.source_path in snapshot.all_source_paths
                and snapshot.path_is_effectively_selected(owner.source_path))
