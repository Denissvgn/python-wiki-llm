"""Read-only ownership and filesystem preflight for entity/module page writes."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
import stat
from typing import Mapping

from .bootstrap_runtime import _module_name_from_path
from .sync_analysis import SyncOwnershipError, _recorded_entity_pages
from .sync_manifest import ManifestPageSource, SyncManifest
from .validation import portable_path_key
from .wiki_surface import PageKind, WikiSurfaceError, canonical_path


class PageTransitionError(SyncOwnershipError):
    """The intended page writes cannot preserve verified ownership."""


@dataclass(frozen=True)
class PageTransition:
    owner: ManifestPageSource
    previous_owner: ManifestPageSource | None
    old_path: str | None
    source_path: str | None  # actual existing file, including its recorded casing
    final_path: str
    refresh_requested: bool

    @property
    def action(self) -> str:
        if self.source_path is None:
            return "create"
        if self.source_path != self.final_path:
            return "rename"
        if self.refresh_requested or self.owner != self.previous_owner:
            return "refresh"
        return "retain"

    @property
    def source_missing(self) -> bool:
        return self.old_path is not None and self.source_path is None


@dataclass(frozen=True)
class StagedPageMove:
    source_path: str
    staging_slot: str
    final_path: str


@dataclass(frozen=True)
class PageTransitionPlan:
    transitions: tuple[PageTransition, ...]
    # The executor fills ALL slots before placing ANY final target.
    # Slots are names within a private temporary directory, never wiki paths.
    staged_moves: tuple[StagedPageMove, ...]
    reserved_path_keys: tuple[str, ...]

def _page_path(scope: str, page: str) -> str:
    try:
        kind = PageKind.ENTITIES if scope == "entity" else PageKind.MODULES
        return canonical_path(kind, page)
    except WikiSurfaceError as exc:
        raise PageTransitionError(f"Invalid recorded {scope} page: {page!r}") from exc


@dataclass
class _Ownership:
    candidates: dict[ManifestPageSource, set[str]] = field(default_factory=dict)
    claims: dict[str, set[ManifestPageSource]] = field(default_factory=dict)

    def add(self, owner: ManifestPageSource, path: str, *, candidate: bool = True) -> None:
        if candidate:
            self.candidates.setdefault(owner, set()).add(path)
        self.claims.setdefault(portable_path_key(path), set()).add(owner)

    def resolve(self, owner: ManifestPageSource) -> str | None:
        paths = self.candidates.get(owner, set())
        if not paths:
            return None
        if len(paths) != 1:
            raise PageTransitionError(
                f"Conflicting recorded {owner.scope} pages for {owner.source_path!r}: {sorted(paths)!r}"
            )
        path = next(iter(paths))
        if self.claims[portable_path_key(path)] != {owner}:
            raise PageTransitionError(f"Multiple recorded owners claim {path!r}")
        return path


def _prior_ownership(manifest: SyncManifest) -> _Ownership:
    prior = _Ownership()
    for path, owner in manifest.page_source_mappings.items():
        if path != _page_path(owner.scope, Path(path).stem):
            raise PageTransitionError(f"Invalid recorded page path: {path!r}")
    entities = _recorded_entity_pages(manifest)
    for (source, name, occurrence), pages in entities.pages.items():
        owner = ManifestPageSource("entity", source, name, occurrence)
        for page in pages:
            prior.add(owner, _page_path("entity", page))
    for key, owners in entities.owners.items():
        for source, name, occurrence in owners:
            prior.add(
                ManifestPageSource("entity", source, name, occurrence),
                f"entities/{key}.md",
                candidate=False,
            )
    for source, info in sorted(manifest.sources.items()):
        if info.get("module_page"):
            prior.add(
                ManifestPageSource("module", source),
                _page_path("module", info["module_page"]),
            )
    for path, owner in sorted(manifest.page_source_mappings.items()):
        if owner.scope == "module":
            prior.add(owner, path, candidate=path not in manifest.tombstones)
    for source in sorted(manifest.sources):
        owner = ManifestPageSource("module", source)
        if owner not in prior.candidates:
            prior.add(owner, _page_path("module", _module_name_from_path(source)))
    return prior


def _existing_pages(wiki_dir: Path) -> dict[str, tuple[str, bool]]:
    """Inventory names and file kinds without reading content or following links."""
    existing: dict[str, tuple[str, bool]] = {}
    for directory in ("entities", "modules"):
        parent = wiki_dir / directory
        try:
            mode = parent.lstat().st_mode
        except FileNotFoundError:
            continue
        if not stat.S_ISDIR(mode):
            raise PageTransitionError(
                f"sync cannot safely stage page transitions under {directory!r}: "
                "not a regular directory"
            )
        for path in sorted(parent.iterdir()):
            if path.suffix.casefold() != ".md":
                continue
            relative = f"{directory}/{path.name}"
            key = portable_path_key(relative)
            if key in existing:
                raise PageTransitionError(
                    f"Portable page filename collision: {existing[key][0]!r} and {relative!r}"
                )
            existing[key] = (relative, stat.S_ISREG(path.lstat().st_mode))
    return existing


def _current_pages(
    inventory: Mapping[str, Mapping],
    module_pages: Mapping[str, str],
    entity_pages: Mapping[tuple[str, str, int], str],
) -> dict[ManifestPageSource, str]:
    pages: dict[ManifestPageSource, str] = {}
    entity_keys = set()
    for source, data in sorted(inventory.items()):
        if source not in module_pages:
            raise PageTransitionError(f"Missing module page mapping for {source!r}")
        pages[ManifestPageSource("module", source)] = _page_path(
            "module", module_pages[source]
        )
        occurrences: Counter[str] = Counter()
        for cls in data.get("classes", []):
            name = cls["name"]
            occurrences[name] += 1
            key = (name, source, occurrences[name])
            entity_keys.add(key)
            if key not in entity_pages:
                raise PageTransitionError(f"Missing entity occurrence page mapping: {key!r}")
            owner = ManifestPageSource("entity", source, name, occurrences[name])
            pages[owner] = _page_path("entity", entity_pages[key])
    if set(module_pages) != set(inventory) or set(entity_pages) != entity_keys:
        raise PageTransitionError("Page maps contain owners absent from the current inventory")
    return pages


def plan_page_transitions(
    wiki_dir: Path,
    manifest: SyncManifest,
    inventory: Mapping[str, Mapping],
    *,
    module_page_map: Mapping[str, str],
    entity_occurrence_page_map: Mapping[tuple[str, str, int], str],
    refresh_sources: frozenset[str] = frozenset(),
    moved_entities: Mapping[str, tuple[str, str]] | None = None,
) -> PageTransitionPlan:
    """Plan every live source-owned page using supplied names, without mutations.

    Occupied targets must belong to their incoming owner or to another verified
    owner that this same plan moves away. Missing originals never acquire the
    content of a different page. This plan describes missing-page creation even
    when an unchanged source has not yet been scheduled by sync for refresh.
    """
    prior = _prior_ownership(manifest)
    try:
        existing = _existing_pages(wiki_dir)
    except OSError as exc:
        raise PageTransitionError(f"Cannot inspect entity/module page paths: {exc}") from exc
    current = _current_pages(inventory, module_page_map, entity_occurrence_page_map)
    old_counts = {
        source: Counter(info.get("entities", []))
        for source, info in manifest.sources.items()
    }
    new_names = Counter(owner.entity_name for owner in current if owner.scope == "entity")
    old_names: Counter[str] = Counter()
    for counts in old_counts.values():
        old_names.update(counts)
    moves = moved_entities or {}
    targets: set[str] = set()
    origins: dict[str, PageTransition] = {}
    transitions = []
    for owner, target in sorted(current.items(), key=lambda item: item[1]):
        target_key = portable_path_key(target)
        if target_key in targets:
            raise PageTransitionError(f"Multiple current owners target {target!r}")
        targets.add(target_key)
        previous = None
        if owner.scope == "module" and owner.source_path in manifest.sources:
            previous = owner
        elif owner.scope == "entity":
            name, occurrence = str(owner.entity_name), int(owner.occurrence or 0)
            if old_counts.get(owner.source_path, {}).get(name, 0) >= occurrence:
                previous = owner
            elif name in moves and moves[name][1] == owner.source_path:
                old_source = moves[name][0]
                if (
                    old_names[name] != 1
                    or new_names[name] != 1
                    or old_counts.get(old_source, {}).get(name) != 1
                ):
                    raise PageTransitionError(f"Ambiguous source move for {name!r}")
                previous = ManifestPageSource("entity", old_source, name, 1)
        old_path = prior.resolve(previous) if previous is not None else None
        source_path = None
        if old_path is not None and portable_path_key(old_path) in existing:
            source_path, regular = existing[portable_path_key(old_path)]
            if not regular:
                raise PageTransitionError(f"Rename source is not a regular file: {source_path!r}")
        item = PageTransition(
            owner=owner,
            previous_owner=previous,
            old_path=old_path,
            source_path=source_path,
            final_path=target,
            refresh_requested=owner.source_path in refresh_sources,
        )
        transitions.append(item)
        if old_path is not None:
            key = portable_path_key(old_path)
            if key in origins:
                raise PageTransitionError(f"Multiple current owners claim old page {old_path!r}")
            origins[key] = item

    for item in transitions:
        key = portable_path_key(item.final_path)
        if key not in existing:
            continue
        occupant, regular = existing[key]
        if not regular:
            raise PageTransitionError(f"Write target is not a regular file: {occupant!r}")
        outgoing = origins.get(key)
        if outgoing is None or prior.claims.get(key) != {outgoing.previous_owner}:
            raise PageTransitionError(
                f"Occupied target has no verified outgoing owner: {occupant!r}"
            )
        if outgoing.owner != item.owner and portable_path_key(outgoing.final_path) == key:
            raise PageTransitionError(f"Occupied target is retained by another owner: {occupant!r}")

    staged = tuple(
        StagedPageMove(item.source_path, f"page-{index:06d}", item.final_path)
        for index, item in enumerate(sorted(transitions, key=lambda item: item.old_path or ""))
        if item.source_path is not None and item.action == "rename"
    )
    return PageTransitionPlan(
        transitions=tuple(transitions),
        staged_moves=staged,
        reserved_path_keys=tuple(sorted(prior.claims)),
    )
