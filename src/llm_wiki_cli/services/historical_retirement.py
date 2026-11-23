"""Plan explicit whole-file archival from the authenticated *prior* source projection."""

from collections import Counter
from pathlib import PurePosixPath
from typing import NoReturn

from llm_wiki_engine.historical_sources import (
    INPUT, SCHEMA, bound_records, page_matches, predecessor_records, read_records, remove_bound_registry,
)
from llm_wiki_engine.host import emit
from llm_wiki_engine.knowledge_evidence import is_valid_sha256, sha256_bytes
from llm_wiki_engine.knowledge_storage import MAX_EXPANDED_BYTES
from llm_wiki_engine.knowledge_storage_io import StorageReadSession
from llm_wiki_engine.source_retirement import SourceRetirementError
from llm_wiki_engine.sync_manifest import ManifestPageSource
from llm_wiki_engine.validation import portable_path_key, require_repository_relative_path
from llm_wiki_engine.wiki_surface import PageKind, canonical_path
from .source_snapshot import confirmed_missing_source_paths


def refuse(message: str) -> NoReturn:
    raise SourceRetirementError(f"Historical source retirement refused: {message}. For enrolled pages, preview --release-historical-page PAGE before reconciling a replacement.")


def _selected_paths(values, maximum):
    if values is None:
        return ()
    if isinstance(values, (str, bytes)):
        refuse("supply a collection of repository-relative source paths")
    unique = set()
    error = SourceRetirementError("Historical source retirement requires portable source-relative paths")
    for index, path in enumerate(values):
        if index >= maximum:
            refuse(f"select up to {maximum} paths per operation")
        unique.add(require_repository_relative_path(
            path, text_error=error, posix_error=error, normalized_error=error,
            absolute_error=error, separator_error=error, control_error=error,
            reject_delete_character=True, portability_error=error,
        ))
    return tuple(sorted(unique))


def selected_sources(values):
    return _selected_paths(values, 256)


def selected_pages(values):
    pages = _selected_paths(values, 4096)
    for path in pages:
        parts = PurePosixPath(path).parts
        if (len(parts) != 2 or parts[0] not in {"modules", "entities"}
                or canonical_path(PageKind(parts[0]), PurePosixPath(path).stem) != path):
            refuse(f"expected an exact canonical module or entity Markdown path, got {path!r}")
    return pages


def confirm_absence(snapshot, sources):
    if not sources:
        return
    if snapshot.only_files is not None:
        refuse("a partial source scan cannot establish whole-file absence")
    missing = confirmed_missing_source_paths(snapshot, sources)
    if missing != set(sources):
        refuse(f"current complete source selection cannot confirm absence of {sorted(set(sources) - missing)!r}")


def check_prior_pages(wiki_root, previous, next_records):
    """Bind an imminent write to the exact enrollment preimages, including its index."""
    if not previous and not next_records:
        return
    with StorageReadSession(wiki_root).phase() as reader:
        remove_bound_registry(reader.read("index.md", MAX_EXPANDED_BYTES).decode("utf-8"), previous)
        for path, row in (previous | next_records).items():
            raw = reader.read(path, MAX_EXPANDED_BYTES)
            if path in previous:
                matched = page_matches(raw, row["page_hash"])
            else:
                matched = sha256_bytes(raw) == row["page_hash"]
            if not matched:
                refuse(f"original page {path!r} changed after the historical source plan")


def _original_owners(manifest, source):
    previous = manifest.sources.get(source)
    if previous is None or not isinstance(previous.get("entities"), list):
        refuse(f"{source!r} has no active predecessor source evidence; start from its intact prior wiki")
    expected = {ManifestPageSource("module", source)}
    for name, count in Counter(previous["entities"]).items():
        expected.update(ManifestPageSource("entity", source, name, index) for index in range(1, count + 1))
    owners = {path: owner for path, owner in manifest.page_source_mappings.items() if owner in expected}
    if Counter(owners.values()) != Counter({owner: 1 for owner in expected}):
        refuse(f"predecessor page custody is incomplete or ambiguous for {source!r}")
    return owners


def released_inputs(manifest, artifacts, source_snapshot):
    """Associate ordinary revival with the current capture and the previous native page digest."""
    from llm_wiki_engine.contracts import SECTION_OWNERSHIP_EXTENSION_KEY
    from llm_wiki_engine.knowledge_artifacts import require_validated_artifacts
    from llm_wiki_engine.historical_sources import RELEASES, latest_released_pages
    from .sync_transitions import ReleasedPageInputs

    if RELEASES not in manifest.generation_inputs or artifacts is None:
        return None
    released = latest_released_pages(manifest.generation_inputs).keys() & manifest.tombstones.keys()
    if not released or manifest.artifact_hashes is None:
        return None
    prior = require_validated_artifacts(artifacts)
    if manifest.artifact_hashes.knowledge_index_hash != prior.knowledge_index_hash:
        refuse("previous source/page custody is not bound to this native snapshot")
    sources = {owner.source_path for path, owner in manifest.page_source_mappings.items() if path in released}
    paths = {path for path, owner in manifest.page_source_mappings.items()
             if owner.source_path in sources and path in manifest.tombstones}
    locators = {c.locator: c.document.canonical_path for c in prior.knowledge.concepts if c.document.canonical_path in paths}
    sections = prior.knowledge.extensions.get(SECTION_OWNERSHIP_EXTENSION_KEY, {}).get("pages", ())
    page_hashes = {locators[row["page_locator"]]: row["source_hash"] for row in sections if row["page_locator"] in locators}
    return ReleasedPageInputs(source_snapshot.captured_content_hashes, page_hashes)


def plan_retirement(options, manifest, committed, snapshot, inventory, page_plan, generation_inputs):
    previous = bound_records(manifest)
    requested = set(options.retire_missing_sources)
    requested_pages = set(options.retire_missing_pages)
    if not previous and not requested:
        return generation_inputs
    if page_plan is None or options.initialize_surfaces:
        refuse("use ordinary sync with complete page ownership planning")
    committed.require_for(options.wiki_dir)
    artifacts = committed.artifacts
    if artifacts is None:
        refuse("the previous committed native projection is unavailable")
    records = dict(previous)
    old_sources = {row["owner"]["source_path"] for row in previous.values()}
    present = old_sources.intersection(inventory)
    if present and not options.preserve_semantic:
        refuse("exact revival restores the full archived body; omit --no-preserve-semantic or explicitly release first")
    if requested.intersection(inventory):
        refuse("a requested source still exists in the current inventory")
    confirm_absence(snapshot, (requested | old_sources) - present)
    owners_now = {item.owner: item for item in page_plan.transitions}
    targets = {portable_path_key(item.final_path): item for item in page_plan.transitions}
    outgoing = {item.previous_owner: item for item in page_plan.transitions if item.previous_owner is not None}
    new_sources = requested - old_sources
    with StorageReadSession(options.wiki_dir).phase() as reader:
        index = reader.read("index.md", MAX_EXPANDED_BYTES).decode("utf-8")
        remove_bound_registry(index, previous)
        for path, row in previous.items():
            owner = ManifestPageSource.from_payload(row["owner"], "historical.owner")
            if not page_matches(reader.read(path, MAX_EXPANDED_BYTES), row["page_hash"]):
                refuse(f"{path!r} differs from the enrolled predecessor page")
            if owner.source_path in present:
                item = owners_now.get(owner)
                if (not item or item.previous_owner != owner or item.source_path != path
                        or snapshot.captured_content_hashes.get(owner.source_path) != row["basis"]["source_content_hash"]):
                    refuse(f"the returning source cannot prove the original bytes and coordinate for {path!r}")
                del records[path]
            elif portable_path_key(path) in targets or owner in outgoing:
                refuse(f"a different current source claims historical page {path!r}")
        acquiring = set()
        for source in sorted(new_sources):
            retained = set()
            for path, owner in _original_owners(manifest, source).items():
                if requested_pages and path not in requested_pages:
                    continue
                moved = outgoing.get(owner)
                if moved is not None:
                    if requested_pages:
                        refuse(f"the explicitly selected page {path!r} is claimed by a live declaration")
                    original_hash = manifest.sources[source].get("hash")
                    matching_sources = [candidate for candidate in inventory
                                        if snapshot.captured_content_hashes.get(candidate) == original_hash]
                    if (is_valid_sha256(original_hash) and moved.old_path == path
                            and moved.owner != owner and moved.owner.scope == owner.scope
                            and matching_sources == [moved.owner.source_path]
                            and moved.owner.entity_name == owner.entity_name and moved.owner.occurrence == owner.occurrence):
                        continue  # One exact source-byte continuation has recorded custody.
                    refuse(f"a competing live declaration cannot prove continuation of {path!r}")
                if portable_path_key(path) in targets:
                    refuse(f"a current declaration occupies predecessor page {path!r}")
                retained.add(path)
            if not retained:
                refuse(f"{source!r} has no retained former page after verified transfers")
            acquiring.update(retained)
        if acquiring:
            originals = {path: reader.read(path, MAX_EXPANDED_BYTES) for path in sorted(acquiring)}
            records.update(predecessor_records(manifest, artifacts, originals))
    if requested_pages:
        selected = {path for path, row in records.items()
                    if path in requested_pages and row["owner"]["source_path"] in requested}
        if selected != requested_pages or {records[path]["owner"]["source_path"] for path in selected} != requested:
            refuse("the requested page allowlist must bind exactly to retained pages of every requested source")
    for path in sorted(records.keys() - previous.keys()):
        emit(f"  RETAIN historical source page: {path}")
    for path in sorted(previous.keys() - records.keys()):
        emit(f"  REVIVE historical source page: {path}")
    if any(item.path in records for item in page_plan.retained_page_repairs):
        refuse("a retained page also requires a link or content rewrite")
    result = dict(generation_inputs)
    if records:
        result[INPUT] = {"schema_version": SCHEMA, "pages": records}
        read_records(result)
    else:
        result.pop(INPUT, None)
    return result
