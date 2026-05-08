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

from .extract_cmd import get_inventory_result, infer_language_from_path, print_inventory_failures
from .bootstrap_cmd import (
    _build_relationships,
    _generate_entity_md,
    _generate_index_md,
    _generate_module_md,
    _module_name_from_path,
    _page_name_for_entity,
    _page_name_for_module,
    build_entity_page_map,
    build_module_page_map,
)
from ..config import validate_path
from ..services.inventory_cache import InventoryCacheOptions, InventoryCacheStats, format_cache_stats
from ..services.io import read_md, write_md

# ── Constants ─────────────────────────────────────────────────────────────────

MANIFEST_FILENAME = ".llm-wiki-manifest.json"
MANIFEST_VERSION = 2
MAX_SYNC_AFFECTED_FILES = 50
MAX_SYNC_AFFECTED_RATIO = 0.30
MIN_SOURCES_FOR_RATIO_GUARD = 10
_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
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


def _build_manifest_from_inventory(inventory: dict, src_dir: str) -> "SyncManifest":
    colliding_stems, colliding_cls, entity_page_cache = _collision_maps(inventory, src_dir)
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

# ── Manifest ──────────────────────────────────────────────────────────────────


@dataclass
class SyncManifest:
    """Persistent record of what the wiki was generated from.

    Schema v2::

        {
            "version": 1,
            "sources": {
                "src/models.py": {
                    "hash": "sha256:<hex>",
                    "language": "python",
                    "entities": ["User", "Role"],
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
                "language": file_data.get("language") or infer_language_from_path(filepath),
                "entities": [c["name"] for c in file_data.get("classes", [])],
                "entity_pages": {
                    c["name"]: entity_page_cache.get((c["name"], filepath), c["name"])
                    for c in file_data.get("classes", [])
                },
                "module_page": module_page_map.get(filepath, _module_name_from_path(filepath)),
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
    unchanged_files: list[str] = field(default_factory=list)
    removed_files: list[str] = field(default_factory=list)
    # {class_name: (old_filepath, new_filepath)}
    moved_entities: dict[str, tuple[str, str]] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(
            self.new_files
            or self.changed_files
            or self.removed_files
            or self.moved_entities
        )


def _affected_source_files(diff: SyncDiff) -> set[str]:
    affected = set(diff.new_files) | set(diff.changed_files) | set(diff.removed_files)
    for old_path, new_path in diff.moved_entities.values():
        affected.add(old_path)
        affected.add(new_path)
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


def _compute_diff(manifest: SyncManifest, inventory: dict, src_dir: str) -> SyncDiff:
    """Compare *manifest* against the live *inventory*.

    Move detection: a class that appears in the manifest under one filepath
    but now lives in a *different* filepath is considered moved rather than
    deleted+created.  Its source-file hash is therefore refreshed from the
    *new* filepath.
    """
    diff = SyncDiff()

    # Build reverse lookup: class_name → filepath (from old manifest)
    old_cls_to_file: dict[str, str] = {}
    for fp, info in manifest.sources.items():
        for cls_name in info.get("entities", []):
            old_cls_to_file[cls_name] = fp

    # Build reverse lookup: class_name → filepath (from new inventory)
    new_cls_to_file: dict[str, str] = {}
    for fp, file_data in inventory.items():
        for cls in file_data.get("classes", []):
            new_cls_to_file[cls["name"]] = fp

    # Detect moves: same class name, different file
    for cls_name, old_fp in old_cls_to_file.items():
        new_fp = new_cls_to_file.get(cls_name)
        if new_fp is not None and new_fp != old_fp:
            diff.moved_entities[cls_name] = (old_fp, new_fp)

    # Categorise each file in the new inventory
    for filepath, file_data in inventory.items():
        if filepath not in manifest.sources:
            diff.new_files.append(filepath)
        else:
            # Re-hash to detect content changes
            current_hash = _hash_file(Path(src_dir) / filepath)
            if current_hash != manifest.sources[filepath].get("hash", ""):
                diff.changed_files.append(filepath)
            else:
                diff.unchanged_files.append(filepath)

    # Detect removals: in manifest but not in new inventory
    for filepath in manifest.sources:
        if filepath not in inventory:
            diff.removed_files.append(filepath)

    return diff


# ── Apply ─────────────────────────────────────────────────────────────────────


@dataclass
class SyncResult:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    deprecated: int = 0


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


def _apply_diff(
    diff: SyncDiff,
    wiki_dir: Path,
    inventory: dict,
    src_dir: str,
    manifest: SyncManifest,
) -> SyncResult:
    """Regenerate pages for new/changed files, deprecate pages for removed files."""
    result = SyncResult()

    # Full collision maps over the *entire* inventory
    colliding_stems, colliding_cls, entity_page_cache = _collision_maps(inventory, src_dir)

    # Module page map for the manifest builder: filepath → module_page_name
    module_page_map: dict[str, str] = build_module_page_map(inventory)

    # Re-build relationships from the full inventory using the same
    # collision-aware module page names as bootstrap/migrate.
    relationships = _build_relationships(inventory, module_page_map)

    # ── New + changed files ────────────────────────────────────────────────────
    for filepath in diff.new_files + diff.changed_files:
        file_data = inventory[filepath]
        mod_page_name = module_page_map.get(filepath, _page_name_for_module(filepath))

        file_entity_page_map = {
            cls["name"]: entity_page_cache[(cls["name"], filepath)]
            for cls in file_data.get("classes", [])
        }

        # Entity pages
        for cls in file_data.get("classes", []):
            entity_page_name = file_entity_page_map[cls["name"]]
            entity_path = wiki_dir / "entities" / f"{entity_page_name}.md"
            content = _generate_entity_md(cls, filepath, relationships, mod_page_name)
            write_state = _write_md_if_changed(entity_path, content)
            if write_state == "created":
                result.created += 1
                print(f"  CREATE entity: {entity_page_name}")
            elif write_state == "updated":
                result.updated += 1
                print(f"  UPDATE entity: {entity_page_name}")
            else:
                result.skipped += 1
                print(f"  SKIP entity (unchanged): {entity_page_name}")

        # Module page
        module_path = wiki_dir / "modules" / f"{mod_page_name}.md"
        content = _generate_module_md(filepath, file_data, file_entity_page_map)
        write_state = _write_md_if_changed(module_path, content)
        if write_state == "created":
            result.created += 1
            print(f"  CREATE module: {mod_page_name}")
        elif write_state == "updated":
            result.updated += 1
            print(f"  UPDATE module: {mod_page_name}")
        else:
            result.skipped += 1
            print(f"  SKIP module (unchanged): {mod_page_name}")

    # ── Unchanged files ────────────────────────────────────────────────────────
    for filepath in diff.unchanged_files:
        mod_page_name = module_page_map.get(filepath, _page_name_for_module(filepath))
        entity_count = len(inventory[filepath].get("classes", []))
        result.skipped += 1 + entity_count  # 1 module page + N entity pages
        print(f"  SKIP (unchanged): {_module_name_from_path(filepath)}")

    # ── Removed files ──────────────────────────────────────────────────────────
    for filepath in diff.removed_files:
        old_info = manifest.sources[filepath]
        deprecated_count = 0

        for cls_name in old_info.get("entities", []):
            entity_page_name = _removed_entity_page_name(wiki_dir, cls_name, filepath, old_info)

            if entity_page_name:
                entity_path = wiki_dir / "entities" / f"{entity_page_name}.md"
                text = read_md(entity_path)
                if _DEPRECATION_HEADER not in text:
                    write_state = _write_md_if_changed(entity_path, _DEPRECATION_HEADER + text)
                    if write_state != "unchanged":
                        deprecated_count += 1
                        result.deprecated += 1
                        print(f"  DEPRECATE entity: {entity_page_name}")

        # Module page deprecation
        old_mod_page = old_info.get("module_page", _module_name_from_path(filepath))
        mod_page_path = wiki_dir / "modules" / f"{old_mod_page}.md"

        if mod_page_path.exists():
            text = read_md(mod_page_path)
            if _DEPRECATION_HEADER not in text:
                write_state = _write_md_if_changed(mod_page_path, _DEPRECATION_HEADER + text)
                if write_state != "unchanged":
                    result.deprecated += 1
                    print(f"  DEPRECATE module: {mod_page_path.stem}")

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


def run(args) -> None:
    src_dir: str = getattr(args, "src_dir", ".")
    wiki_dir = Path(getattr(args, "wiki_dir", "docs/llm_wiki"))
    cache_options = _cache_options_from_args(args)
    cache_stats_enabled = bool(getattr(args, "cache_stats", False))
    parallel_jobs = getattr(args, "jobs", 1)
    force = bool(getattr(args, "force", False))
    validate_path(src_dir, "--src-dir")
    validate_path(str(wiki_dir), "--wiki-dir")

    # 1. Load manifest — seed one if the wiki exists but the manifest doesn't
    #    (migration path for projects bootstrapped by older llm-wiki versions)
    try:
        manifest = SyncManifest.load(wiki_dir)
    except FileNotFoundError:
        if (wiki_dir / "index.md").exists():
            # Wiki was bootstrapped before manifests existed → seed baseline
            print(
                f"No sync manifest found — seeding from current source state.\n"
                f"Existing wiki pages will NOT be modified.\n"
                f"Future `llm-wiki sync` runs will update incrementally.\n"
            )
            print("Extracting current source inventory...")
            inventory_result = get_inventory_result(
                src_dir,
                deep=True,
                cache_options=cache_options,
                parallel_jobs=parallel_jobs,
            )
            if inventory_result.failed:
                print_inventory_failures(inventory_result)
                sys.exit(1)
            inventory = inventory_result.inventory
            print(f"Extracted current source inventory: {len(inventory)} file(s).")
            if not inventory:
                print("No supported source files found; manifest not written.")
                _print_cache_stats(inventory_result.cache_stats, enabled=cache_stats_enabled)
                return
            seed = _build_manifest_from_inventory(inventory, src_dir)
            seed.save(wiki_dir)
            print(f"Manifest written to {wiki_dir / MANIFEST_FILENAME}")
            _print_cache_stats(inventory_result.cache_stats, enabled=cache_stats_enabled)
            return
        print(
            f"Error: no sync manifest found at {wiki_dir / MANIFEST_FILENAME}.\n"
            "Run `llm-wiki bootstrap` first to create the initial wiki and manifest.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Syncing wiki from source: {src_dir}")
    print(f"Wiki directory: {wiki_dir}")

    # 2. Extract current AST inventory (always deep for full page content)
    print("Extracting current source inventory...")
    inventory_result = get_inventory_result(
        src_dir,
        deep=True,
        cache_options=cache_options,
        parallel_jobs=parallel_jobs,
    )
    if inventory_result.failed:
        print_inventory_failures(inventory_result)
        sys.exit(1)
    inventory = inventory_result.inventory
    print(f"Extracted current source inventory: {len(inventory)} file(s).")

    if not inventory and not manifest.sources:
        print("No supported source files with classes or functions found.")
        _print_cache_stats(inventory_result.cache_stats, enabled=cache_stats_enabled)
        return

    invalid_hash_paths = _invalid_manifest_hash_paths(manifest)
    if invalid_hash_paths:
        repaired = _build_manifest_from_inventory(inventory, src_dir)
        repaired.save(wiki_dir)
        print(
            f"Sync manifest repaired: {len(invalid_hash_paths)} source entr"
            f"{'y has' if len(invalid_hash_paths) == 1 else 'ies have'} invalid or missing hashes."
        )
        print("Wiki pages were not modified. Run `llm-wiki sync` again to apply source changes.")
        _print_cache_stats(inventory_result.cache_stats, enabled=cache_stats_enabled)
        return

    # 3. Compute diff
    diff = _compute_diff(manifest, inventory, src_dir)

    if not diff.has_changes:
        print("Wiki is up to date.")
        _print_cache_stats(inventory_result.cache_stats, enabled=cache_stats_enabled)
        return

    large_diff_message = _large_diff_message(diff, manifest)
    if large_diff_message and not force:
        print(f"Error: {large_diff_message}", file=sys.stderr)
        print(
            "This sync is broad enough to risk unintended wiki churn. "
            "Re-run with `llm-wiki sync --force` if this update is intentional.",
            file=sys.stderr,
        )
        _print_cache_stats(inventory_result.cache_stats, enabled=cache_stats_enabled)
        sys.exit(1)

    # 4. Apply changes
    result = _apply_diff(diff, wiki_dir, inventory, src_dir, manifest)

    # 5. Rebuild index.md
    _rebuild_index(wiki_dir, inventory, src_dir)

    # 6. Append log entry
    _append_log(wiki_dir, src_dir, diff, result)

    # 7. Compute collision maps + module page map for manifest, then save
    updated_manifest = _build_manifest_from_inventory(inventory, src_dir)
    updated_manifest.save(wiki_dir)

    print(
        f"\nSync complete: {result.created} created, {result.updated} updated, "
        f"{result.skipped} skipped, {result.deprecated} deprecated."
    )
    if diff.moved_entities:
        names = ", ".join(diff.moved_entities.keys())
        print(f"Moved entities detected (pages updated in-place): {names}")
    _print_cache_stats(inventory_result.cache_stats, enabled=cache_stats_enabled)


# ── Index + log helpers ───────────────────────────────────────────────────────


def _rebuild_index(wiki_dir: Path, inventory: dict, src_dir: str) -> None:
    """Regenerate index.md from the live inventory."""
    colliding_stems, colliding_cls, entity_page_cache = _collision_maps(inventory, src_dir)
    mod_page_map = build_module_page_map(inventory)

    all_entity_names: list[str] = []
    seen: set[str] = set()
    module_entries: list[dict] = []

    for filepath, file_data in inventory.items():
        mod_page_name = mod_page_map.get(filepath, _page_name_for_module(filepath))
        module_entries.append({
            "name": mod_page_name,
            "path": filepath,
            "docstring": file_data.get("module_docstring", ""),
        })
        for cls in file_data.get("classes", []):
            page_name = entity_page_cache[(cls["name"], filepath)]
            if page_name not in seen:
                all_entity_names.append(page_name)
                seen.add(page_name)

    # Collect any existing workflow + infrastructure entries from disk
    workflow_entries = _list_existing_pages(wiki_dir / "workflows", "entry")
    infra_entries = _list_existing_pages(wiki_dir / "infrastructure", "type")

    index_path = wiki_dir / "index.md"
    write_state = _write_md_if_changed(
        index_path,
        _generate_index_md(all_entity_names, module_entries, workflow_entries or None, infra_entries or None),
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


def _append_log(wiki_dir: Path, src_dir: str, diff: SyncDiff, result: SyncResult) -> None:
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
        f"- Pages skipped (unchanged): {result.skipped}\n"
        f"- Pages deprecated: {result.deprecated}\n"
        f"- Moved entities: {moved_str}\n"
    )
    if log_path.exists():
        existing_log = read_md(log_path)
        write_md(log_path, existing_log + entry)
    else:
        write_md(log_path, "# Architectural Log\n\nAppend-only chronological log.\n" + entry)
    print("  APPEND log.md")
