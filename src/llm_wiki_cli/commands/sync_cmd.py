"""Incremental wiki sync — update only pages whose source has changed.

Workflow:
    1. Load ``wiki_dir/.llm-wiki-manifest.json`` (error if missing — run bootstrap first).
    2. Hash every source file in the current AST inventory.
    3. Compute a diff: new / changed / unchanged / removed files, moved classes.
    4. Apply changes surgically: regenerate pages for new/changed files, add a
       deprecation warning to pages whose source was removed, skip everything else.
    5. Rebuild index.md and append a log entry if anything changed.
    6. Save the updated manifest.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Optional

from .extract_cmd import (
    InventoryResult,
    get_inventory_result,
    infer_language_from_path,
    print_inventory_failures,
    resolve_call_edges,
)
from .bootstrap_cmd import (
    _build_relationships,
    _generate_dependencies_md,
    _generate_entity_md,
    _generate_flow_md,
    _generate_index_md,
    _generate_load_order_md,
    _generate_module_md,
    _module_name_from_path,
    _page_name_for_module,
    build_entity_page_map,
    build_module_page_map,
)
from ..config import validate_path
from ..services.dependencies import analyze_dependencies
from ..services.entrypoints import build_flow, get_entry_points, read_console_scripts
from ..services.inventory_cache import (
    InventoryCacheOptions,
    InventoryCacheStats,
    format_cache_stats,
)
from ..services.io import read_md, write_md

# ── Constants ─────────────────────────────────────────────────────────────────

MANIFEST_FILENAME = ".llm-wiki-manifest.json"
MANIFEST_VERSION = 3
MAX_SYNC_AFFECTED_FILES = 50
MAX_SYNC_AFFECTED_RATIO = 0.30
MIN_SOURCES_FOR_RATIO_GUARD = 10
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_AUTO_GENERATED_RE = re.compile(r"^_Auto-generated from `.+`(?: in `.+`)?\._$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_DEPRECATION_HEADER = (
    "> ⚠️ **Stale:** Source no longer found in codebase. "
    "Run `llm-wiki lint` to audit.\n\n"
)


def _cache_options_from_args(args) -> InventoryCacheOptions:
    cache_stats = bool(getattr(args, "cache_stats", False))
    return InventoryCacheOptions(
        enabled=not bool(getattr(args, "no_cache", False)),
        rebuild=bool(getattr(args, "rebuild_cache", False)),
        cache_dir=getattr(args, "cache_dir", None),
        stats_enabled=cache_stats,
    )


def _print_cache_stats(stats: InventoryCacheStats | None, *, enabled: bool) -> None:
    if not enabled or stats is None:
        return
    for line in format_cache_stats(stats):
        print(line)


def _is_valid_manifest_hash(value: object) -> bool:
    return isinstance(value, str) and bool(_HASH_RE.match(value))


def _invalid_manifest_hash_paths(manifest: "SyncManifest") -> list[str]:
    return [
        filepath
        for filepath, info in manifest.sources.items()
        if not _is_valid_manifest_hash(info.get("hash"))
    ]


def _build_manifest_from_inventory(
    inventory: dict,
    src_dir: str,
    *,
    entity_page_cache: dict[tuple[str, str], str] | None = None,
    module_page_map: dict[str, str] | None = None,
) -> "SyncManifest":
    if entity_page_cache is None:
        _, _, entity_page_cache = _collision_maps(inventory, src_dir)
    if module_page_map is None:
        module_page_map = build_module_page_map(inventory)
    return SyncManifest.build_from_inventory(
        inventory,
        src_dir,
        entity_page_cache,
        module_page_map,
    )


def _normalize_md(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _write_md_if_changed(path: Path, text: str) -> str:
    """Write markdown only when content changes.

    Returns ``created``, ``updated``, or ``unchanged``.
    """
    normalized = _normalize_md(text)
    if path.exists():
        existing = _normalize_md(read_md(path))
        if existing == normalized:
            return "unchanged"
        write_md(path, normalized)
        return "updated"
    write_md(path, normalized)
    return "created"


def _without_line_metadata(value):
    """Return inventory data with line-only metadata removed."""
    if isinstance(value, dict):
        return {
            key: _without_line_metadata(item)
            for key, item in sorted(value.items())
            if key != "line"
        }
    if isinstance(value, list):
        return [_without_line_metadata(item) for item in value]
    return value


def _semantic_hash_for_file(file_data: dict) -> str:
    """Fingerprint extracted source semantics while ignoring line shifts."""
    payload = _without_line_metadata(file_data)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _first_doc_line(info: dict) -> str:
    docstring = info.get("docstring", "")
    return docstring.split("\n")[0] if docstring else "—"


def _generated_semantics_for_file(filepath: str, file_data: dict) -> dict:
    """Return the generated description fields that sync may later preserve over."""
    module_docstring = file_data.get("module_docstring", "")
    module_description = module_docstring or f"_Auto-generated from `{filepath}`._"
    return {
        "module": {
            "description": module_description,
            "classes": {
                cls["name"]: _first_doc_line(cls)
                for cls in file_data.get("classes", [])
            },
            "functions": {
                fn["name"]: _first_doc_line(fn) for fn in file_data.get("functions", [])
            },
        },
        "entities": {
            cls["name"]: {
                "description": cls.get("docstring", "")
                or f"_Auto-generated from `{cls['name']}` in `{filepath}`._",
                "attributes": {attr["name"]: "—" for attr in cls.get("attributes", [])},
                "methods": {
                    method["name"]: _first_doc_line(method)
                    for method in cls.get("methods", [])
                },
            }
            for cls in file_data.get("classes", [])
        },
    }


def _section_bounds(lines: list[str], heading: str) -> tuple[int, int, int] | None:
    """Return ``(heading_index, body_start, body_end)`` for a level-2 heading."""
    target = heading.casefold()
    for i, line in enumerate(lines):
        match = _HEADING_RE.match(line.strip())
        if not match:
            continue
        level = len(match.group(1))
        title = match.group(2).strip().casefold()
        if level != 2 or title != target:
            continue
        end = len(lines)
        for j in range(i + 1, len(lines)):
            next_match = _HEADING_RE.match(lines[j].strip())
            if next_match and len(next_match.group(1)) <= level:
                end = j
                break
        return i, i + 1, end
    return None


def _trim_blank_lines(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and lines[start].strip() == "":
        start += 1
    while end > start and lines[end - 1].strip() == "":
        end -= 1
    return lines[start:end]


def _section_body(markdown: str, heading: str) -> str | None:
    lines = _normalize_md(markdown).splitlines()
    bounds = _section_bounds(lines, heading)
    if not bounds:
        return None
    _, start, end = bounds
    body_lines = _trim_blank_lines(lines[start:end])
    return "\n".join(body_lines).strip()


def _replace_section_body(markdown: str, heading: str, body: str) -> str:
    lines = _normalize_md(markdown).splitlines()
    bounds = _section_bounds(lines, heading)
    if not bounds:
        return markdown
    heading_idx, _, end = bounds
    replacement = [""] + body.splitlines() + [""]
    return "\n".join(lines[: heading_idx + 1] + replacement + lines[end:])


def _is_placeholder_description(value: str | None) -> bool:
    if value is None:
        return True
    stripped = value.strip()
    if not stripped or stripped in {"—", "-"}:
        return True
    if _AUTO_GENERATED_RE.match(stripped):
        return True
    return False


def _should_preserve_semantic_value(
    existing: str | None,
    generated: str | None,
    old_generated: str | None,
) -> bool:
    if _is_placeholder_description(existing):
        return False
    existing_stripped = (existing or "").strip()
    generated_stripped = (generated or "").strip()
    if old_generated is None:
        return existing_stripped != generated_stripped
    old_stripped = old_generated.strip()
    if existing_stripped == old_stripped:
        return False
    return existing_stripped != generated_stripped


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def _format_table_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def _is_table_separator(cells: list[str]) -> bool:
    if not cells:
        return False
    return all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def _semantic_table_key(cell: str) -> str:
    key = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cell)
    key = key.replace("`", "").replace("*", "")
    return key.strip()


def _table_description_cells(markdown: str, heading: str) -> dict[str, str]:
    lines = _normalize_md(markdown).splitlines()
    bounds = _section_bounds(lines, heading)
    if not bounds:
        return {}
    _, start, end = bounds

    for i in range(start, end):
        headers = _split_table_row(lines[i])
        if not headers or "Description" not in headers:
            continue
        desc_idx = headers.index("Description")
        row_start = i + 1
        if row_start < end and _is_table_separator(_split_table_row(lines[row_start])):
            row_start += 1

        descriptions: dict[str, str] = {}
        for row_idx in range(row_start, end):
            row = _split_table_row(lines[row_idx])
            if not row:
                break
            if len(row) <= desc_idx:
                continue
            key = _semantic_table_key(row[0])
            description = row[desc_idx].strip()
            if key and not _is_placeholder_description(description):
                descriptions[key] = description
        return descriptions
    return {}


def _preserve_table_description_cells(
    markdown: str,
    heading: str,
    descriptions: dict[str, str],
    old_descriptions: dict[str, str] | None = None,
) -> tuple[str, int]:
    if not descriptions:
        return markdown, 0

    lines = _normalize_md(markdown).splitlines()
    bounds = _section_bounds(lines, heading)
    if not bounds:
        return markdown, 0
    _, start, end = bounds

    preserved = 0
    for i in range(start, end):
        headers = _split_table_row(lines[i])
        if not headers or "Description" not in headers:
            continue
        desc_idx = headers.index("Description")
        row_start = i + 1
        if row_start < end and _is_table_separator(_split_table_row(lines[row_start])):
            row_start += 1

        for row_idx in range(row_start, end):
            row = _split_table_row(lines[row_idx])
            if not row:
                break
            if len(row) <= desc_idx:
                continue
            key = _semantic_table_key(row[0])
            existing_description = descriptions.get(key)
            old_description = (old_descriptions or {}).get(key)
            if not _should_preserve_semantic_value(
                existing_description,
                row[desc_idx],
                old_description,
            ):
                continue
            row[desc_idx] = existing_description
            lines[row_idx] = _format_table_row(row)
            preserved += 1
        break

    if preserved == 0:
        return markdown, 0
    updated = "\n".join(lines)
    if markdown.endswith("\n"):
        updated += "\n"
    return updated, preserved


@dataclass
class SemanticMergeResult:
    text: str
    preserved: int = 0


def _merge_semantic_markdown(
    existing: str,
    generated: str,
    table_headings: tuple[str, ...],
    *,
    old_description: str | None = None,
    old_table_descriptions: dict[str, dict[str, str]] | None = None,
) -> SemanticMergeResult:
    """Preserve human-written semantic fields in regenerated wiki markdown."""
    merged = _normalize_md(generated)
    preserved = 0

    existing_description = _section_body(existing, "Description")
    generated_description = _section_body(generated, "Description")
    if _should_preserve_semantic_value(
        existing_description,
        generated_description,
        old_description,
    ):
        merged = _replace_section_body(merged, "Description", existing_description)
        preserved += 1

    for heading in table_headings:
        descriptions = _table_description_cells(existing, heading)
        merged, table_preserved = _preserve_table_description_cells(
            merged,
            heading,
            descriptions,
            (old_table_descriptions or {}).get(heading),
        )
        preserved += table_preserved

    return SemanticMergeResult(merged, preserved)


def _merge_entity_semantics(
    existing: str,
    generated: str,
    old_semantics: dict | None = None,
) -> SemanticMergeResult:
    old_semantics = old_semantics or {}
    return _merge_semantic_markdown(
        existing,
        generated,
        ("Attributes", "Methods"),
        old_description=old_semantics.get("description"),
        old_table_descriptions={
            "Attributes": old_semantics.get("attributes", {}),
            "Methods": old_semantics.get("methods", {}),
        },
    )


def _merge_module_semantics(
    existing: str,
    generated: str,
    old_semantics: dict | None = None,
) -> SemanticMergeResult:
    old_semantics = old_semantics or {}
    return _merge_semantic_markdown(
        existing,
        generated,
        ("Classes", "Functions"),
        old_description=old_semantics.get("description"),
        old_table_descriptions={
            "Classes": old_semantics.get("classes", {}),
            "Functions": old_semantics.get("functions", {}),
        },
    )


# ── Manifest ──────────────────────────────────────────────────────────────────


@dataclass
class SyncManifest:
    """Persistent record of what the wiki was generated from.

    Schema v2::

        {
            "version": 2,
            "sources": {
                "src/models.py": {
                    "hash": "sha256:<hex>",
                    "semantic_hash": "sha256:<hex>",
                    "generated_semantics": {
                        "module": {
                            "description": "...",
                            "classes": {"User": "..."},
                            "functions": {}
                        },
                        "entities": {
                            "User": {
                                "description": "...",
                                "attributes": {"name": "—"},
                                "methods": {}
                            }
                        }
                    },
                    "language": "python",
                    "entities": ["User", "Role"],
                    "entity_pages": {"User": "User", "Role": "Role"},
                    "module_page": "models"
                }
            }
        }
    """

    sources: dict[str, dict] = field(default_factory=dict)

    # ── Persistence ───────────────────────────────────────────────────────────

    @classmethod
    def load(cls, wiki_dir: Path) -> "SyncManifest":
        """Load manifest from *wiki_dir*; raise ``FileNotFoundError`` if absent."""
        manifest_path = wiki_dir / MANIFEST_FILENAME
        if not manifest_path.exists():
            raise FileNotFoundError(manifest_path)
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        sources = data.get("sources", {})
        for filepath, info in sources.items():
            if "language" not in info:
                info["language"] = infer_language_from_path(filepath)
        return cls(sources=sources)

    def save(self, wiki_dir: Path) -> None:
        """Write manifest to *wiki_dir* atomically (write + rename)."""
        manifest_path = wiki_dir / MANIFEST_FILENAME
        tmp_path = manifest_path.with_suffix(".json.tmp")
        payload = json.dumps(
            {"version": MANIFEST_VERSION, "sources": self.sources},
            indent=2,
            sort_keys=True,
        )
        tmp_path.write_text(payload, encoding="utf-8")
        tmp_path.replace(manifest_path)

    # ── Factory ───────────────────────────────────────────────────────────────

    @classmethod
    def build_from_inventory(
        cls,
        inventory: dict,
        src_dir: str,
        entity_page_cache: dict[tuple[str, str], str],
        module_page_map: dict[str, str],
    ) -> "SyncManifest":
        """Create a manifest that reflects the current inventory state."""
        sources: dict[str, dict] = {}
        for filepath, file_data in inventory.items():
            sources[filepath] = {
                "hash": _hash_file(Path(src_dir) / filepath),
                "semantic_hash": _semantic_hash_for_file(file_data),
                "generated_semantics": _generated_semantics_for_file(
                    filepath, file_data
                ),
                "language": file_data.get("language")
                or infer_language_from_path(filepath),
                "entities": [c["name"] for c in file_data.get("classes", [])],
                "entity_pages": {
                    c["name"]: entity_page_cache.get((c["name"], filepath), c["name"])
                    for c in file_data.get("classes", [])
                },
                "module_page": module_page_map.get(
                    filepath, _module_name_from_path(filepath)
                ),
            }
        return cls(sources=sources)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _hash_file(path: Path) -> str:
    """Return a ``"sha256:<hexdigest>"`` fingerprint of *path*'s raw bytes.

    If the file cannot be read (deleted between inventory scan and hash)
    return an empty sentinel so the caller treats it as changed.
    """
    try:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        return f"sha256:{digest}"
    except OSError:
        return ""


# ── Diff ──────────────────────────────────────────────────────────────────────


@dataclass
class SyncDiff:
    """Categorised difference between the persisted manifest and live inventory."""

    new_files: list[str] = field(default_factory=list)
    changed_files: list[str] = field(default_factory=list)
    metadata_only_files: list[str] = field(default_factory=list)
    unchanged_files: list[str] = field(default_factory=list)
    removed_files: list[str] = field(default_factory=list)
    # {class_name: (old_filepath, new_filepath)}
    moved_entities: dict[str, tuple[str, str]] = field(default_factory=dict)
    # {(class_name, filepath): (old_page_name, new_page_name)}
    renamed_entity_pages: dict[tuple[str, str], tuple[str, str]] = field(
        default_factory=dict
    )
    # {filepath: (old_page_name, new_page_name)}
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


def _affected_source_files(diff: SyncDiff) -> set[str]:
    affected = (
        set(diff.new_files)
        | set(diff.changed_files)
        | set(diff.metadata_only_files)
        | set(diff.removed_files)
    )
    for old_path, new_path in diff.moved_entities.values():
        affected.add(old_path)
        affected.add(new_path)
    for _, filepath in diff.renamed_entity_pages:
        affected.add(filepath)
    affected.update(diff.renamed_module_pages)
    return affected


def _large_diff_message(diff: SyncDiff, manifest: SyncManifest) -> str | None:
    affected_count = len(_affected_source_files(diff))
    manifest_count = len(manifest.sources)
    if affected_count > MAX_SYNC_AFFECTED_FILES:
        return (
            f"sync would affect {affected_count} source file(s), "
            f"which exceeds the safety limit of {MAX_SYNC_AFFECTED_FILES}."
        )
    if manifest_count >= MIN_SOURCES_FOR_RATIO_GUARD:
        affected_ratio = affected_count / manifest_count
        if affected_ratio > MAX_SYNC_AFFECTED_RATIO:
            percent = int(affected_ratio * 100)
            limit_percent = int(MAX_SYNC_AFFECTED_RATIO * 100)
            return (
                f"sync would affect {affected_count} of {manifest_count} manifest source file(s) "
                f"({percent}%), which exceeds the {limit_percent}% safety limit."
            )
    return None


def _compute_diff(
    manifest: SyncManifest,
    inventory: dict,
    src_dir: str,
    *,
    entity_page_cache: dict[tuple[str, str], str] | None = None,
    module_page_map: dict[str, str] | None = None,
) -> SyncDiff:
    """Compare *manifest* against the live *inventory*.

    Move detection: a class that appears in the manifest under one filepath
    but now lives in a *different* filepath is considered moved rather than
    deleted+created.  Its source-file hash is therefore refreshed from the
    *new* filepath.
    """
    diff = SyncDiff()

    # Build reverse lookups. Keep sets so duplicate class names do not collapse
    # into false moves when a new same-named entity appears.
    old_cls_to_files: dict[str, set[str]] = {}
    for fp, info in manifest.sources.items():
        for cls_name in info.get("entities", []):
            old_cls_to_files.setdefault(cls_name, set()).add(fp)

    new_cls_to_files: dict[str, set[str]] = {}
    for fp, file_data in inventory.items():
        for cls in file_data.get("classes", []):
            new_cls_to_files.setdefault(cls["name"], set()).add(fp)

    # Detect moves only when the entity name is unambiguous before and after.
    # If both old and new paths still contain the same class name, this is a
    # naming collision, not a move.
    for cls_name, old_files in old_cls_to_files.items():
        new_files = new_cls_to_files.get(cls_name, set())
        if len(old_files) == 1 and len(new_files) == 1:
            old_fp = next(iter(old_files))
            new_fp = next(iter(new_files))
        else:
            continue
        if old_fp != new_fp:
            diff.moved_entities[cls_name] = (old_fp, new_fp)

    # Categorise each file in the new inventory
    for filepath, file_data in inventory.items():
        if filepath not in manifest.sources:
            diff.new_files.append(filepath)
        else:
            # Re-hash to detect content changes
            current_hash = _hash_file(Path(src_dir) / filepath)
            if current_hash != manifest.sources[filepath].get("hash", ""):
                current_semantic_hash = _semantic_hash_for_file(file_data)
                if current_semantic_hash == manifest.sources[filepath].get(
                    "semantic_hash"
                ):
                    diff.metadata_only_files.append(filepath)
                else:
                    diff.changed_files.append(filepath)
            else:
                diff.unchanged_files.append(filepath)

    # Detect removals: in manifest but not in new inventory
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
        new_module_page = module_page_map.get(filepath, _page_name_for_module(filepath))
        if old_module_page != new_module_page:
            diff.renamed_module_pages[filepath] = (old_module_page, new_module_page)

        entity_pages = old_info.get("entity_pages")
        for cls in file_data.get("classes", []):
            cls_name = cls["name"]
            new_page = entity_page_cache.get((cls_name, filepath), cls_name)
            old_page = (
                str(entity_pages[cls_name])
                if isinstance(entity_pages, dict) and cls_name in entity_pages
                else cls_name
            )
            if old_page != new_page:
                diff.renamed_entity_pages[(cls_name, filepath)] = (old_page, new_page)

    return diff


# ── Apply ─────────────────────────────────────────────────────────────────────


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    metadata_only: int = 0
    skipped: int = 0
    deprecated: int = 0
    preserved_semantic: int = 0


def _collision_maps(
    inventory: dict, src_dir: str
) -> tuple[set[str], set[str], dict[tuple[str, str], str]]:
    """Return (colliding_stems, colliding_cls, entity_page_name_cache).

    Uses :func:`build_entity_page_map` for collision-aware entity names.
    The first two sets are retained for API compatibility but are no
    longer consumed directly.
    """
    entity_page_cache = build_entity_page_map(inventory)
    return set(), set(), entity_page_cache


@dataclass(frozen=True)
class _ApplyDiffContext:
    wiki_dir: Path
    inventory: dict
    manifest: SyncManifest
    entity_page_cache: dict[tuple[str, str], str]
    module_page_map: dict[str, str]
    relationships: dict
    metadata_only_files: set[str]
    current_entity_pages: set[str]
    current_module_pages: set[str]
    preserve_semantic: bool


def _target_entities_for_diff(diff: SyncDiff, inventory: dict) -> set[tuple[str, str]]:
    target_entities = {
        (cls["name"], filepath)
        for filepath in diff.new_files + diff.changed_files + diff.metadata_only_files
        if filepath in inventory
        for cls in inventory[filepath].get("classes", [])
    }
    for cls_name, (_, new_path) in diff.moved_entities.items():
        if new_path in inventory:
            target_entities.add((cls_name, new_path))
    target_entities.update(diff.renamed_entity_pages)
    for filepath in diff.renamed_module_pages:
        if filepath in inventory:
            for cls in inventory[filepath].get("classes", []):
                target_entities.add((cls["name"], filepath))
    return target_entities


def _relationships_for_targets(
    inventory: dict,
    module_page_map: dict[str, str],
    target_entities: set[tuple[str, str]],
) -> dict:
    if not target_entities:
        return {}
    print(
        f"Building relationships for {len(target_entities)} affected entity target(s)...",
        flush=True,
    )
    relationships = _build_relationships(
        inventory,
        module_page_map,
        target_entities=target_entities,
    )
    print(
        f"Built affected relationships: {sum(len(v) for v in relationships.values())}.",
        flush=True,
    )
    return relationships


def _refresh_files_for_diff(diff: SyncDiff) -> list[str]:
    return list(
        dict.fromkeys(
            diff.new_files
            + diff.changed_files
            + diff.metadata_only_files
            + [filepath for _, filepath in diff.renamed_entity_pages]
            + list(diff.renamed_module_pages)
        )
    )


def _file_entity_page_map(
    filepath: str,
    file_data: dict,
    entity_page_cache: dict[tuple[str, str], str],
) -> dict[str, str]:
    return {
        cls["name"]: entity_page_cache[(cls["name"], filepath)]
        for cls in file_data.get("classes", [])
    }


def _move_renamed_entity_page(
    wiki_dir: Path,
    rename: tuple[str, str] | None,
    current_entity_pages: set[str],
) -> None:
    if not rename:
        return
    old_page_name, new_page_name = rename
    old_entity_path = wiki_dir / "entities" / f"{old_page_name}.md"
    new_entity_path = wiki_dir / "entities" / f"{new_page_name}.md"
    if old_entity_path == new_entity_path or not old_entity_path.exists():
        return
    if not new_entity_path.exists():
        old_entity_path.replace(new_entity_path)
        print(f"  RENAME entity: {old_page_name} -> {new_page_name}")
    elif old_page_name not in current_entity_pages:
        old_entity_path.unlink()
        print(f"  REMOVE stale entity page: {old_page_name}")


def _move_renamed_module_page(
    wiki_dir: Path,
    rename: tuple[str, str] | None,
    current_module_pages: set[str],
) -> None:
    if not rename:
        return
    old_page_name, new_page_name = rename
    old_module_path = wiki_dir / "modules" / f"{old_page_name}.md"
    new_module_path = wiki_dir / "modules" / f"{new_page_name}.md"
    if old_module_path == new_module_path or not old_module_path.exists():
        return
    if not new_module_path.exists():
        old_module_path.replace(new_module_path)
        print(f"  RENAME module: {old_page_name} -> {new_page_name}")
    elif old_page_name not in current_module_pages:
        old_module_path.unlink()
        print(f"  REMOVE stale module page: {old_page_name}")


def _record_page_write(
    result: SyncResult,
    page_kind: str,
    page_name: str,
    write_state: str,
    *,
    metadata_only: bool,
) -> None:
    if write_state == "created":
        result.created += 1
        print(f"  CREATE {page_kind}: {page_name}")
    elif write_state == "updated":
        if metadata_only:
            result.metadata_only += 1
            print(f"  METADATA {page_kind}: {page_name}")
        else:
            result.updated += 1
            print(f"  UPDATE {page_kind}: {page_name}")
    else:
        result.skipped += 1
        print(f"  SKIP {page_kind} (unchanged): {page_name}")


def _merge_entity_page(
    ctx: _ApplyDiffContext,
    entity_path: Path,
    generated: str,
    old_generated_semantics: dict,
    cls_name: str,
    result: SyncResult,
) -> SemanticMergeResult:
    merge_result = SemanticMergeResult(generated)
    if ctx.preserve_semantic and entity_path.exists():
        old_entity_semantics = (
            old_generated_semantics.get("entities", {}).get(cls_name)
            if isinstance(old_generated_semantics, dict)
            else None
        )
        merge_result = _merge_entity_semantics(
            read_md(entity_path),
            generated,
            old_entity_semantics,
        )
        result.preserved_semantic += merge_result.preserved
    return merge_result


def _merge_module_page(
    ctx: _ApplyDiffContext,
    module_path: Path,
    generated: str,
    old_generated_semantics: dict,
    result: SyncResult,
) -> SemanticMergeResult:
    merge_result = SemanticMergeResult(generated)
    if ctx.preserve_semantic and module_path.exists():
        old_module_semantics = (
            old_generated_semantics.get("module")
            if isinstance(old_generated_semantics, dict)
            else None
        )
        merge_result = _merge_module_semantics(
            read_md(module_path),
            generated,
            old_module_semantics,
        )
        result.preserved_semantic += merge_result.preserved
    return merge_result


def _apply_entity_page(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
    filepath: str,
    cls: dict,
    mod_page_name: str,
    old_generated_semantics: dict,
    file_entity_page_map: dict[str, str],
) -> None:
    entity_page_name = file_entity_page_map[cls["name"]]
    entity_path = ctx.wiki_dir / "entities" / f"{entity_page_name}.md"
    rename = diff.renamed_entity_pages.get((cls["name"], filepath))
    _move_renamed_entity_page(ctx.wiki_dir, rename, ctx.current_entity_pages)

    generated = _generate_entity_md(cls, filepath, ctx.relationships, mod_page_name)
    merge_result = _merge_entity_page(
        ctx,
        entity_path,
        generated,
        old_generated_semantics,
        cls["name"],
        result,
    )
    write_state = _write_md_if_changed(entity_path, merge_result.text)
    _record_page_write(
        result,
        "entity",
        entity_page_name,
        write_state,
        metadata_only=filepath in ctx.metadata_only_files,
    )


def _apply_module_page(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
    filepath: str,
    file_data: dict,
    mod_page_name: str,
    old_generated_semantics: dict,
    file_entity_page_map: dict[str, str],
) -> None:
    module_path = ctx.wiki_dir / "modules" / f"{mod_page_name}.md"
    _move_renamed_module_page(
        ctx.wiki_dir,
        diff.renamed_module_pages.get(filepath),
        ctx.current_module_pages,
    )

    generated = _generate_module_md(filepath, file_data, file_entity_page_map)
    merge_result = _merge_module_page(
        ctx, module_path, generated, old_generated_semantics, result
    )
    write_state = _write_md_if_changed(module_path, merge_result.text)
    _record_page_write(
        result,
        "module",
        mod_page_name,
        write_state,
        metadata_only=filepath in ctx.metadata_only_files,
    )


def _apply_refreshed_file_pages(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
    refresh_files: list[str],
) -> None:
    for filepath in refresh_files:
        file_data = ctx.inventory[filepath]
        mod_page_name = ctx.module_page_map.get(
            filepath, _page_name_for_module(filepath)
        )
        old_generated_semantics = ctx.manifest.sources.get(filepath, {}).get(
            "generated_semantics", {}
        )
        file_entity_page_map = _file_entity_page_map(
            filepath, file_data, ctx.entity_page_cache
        )

        for cls in file_data.get("classes", []):
            _apply_entity_page(
                ctx,
                diff,
                result,
                filepath,
                cls,
                mod_page_name,
                old_generated_semantics,
                file_entity_page_map,
            )
        _apply_module_page(
            ctx,
            diff,
            result,
            filepath,
            file_data,
            mod_page_name,
            old_generated_semantics,
            file_entity_page_map,
        )


def _record_unchanged_file_skips(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
    refresh_files: list[str],
) -> None:
    refresh_file_set = set(refresh_files)
    unchanged_files = [
        filepath
        for filepath in diff.unchanged_files
        if filepath not in refresh_file_set
    ]
    unchanged_pages = sum(
        1 + len(ctx.inventory[filepath].get("classes", []))
        for filepath in unchanged_files
        if filepath in ctx.inventory
    )
    result.skipped += unchanged_pages
    if unchanged_files:
        print(
            f"  SKIP unchanged source files: {len(unchanged_files)} "
            f"file(s), {unchanged_pages} generated page(s)"
        )


def _deprecate_existing_page(
    path: Path,
    result: SyncResult,
    page_kind: str,
    page_name: str,
) -> None:
    if not path.exists():
        return
    text = read_md(path)
    if _DEPRECATION_HEADER in text:
        return
    write_state = _write_md_if_changed(path, _DEPRECATION_HEADER + text)
    if write_state != "unchanged":
        result.deprecated += 1
        print(f"  DEPRECATE {page_kind}: {page_name}")


def _deprecate_removed_entities(
    wiki_dir: Path,
    filepath: str,
    old_info: dict,
    result: SyncResult,
) -> None:
    for cls_name in old_info.get("entities", []):
        entity_page_name = _removed_entity_page_name(
            wiki_dir, cls_name, filepath, old_info
        )
        if entity_page_name:
            entity_path = wiki_dir / "entities" / f"{entity_page_name}.md"
            _deprecate_existing_page(entity_path, result, "entity", entity_page_name)


def _deprecate_removed_module(
    wiki_dir: Path,
    filepath: str,
    old_info: dict,
    result: SyncResult,
) -> None:
    old_mod_page = old_info.get("module_page", _module_name_from_path(filepath))
    mod_page_path = wiki_dir / "modules" / f"{old_mod_page}.md"
    _deprecate_existing_page(mod_page_path, result, "module", mod_page_path.stem)


def _deprecate_removed_files(
    ctx: _ApplyDiffContext,
    diff: SyncDiff,
    result: SyncResult,
) -> None:
    for filepath in diff.removed_files:
        old_info = ctx.manifest.sources[filepath]
        _deprecate_removed_entities(ctx.wiki_dir, filepath, old_info, result)
        _deprecate_removed_module(ctx.wiki_dir, filepath, old_info, result)


def _apply_diff(
    diff: SyncDiff,
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    manifest: SyncManifest,
    *,
    entity_page_cache: dict[tuple[str, str], str] | None = None,
    module_page_map: dict[str, str] | None = None,
    preserve_semantic: bool = True,
) -> SyncResult:
    """Regenerate pages for new/changed files, deprecate pages for removed files."""
    if entity_page_cache is None:
        _, _, entity_page_cache = _collision_maps(inventory, src_dir)
    if module_page_map is None:
        module_page_map = build_module_page_map(inventory)

    target_entities = _target_entities_for_diff(diff, inventory)
    relationships = _relationships_for_targets(
        inventory, module_page_map, target_entities
    )
    refresh_files = _refresh_files_for_diff(diff)
    result = SyncResult()
    ctx = _ApplyDiffContext(
        wiki_dir=wiki_dir,
        inventory=inventory,
        manifest=manifest,
        entity_page_cache=entity_page_cache,
        module_page_map=module_page_map,
        relationships=relationships,
        metadata_only_files=set(diff.metadata_only_files),
        current_entity_pages=set(entity_page_cache.values()),
        current_module_pages=set(module_page_map.values()),
        preserve_semantic=preserve_semantic,
    )

    # ── New + changed + renamed files ──────────────────────────────────────────
    print("Applying wiki page changes...", flush=True)
    _apply_refreshed_file_pages(ctx, diff, result, refresh_files)

    # ── Unchanged files ────────────────────────────────────────────────────────
    _record_unchanged_file_skips(ctx, diff, result, refresh_files)

    # ── Removed files ──────────────────────────────────────────────────────────
    _deprecate_removed_files(ctx, diff, result)

    print("Applied wiki page changes.", flush=True)
    return result


def _removed_entity_page_name(
    wiki_dir: Path,
    cls_name: str,
    filepath: str,
    old_info: dict,
) -> Optional[str]:
    """Resolve the existing entity page for a class whose source file was removed."""
    entity_pages = old_info.get("entity_pages", {})
    candidates: list[str] = []
    if isinstance(entity_pages, dict) and entity_pages.get(cls_name):
        candidates.append(str(entity_pages[cls_name]))

    old_mod_page = old_info.get("module_page", _module_name_from_path(filepath))
    if old_mod_page:
        candidates.append(f"{old_mod_page}_{cls_name}")
    candidates.append(cls_name)

    seen: set[str] = set()
    for page_name in candidates:
        if page_name in seen:
            continue
        seen.add(page_name)
        if (wiki_dir / "entities" / f"{page_name}.md").exists():
            return page_name

    matches = sorted((wiki_dir / "entities").glob(f"*_{cls_name}.md"))
    return matches[0].stem if matches else None


# ── run ───────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class _SyncRunOptions:
    src_dir: str
    wiki_dir: Path
    cache_options: InventoryCacheOptions
    cache_stats_enabled: bool
    parallel_jobs: int
    force: bool
    preserve_semantic: bool


@dataclass(frozen=True)
class _SyncPageMaps:
    module_page_map: dict[str, str]
    entity_page_cache: dict[tuple[str, str], str]


def _sync_run_options_from_args(args) -> _SyncRunOptions:
    src_dir: str = getattr(args, "src_dir", ".")
    wiki_dir = Path(getattr(args, "wiki_dir", "docs/llm_wiki"))
    cache_options = _cache_options_from_args(args)
    cache_stats_enabled = bool(getattr(args, "cache_stats", False))
    parallel_jobs = getattr(args, "jobs", 1)
    force = bool(getattr(args, "force", False))
    preserve_semantic = not bool(getattr(args, "no_preserve_semantic", False))
    validate_path(src_dir, "--src-dir")
    validate_path(str(wiki_dir), "--wiki-dir")

    return _SyncRunOptions(
        src_dir=src_dir,
        wiki_dir=wiki_dir,
        cache_options=cache_options,
        cache_stats_enabled=cache_stats_enabled,
        parallel_jobs=parallel_jobs,
        force=force,
        preserve_semantic=preserve_semantic,
    )


def _load_or_seed_manifest(options: _SyncRunOptions) -> Optional["SyncManifest"]:
    try:
        return SyncManifest.load(options.wiki_dir)
    except FileNotFoundError:
        if (options.wiki_dir / "index.md").exists():
            _seed_manifest_from_existing_wiki(options)
            return None
        print(
            f"Error: no sync manifest found at {options.wiki_dir / MANIFEST_FILENAME}.\n"
            "Run `llm-wiki bootstrap` first to create the initial wiki and manifest.",
            file=sys.stderr,
        )
        sys.exit(1)


def _seed_manifest_from_existing_wiki(options: _SyncRunOptions) -> None:
    print(
        "No sync manifest found — seeding from current source state.\n"
        "Existing wiki pages will NOT be modified.\n"
        "Future `llm-wiki sync` runs will update incrementally.\n"
    )
    inventory_result = _extract_current_inventory(options)
    inventory = inventory_result.inventory

    if not inventory:
        print("No supported source files found; manifest not written.")
        _print_cache_stats(
            inventory_result.cache_stats, enabled=options.cache_stats_enabled
        )
        return

    seed = _build_manifest_from_inventory(inventory, options.src_dir)
    seed.save(options.wiki_dir)
    print(f"Manifest written to {options.wiki_dir / MANIFEST_FILENAME}")
    _print_cache_stats(
        inventory_result.cache_stats, enabled=options.cache_stats_enabled
    )


def _extract_current_inventory(options: _SyncRunOptions) -> InventoryResult:
    print("Extracting current source inventory...")
    inventory_result = get_inventory_result(
        options.src_dir,
        deep=True,
        cache_options=options.cache_options,
        parallel_jobs=options.parallel_jobs,
    )
    if inventory_result.failed:
        print_inventory_failures(inventory_result)
        sys.exit(1)
    print(
        f"Extracted current source inventory: {len(inventory_result.inventory)} file(s)."
    )
    return inventory_result


def _finish_if_empty_inventory(
    options: _SyncRunOptions,
    manifest: "SyncManifest",
    inventory_result: InventoryResult,
) -> bool:
    if inventory_result.inventory or manifest.sources:
        return False
    print("No supported source files with classes or functions found.")
    _print_cache_stats(
        inventory_result.cache_stats, enabled=options.cache_stats_enabled
    )
    return True


def _repair_manifest_if_needed(
    options: _SyncRunOptions,
    manifest: "SyncManifest",
    inventory: dict,
    inventory_result: InventoryResult,
) -> bool:
    invalid_hash_paths = _invalid_manifest_hash_paths(manifest)
    if not invalid_hash_paths:
        return False

    repaired = _build_manifest_from_inventory(inventory, options.src_dir)
    repaired.save(options.wiki_dir)
    print(
        f"Sync manifest repaired: {len(invalid_hash_paths)} source entr"
        f"{'y has' if len(invalid_hash_paths) == 1 else 'ies have'} invalid or missing hashes."
    )
    print(
        "Wiki pages were not modified. Run `llm-wiki sync` again to apply source changes."
    )
    _print_cache_stats(
        inventory_result.cache_stats, enabled=options.cache_stats_enabled
    )
    return True


def _prepare_sync_page_maps(inventory: dict) -> _SyncPageMaps:
    print("Preparing sync page maps...", flush=True)
    page_maps = _SyncPageMaps(
        module_page_map=build_module_page_map(inventory),
        entity_page_cache=build_entity_page_map(inventory),
    )
    print("Prepared sync page maps.", flush=True)
    return page_maps


def _compute_sync_diff(
    manifest: "SyncManifest",
    inventory: dict,
    options: _SyncRunOptions,
    page_maps: _SyncPageMaps,
) -> "SyncDiff":
    return _compute_diff(
        manifest,
        inventory,
        options.src_dir,
        entity_page_cache=page_maps.entity_page_cache,
        module_page_map=page_maps.module_page_map,
    )


def _finish_if_no_changes(
    options: _SyncRunOptions,
    diff: "SyncDiff",
    inventory_result: InventoryResult,
) -> bool:
    if diff.has_changes:
        return False
    print("Wiki is up to date.")
    _print_cache_stats(
        inventory_result.cache_stats, enabled=options.cache_stats_enabled
    )
    return True


def _exit_if_large_unforced_diff(
    options: _SyncRunOptions,
    diff: "SyncDiff",
    manifest: "SyncManifest",
    inventory_result: InventoryResult,
) -> None:
    large_diff_message = _large_diff_message(diff, manifest)
    if not large_diff_message or options.force:
        return

    print(f"Error: {large_diff_message}", file=sys.stderr)
    print(
        "This sync is broad enough to risk unintended wiki churn. "
        "Re-run with `llm-wiki sync --force` if this update is intentional.",
        file=sys.stderr,
    )
    _print_cache_stats(
        inventory_result.cache_stats, enabled=options.cache_stats_enabled
    )
    sys.exit(1)


def _apply_sync_changes(
    options: _SyncRunOptions,
    manifest: "SyncManifest",
    inventory: dict,
    diff: "SyncDiff",
    page_maps: _SyncPageMaps,
) -> "SyncResult":
    result = _apply_diff(
        diff,
        options.wiki_dir,
        inventory,
        options.src_dir,
        manifest,
        entity_page_cache=page_maps.entity_page_cache,
        module_page_map=page_maps.module_page_map,
        preserve_semantic=options.preserve_semantic,
    )

    _regenerate_flow_pages(options, inventory, page_maps.module_page_map)
    _regenerate_dependency_pages(options, inventory, page_maps.module_page_map)

    _rebuild_index(
        options.wiki_dir,
        inventory,
        options.src_dir,
        entity_page_cache=page_maps.entity_page_cache,
        module_page_map=page_maps.module_page_map,
    )

    _append_log(options.wiki_dir, options.src_dir, diff, result)
    return result


def _write_updated_manifest(
    options: _SyncRunOptions,
    inventory: dict,
    page_maps: _SyncPageMaps,
) -> None:
    print("Writing sync manifest...", flush=True)
    updated_manifest = _build_manifest_from_inventory(
        inventory,
        options.src_dir,
        entity_page_cache=page_maps.entity_page_cache,
        module_page_map=page_maps.module_page_map,
    )
    updated_manifest.save(options.wiki_dir)
    print(f"Manifest written to {options.wiki_dir / MANIFEST_FILENAME}", flush=True)


def _print_sync_summary(result: "SyncResult", diff: "SyncDiff") -> None:
    print(
        f"\nSync complete: {result.created} created, {result.updated} updated, "
        f"{result.metadata_only} metadata-only, {result.skipped} skipped, "
        f"{result.deprecated} deprecated."
    )
    if result.preserved_semantic:
        print(f"Preserved semantic fields: {result.preserved_semantic}")
    if diff.moved_entities:
        names = ", ".join(diff.moved_entities.keys())
        print(f"Moved entities detected (pages updated in-place): {names}")


def run(args) -> None:
    options = _sync_run_options_from_args(args)
    manifest = _load_or_seed_manifest(options)
    if manifest is None:
        return

    print(f"Syncing wiki from source: {options.src_dir}")
    print(f"Wiki directory: {options.wiki_dir}")

    inventory_result = _extract_current_inventory(options)
    inventory = inventory_result.inventory

    if _finish_if_empty_inventory(options, manifest, inventory_result):
        return

    if _repair_manifest_if_needed(options, manifest, inventory, inventory_result):
        return

    page_maps = _prepare_sync_page_maps(inventory)
    diff = _compute_sync_diff(manifest, inventory, options, page_maps)

    if _finish_if_no_changes(options, diff, inventory_result):
        return

    _exit_if_large_unforced_diff(options, diff, manifest, inventory_result)

    result = _apply_sync_changes(options, manifest, inventory, diff, page_maps)
    _write_updated_manifest(options, inventory, page_maps)
    _print_sync_summary(result, diff)
    _print_cache_stats(
        inventory_result.cache_stats, enabled=options.cache_stats_enabled
    )


# ── Index + log helpers ───────────────────────────────────────────────────────


def _rebuild_index(
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    *,
    entity_page_cache: dict[tuple[str, str], str] | None = None,
    module_page_map: dict[str, str] | None = None,
) -> None:
    """Regenerate index.md from the live inventory."""
    if entity_page_cache is None:
        _, _, entity_page_cache = _collision_maps(inventory, src_dir)
    mod_page_map = module_page_map or build_module_page_map(inventory)

    all_entity_names: list[str] = []
    seen: set[str] = set()
    module_entries: list[dict] = []

    for filepath, file_data in inventory.items():
        mod_page_name = mod_page_map.get(filepath, _page_name_for_module(filepath))
        module_entries.append(
            {
                "name": mod_page_name,
                "path": filepath,
                "docstring": file_data.get("module_docstring", ""),
            }
        )
        for cls in file_data.get("classes", []):
            page_name = entity_page_cache[(cls["name"], filepath)]
            if page_name not in seen:
                all_entity_names.append(page_name)
                seen.add(page_name)

    # Collect any existing workflow + flow + infrastructure entries from disk
    workflow_entries = _list_existing_pages(wiki_dir / "workflows", "entry")
    flow_entries = _list_existing_flow_pages(wiki_dir / "flows")
    infra_entries = _list_existing_pages(wiki_dir / "infrastructure", "type")
    architecture_entries = _list_existing_architecture_pages(wiki_dir)

    index_path = wiki_dir / "index.md"
    write_state = _write_md_if_changed(
        index_path,
        _generate_index_md(
            all_entity_names,
            module_entries,
            workflow_entries or None,
            infra_entries or None,
            flow_entries or None,
            architecture_entries or None,
        ),
    )
    if write_state == "unchanged":
        print("  SKIP index.md (unchanged)")
    else:
        print("  WRITE index.md")


def _list_existing_pages(directory: Path, extra_key: str) -> list[dict]:
    """Return a list of ``{"name": stem}`` dicts for every .md file in *directory*."""
    if not directory.exists():
        return []
    return [{"name": p.stem, extra_key: ""} for p in sorted(directory.glob("*.md"))]


# Top-level architecture pages (stem → index label), regenerated and re-linked
# on sync so they neither go stale nor get orphaned (DL-502).
_ARCHITECTURE_PAGES: tuple[tuple[str, str], ...] = (
    ("dependencies", "Dependencies"),
    ("load-order", "Load order"),
)


def _list_existing_architecture_pages(wiki_dir: Path) -> list[dict]:
    """Return ``{"name", "page"}`` entries for architecture pages present on disk."""
    return [
        {"name": label, "page": stem}
        for stem, label in _ARCHITECTURE_PAGES
        if (wiki_dir / f"{stem}.md").exists()
    ]


def _list_existing_flow_pages(directory: Path) -> list[dict]:
    """Return ``{"id", "category"}`` dicts for existing flow pages.

    ``category`` is derived from the entry-point id prefix so the index can be
    regrouped without re-running entry-point detection.
    """
    if not directory.exists():
        return []
    return [
        {"id": p.stem, "category": p.stem.split("-", 1)[0]}
        for p in sorted(directory.glob("*.md"))
    ]


def _preserve_flow_behavior(old_md: str, new_md: str) -> str:
    """Carry a human-edited ``## Behavior`` section into regenerated flow md."""
    old_body = _section_body(old_md, "Behavior")
    if not old_body or old_body == _section_body(new_md, "Behavior"):
        return new_md
    return _replace_section_body(new_md, "Behavior", old_body)


def _regenerate_flow_pages(
    options: _SyncRunOptions,
    inventory: dict,
    module_page_map: dict[str, str],
) -> int:
    """Regenerate flow pages from the current inventory, preserving Behavior.

    Runs only when the wiki already has flow pages, so projects that opted out
    of flows (``bootstrap --skip-flows``) are left untouched. Detection and the
    Mermaid diagrams are recomputed from the full inventory; only pages whose
    generated content actually changed are rewritten, and a human-edited
    ``## Behavior`` section is carried over when ``preserve_semantic`` is on.
    """
    flows_dir = options.wiki_dir / "flows"
    if not flows_dir.exists() or not any(flows_dir.glob("*.md")):
        return 0

    edges = resolve_call_edges(inventory)
    console_scripts = read_console_scripts(options.src_dir)
    regenerated = 0
    for entry_point in get_entry_points(inventory, console_scripts=console_scripts):
        flow = build_flow(entry_point, edges)
        new_md = _generate_flow_md(flow, module_page_map)
        flow_path = flows_dir / f"{entry_point['id']}.md"
        if options.preserve_semantic and flow_path.exists():
            new_md = _preserve_flow_behavior(read_md(flow_path), new_md)
        state = _write_md_if_changed(flow_path, new_md)
        if state != "unchanged":
            print(f"  {state.upper()} flow: {entry_point['id']}")
            regenerated += 1
    if regenerated:
        print(f"Regenerated {regenerated} flow page(s).")
    return regenerated


def _preserve_notes(old_md: str, new_md: str) -> str:
    """Carry a human-edited ``## Notes`` section into regenerated architecture md."""
    old_body = _section_body(old_md, "Notes")
    if not old_body or old_body == _section_body(new_md, "Notes"):
        return new_md
    return _replace_section_body(new_md, "Notes", old_body)


def _regenerate_dependency_pages(
    options: _SyncRunOptions,
    inventory: dict,
    module_page_map: dict[str, str],
) -> int:
    """Regenerate dependencies.md / load-order.md, preserving ``## Notes``.

    Runs only when a page already exists, so projects that opted out
    (``bootstrap --skip-dependencies``) are left untouched. The graph, cycles,
    reconciliation, and load order are recomputed once from the current
    inventory; only pages whose generated content changed are rewritten, and a
    human-edited ``## Notes`` section is carried over under ``preserve_semantic``.
    """
    deps_path = options.wiki_dir / "dependencies.md"
    load_path = options.wiki_dir / "load-order.md"
    if not deps_path.exists() and not load_path.exists():
        return 0

    analysis = analyze_dependencies(inventory, options.src_dir)
    pages = (
        (deps_path, _generate_dependencies_md(analysis, module_page_map)),
        (load_path, _generate_load_order_md(analysis, module_page_map)),
    )
    regenerated = 0
    for path, new_md in pages:
        if not path.exists():
            continue
        if options.preserve_semantic:
            new_md = _preserve_notes(read_md(path), new_md)
        state = _write_md_if_changed(path, new_md)
        if state != "unchanged":
            print(f"  {state.upper()} {path.name}")
            regenerated += 1
    if regenerated:
        print(f"Regenerated {regenerated} architecture page(s).")
    return regenerated


def _append_log(
    wiki_dir: Path, src_dir: str, diff: SyncDiff, result: SyncResult
) -> None:
    log_path = wiki_dir / "log.md"
    today = date.today().isoformat()
    moved_str = (
        ", ".join(
            f"`{cls}` ({old} → {new})"
            for cls, (old, new) in diff.moved_entities.items()
        )
        if diff.moved_entities
        else "none"
    )
    entry = (
        f"\n## {today}\n\n"
        f"### feat: incremental sync\n"
        f"- Source: `{src_dir}`\n"
        f"- Pages created: {result.created}\n"
        f"- Pages updated: {result.updated}\n"
        f"- Pages metadata-only: {result.metadata_only}\n"
        f"- Pages skipped (unchanged): {result.skipped}\n"
        f"- Pages deprecated: {result.deprecated}\n"
        f"- Semantic fields preserved: {result.preserved_semantic}\n"
        f"- Moved entities: {moved_str}\n"
    )
    if log_path.exists():
        existing_log = read_md(log_path)
        write_md(log_path, existing_log + entry)
    else:
        write_md(
            log_path, "# Architectural Log\n\nAppend-only chronological log.\n" + entry
        )
    print("  APPEND log.md")
