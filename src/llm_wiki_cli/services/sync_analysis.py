"""Read-only source/manifest diff analysis shared by sync and lint."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .bootstrap_runtime import (
    _module_name_from_path,
    _page_name_for_entity,
    _page_name_for_module,
    build_entity_occurrence_page_map,
    build_entity_page_map,
    build_module_page_map,
)
from .knowledge_evidence import hash_file, semantic_hash_for_file
from .sync_manifest import ManifestPageSource, SyncManifest
from .validation import is_portable_path_component, portable_path_key


EntityOwner = tuple[str, str, int]  # source path, entity name, occurrence


class SyncOwnershipError(ValueError):
    """A page cannot be safely assigned to one recorded source entity."""


def _ownership_error(owner: EntityOwner, reason: str) -> SyncOwnershipError:
    filepath, name, occurrence = owner
    return SyncOwnershipError(
        f"Entity page ownership conflict for {name!r} in {filepath!r} "
        f"(occurrence {occurrence}): {reason}. "
        "Review the manifest source mappings before syncing."
    )


@dataclass
class _RecordedEntityPages:
    pages: dict[EntityOwner, set[str]] = field(default_factory=dict)
    owners: dict[str, set[EntityOwner]] = field(default_factory=dict)

    def add(self, owner: EntityOwner, page: object, *, candidate: bool = True) -> None:
        if not isinstance(page, str) or not is_portable_path_component(page):
            raise _ownership_error(owner, "recorded page name is not portable")
        if candidate:
            self.pages.setdefault(owner, set()).add(page)
        self.owners.setdefault(portable_path_key(page), set()).add(owner)

    def resolve(self, owner: EntityOwner) -> str | None:
        candidates = self.pages.get(owner, set())
        if not candidates:
            return None
        if len(candidates) != 1:
            raise _ownership_error(
                owner, f"contradictory recorded pages {sorted(candidates)!r}"
            )
        page = next(iter(candidates))
        claims = self.owners[portable_path_key(page)]
        if claims != {owner}:
            raise _ownership_error(
                owner,
                f"page {page!r} is claimed by multiple source coordinates {sorted(claims)!r}",
            )
        return page


def _recorded_entity_pages(manifest: SyncManifest) -> _RecordedEntityPages:
    """Reconcile explicit ownership before considering any legacy fallback."""
    recorded = _RecordedEntityPages()
    memberships = {
        filepath: Counter(info.get("entities", []))
        for filepath, info in manifest.sources.items()
    }

    def add(owner: EntityOwner, page: object, *, candidate: bool = True) -> None:
        filepath, name, occurrence = owner
        info = manifest.sources.get(filepath)
        if (
            candidate
            and info is not None
            and "entities" in info
            and memberships[filepath][name] < occurrence
        ):
            raise _ownership_error(
                owner, "recorded coordinate contradicts prior source membership"
            )
        recorded.add(owner, page, candidate=candidate)

    for filepath, info in sorted(manifest.sources.items()):
        entity_pages = info.get("entity_pages")
        if isinstance(entity_pages, Mapping):
            for name, page in sorted(entity_pages.items()):
                add((filepath, name, 1), page)
        occurrences = info.get("entity_page_occurrences")
        if isinstance(occurrences, list):
            for item in occurrences:
                if not isinstance(item, Mapping):
                    raise SyncOwnershipError(
                        f"Invalid entity occurrence ownership record in {filepath!r}."
                    )
                name, occurrence = item.get("name"), item.get("occurrence")
                if (
                    not isinstance(name, str)
                    or not name
                    or type(occurrence) is not int
                    or occurrence < 1
                ):
                    raise SyncOwnershipError(
                        f"Invalid entity occurrence ownership record in {filepath!r}."
                    )
                add((filepath, name, occurrence), item.get("page"))
    # Include retained/tombstoned coordinates: their pages cannot be claimed by
    # another live owner merely because their original source has disappeared.
    for path, mapping in sorted(manifest.page_source_mappings.items()):
        if mapping.scope == "entity":
            assert mapping.entity_name is not None and mapping.occurrence is not None
            add(
                (mapping.source_path, mapping.entity_name, mapping.occurrence),
                Path(path).stem,
                candidate=path not in manifest.tombstones,
            )
    for filepath in sorted(manifest.sources):
        for name in sorted(memberships[filepath]):
            owner = (filepath, name, 1)
            if owner not in recorded.pages:
                recorded.add(owner, _page_name_for_entity(name))
    return recorded


@dataclass
class SyncDiff:
    """Categorised difference between a persisted manifest and live inventory."""

    new_files: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    metadata_only_files: list[str] = field(default_factory=list)
    unchanged_files: list[str] = field(default_factory=list)
    removed_files: list[str] = field(default_factory=list)
    moved_entities: dict[str, tuple[str, str]] = field(default_factory=dict)
    renamed_entity_pages: dict[tuple[str, str], tuple[str, str]] = field(
        default_factory=dict
    )
    renamed_module_pages: dict[str, tuple[str, str]] = field(default_factory=dict)
    renamed_entity_occurrences: dict[tuple[str, str, int], tuple[str, str]] = field(default_factory=dict)
    # Apply-only output work; it does not reclassify unchanged source files.
    missing_pages: dict[str, ManifestPageSource] = field(default_factory=dict)

    @property
    def entity_page_renames(self) -> dict[tuple[str, str, int], tuple[str, str]]:
        renames = {(name, path, 1): pages for (name, path), pages in self.renamed_entity_pages.items()}
        renames.update(self.renamed_entity_occurrences)
        return renames

    @property
    def has_changes(self) -> bool:
        return bool(
            self.new_files
            or self.changed_files
            or self.metadata_only_files
            or self.removed_files
            or self.moved_entities
            or self.renamed_entity_pages
            or self.renamed_entity_occurrences
            or self.missing_pages
            or self.renamed_module_pages
        )


def compute_sync_diff(
    manifest: SyncManifest,
    inventory: dict,
    src_dir: str,
    *,
    entity_page_cache: dict[tuple[str, str], str] | None = None,
    module_page_map: dict[str, str] | None = None,
    source_content_hashes: Mapping[str, str] | None = None,
) -> SyncDiff:
    """Compare a managed manifest with one live structural inventory."""

    diff = SyncDiff()
    recorded_pages = _recorded_entity_pages(manifest)

    old_cls_to_files: dict[str, set[str]] = {}
    old_cls_counts: Counter[str] = Counter()
    for filepath, info in manifest.sources.items():
        old_cls_counts.update(info.get("entities", []))
        for class_name in info.get("entities", []):
            old_cls_to_files.setdefault(class_name, set()).add(filepath)

    new_cls_to_files: dict[str, set[str]] = {}
    new_cls_counts: Counter[str] = Counter()
    for filepath, file_data in inventory.items():
        for class_record in file_data.get("classes", []):
            new_cls_counts[class_record["name"]] += 1
            new_cls_to_files.setdefault(class_record["name"], set()).add(filepath)

    for class_name, old_files in sorted(old_cls_to_files.items()):
        new_files = new_cls_to_files.get(class_name, set())
        if len(old_files) != 1 or len(new_files) != 1:
            continue
        old_filepath = next(iter(old_files))
        new_filepath = next(iter(new_files))
        if old_filepath != new_filepath:
            owner = (old_filepath, class_name, 1)
            recorded_pages.resolve(owner)
            if old_cls_counts[class_name] != 1 or new_cls_counts[class_name] != 1:
                raise _ownership_error(
                    owner, "multiple occurrences make the source move ambiguous"
                )
            diff.moved_entities[class_name] = (old_filepath, new_filepath)

    for filepath, file_data in sorted(inventory.items()):
        if filepath not in manifest.sources:
            diff.new_files.append(filepath)
            continue
        current_hash = (
            source_content_hashes[filepath]
            if source_content_hashes is not None
            else hash_file(Path(src_dir) / filepath)
        )
        if current_hash == manifest.sources[filepath].get("hash", ""):
            diff.unchanged_files.append(filepath)
            continue
        current_semantic_hash = semantic_hash_for_file(file_data)
        if current_semantic_hash == manifest.sources[filepath].get("semantic_hash"):
            diff.metadata_only_files.append(filepath)
        else:
            diff.changed_files.append(filepath)

    for filepath in manifest.sources:
        if filepath not in inventory:
            diff.removed_files.append(filepath)

    if entity_page_cache is None:
        entity_page_cache = build_entity_page_map(inventory)
    if module_page_map is None:
        module_page_map = build_module_page_map(inventory)

    occurrence_pages = None
    for filepath, file_data in sorted(inventory.items()):
        old_info = manifest.sources.get(filepath)
        if not old_info:
            continue
        old_module_page = str(
            old_info.get("module_page") or _module_name_from_path(filepath)
        )
        new_module_page = module_page_map.get(
            filepath,
            _page_name_for_module(filepath),
        )
        if old_module_page != new_module_page:
            diff.renamed_module_pages[filepath] = (
                old_module_page,
                new_module_page,
            )

        old_counts = Counter(old_info.get("entities", []))
        seen: dict[str, int] = defaultdict(int)
        for class_record in file_data.get("classes", []):
            class_name = str(class_record["name"])
            seen[class_name] += 1
            occurrence = seen[class_name]
            # The old module's existence is not evidence that this class existed.
            if occurrence > old_counts[class_name]:
                continue
            owner = (filepath, class_name, occurrence)
            old_page = recorded_pages.resolve(owner)
            if old_page is None:
                # Legacy manifests may have collapsed later declarations. There
                # is no supported way to infer their old pages from the name.
                continue
            if occurrence == 1:
                new_page = entity_page_cache.get((class_name, filepath), class_name)
            else:
                if occurrence_pages is None:
                    occurrence_pages = build_entity_occurrence_page_map(inventory)
                new_page = occurrence_pages[(class_name, filepath, occurrence)]
            if old_page != new_page:
                diff.renamed_entity_occurrences[(class_name, filepath, occurrence)] = (old_page, new_page)
                if occurrence == 1:
                    diff.renamed_entity_pages[(class_name, filepath)] = (old_page, new_page)

    return diff


# Compatibility name retained for existing sync/lint internals.
_compute_diff = compute_sync_diff


__all__ = ["SyncDiff", "SyncOwnershipError", "compute_sync_diff"]
