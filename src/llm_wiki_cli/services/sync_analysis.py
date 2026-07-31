"""Read-only source/manifest diff analysis shared by sync and lint."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from .bootstrap_runtime import (
    _module_name_from_path,
    _page_name_for_module,
    build_entity_page_map,
    build_module_page_map,
)
from .knowledge_evidence import hash_file, semantic_hash_for_file
from .sync_manifest import SyncManifest


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

    @property
    def has_changes(self) -> bool:
        return bool(
            self.new_files
            or self.changed_files
            or self.metadata_only_files
            or self.removed_files
            or self.moved_entities
            or self.renamed_entity_pages
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

    old_cls_to_files: dict[str, set[str]] = {}
    for filepath, info in manifest.sources.items():
        for class_name in info.get("entities", []):
            old_cls_to_files.setdefault(class_name, set()).add(filepath)

    new_cls_to_files: dict[str, set[str]] = {}
    for filepath, file_data in inventory.items():
        for class_record in file_data.get("classes", []):
            new_cls_to_files.setdefault(class_record["name"], set()).add(filepath)

    for class_name, old_files in old_cls_to_files.items():
        new_files = new_cls_to_files.get(class_name, set())
        if len(old_files) != 1 or len(new_files) != 1:
            continue
        old_filepath = next(iter(old_files))
        new_filepath = next(iter(new_files))
        if old_filepath != new_filepath:
            diff.moved_entities[class_name] = (old_filepath, new_filepath)

    for filepath, file_data in inventory.items():
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

    for filepath, file_data in inventory.items():
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

        entity_pages = old_info.get("entity_pages")
        for class_record in file_data.get("classes", []):
            class_name = str(class_record["name"])
            new_page = entity_page_cache.get((class_name, filepath), class_name)
            old_page = (
                str(entity_pages[class_name])
                if isinstance(entity_pages, dict) and class_name in entity_pages
                else class_name
            )
            if old_page != new_page:
                diff.renamed_entity_pages[(class_name, filepath)] = (
                    old_page,
                    new_page,
                )

    return diff


# Compatibility name retained for existing sync/lint internals.
_compute_diff = compute_sync_diff


__all__ = ["SyncDiff", "compute_sync_diff"]
