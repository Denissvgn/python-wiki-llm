# sync_transitions Module

**Path:** `src/llm_wiki_cli/services/sync_transitions.py`

## Description

Read-only ownership and filesystem preflight for entity/module page writes.

Retained page repair plans can carry source-derived section corrections as well
as link corrections, with exact expected bytes and an explicit reason. Both
retain the existing ownership, mutation and durable-original recovery boundary.

Validated retired coordinates participate in exact-owner revival. Their occupied
paths cannot be claimed by another live owner. Retirement history repairs use
the same expected-byte guards and durable preimage journal as other retained
page repairs; interrupted application retains recovery data and refuses blind
retry.

## Imports

| Source | Symbols |
|--------|---------|
| `.bootstrap_runtime` | `_module_name_from_path` |
| `.sync_analysis` | `SyncOwnershipError`, `_recorded_entity_pages` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `dataclasses` | `dataclass`, `field` |
| `llm_wiki_engine.knowledge_storage` | `MAX_EXPANDED_BYTES`, `KnowledgeStorageError` |
| `llm_wiki_engine.knowledge_storage_io` | `StorageReadSession` |
| `llm_wiki_engine.markdown_sections` | `normalize_markdown` |
| `llm_wiki_engine.source_retirement` | `retired_entity_mappings` |
| `llm_wiki_engine.sync_manifest` | `ManifestPageSource`, `SyncManifest` |
| `llm_wiki_engine.sync_retained_links` | `repair_retained_page_links` |
| `llm_wiki_engine.validation` | `portable_path_key` |
| `llm_wiki_engine.wiki_surface` | `PageKind`, `WikiSurfaceError`, `canonical_path` |
| `pathlib` | `Path` |
| `stat` | `stat` |
| `typing` | `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/sync_transitions.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/sync_transitions.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (5) |
| Outbound | `src` (10) |

> All 15 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [PageTransitionError](../entities/PageTransitionError.md) | 23 | `SyncOwnershipError` | The intended page writes cannot preserve verified ownership. |
| [PageTransition](../entities/PageTransition.md) | 28 | — | — |
| [StagedPageMove](../entities/StagedPageMove.md) | 52 | — | — |
| [RetainedPageRepair](../entities/RetainedPageRepair.md) | 59 | — | — |
| [PageTransitionPlan](../entities/PageTransitionPlan.md) | 68 | — | — |
| [_Ownership](../entities/Ownership.md) | 133 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_retained_page_repairs` | `(wiki_dir: Path, transitions: list[PageTransition], prior: _Ownership, existing: Mapping[str, tuple[str, bool]], deleted_source_paths: frozenset[str]) -> tuple[RetainedPageRepair, ...]` | — | — |
| `_page_path` | `(scope: str, page: str) -> str` | — | — |
| `_prior_ownership` | `(manifest: SyncManifest) -> _Ownership` | — | — |
| `_moved_module_owner` | `(prior: _Ownership, target: str, inventory: Mapping[str, Mapping]) -> ManifestPageSource \| None` | — | Return the retired module whose page a new module continues, if any. |
| `_moved_entity_owner` | `(prior: _Ownership, target: str, owner: ManifestPageSource, inventory: Mapping[str, Mapping]) -> ManifestPageSource \| None` | — | Return the retired declaration whose page a moved declaration continues. |
| `_existing_pages` | `(wiki_dir: Path) -> dict[str, tuple[str, bool]]` | — | Inventory names and file kinds without reading content or following links. |
| `_current_pages` | `(inventory: Mapping[str, Mapping], module_pages: Mapping[str, str], entity_pages: Mapping[tuple[str, str, int], str]) -> dict[ManifestPageSource, str]` | — | — |
| `plan_page_transitions` | `(wiki_dir: Path, manifest: SyncManifest, inventory: Mapping[str, Mapping], *, module_page_map: Mapping[str, str], entity_occurrence_page_map: Mapping[tuple[str, str, int], str], refresh_sources: frozenset[str] = frozenset(), moved_entities: Mapping[str, tuple[str, str]] \| None = None, deleted_source_paths: frozenset[str] = frozenset()) -> PageTransitionPlan` | — | Plan every live source-owned page using supplied names, without mutations. |
| `find_missing_source_pages` | `(wiki_dir: Path, manifest: SyncManifest, inventory: Mapping[str, Mapping], *, module_page_map: Mapping[str, str], entity_occurrence_page_map: Mapping[tuple[str, str, int], str], refresh_sources: frozenset[str] = frozenset(), moved_entities: Mapping[str, tuple[str, str]] \| None = None) -> dict[str, ManifestPageSource]` | — | Find missing canonical paths without inventing source changes or ownership. |
