# source_retirement Module

**Path:** `src/llm_wiki_cli/services/source_retirement.py`

## Description

Source-owned member retirement, separate from authored concept lifecycle.

Retirement authority comes from exact persisted source coordinates and current
selected inventory, not Markdown headers or filename guesses. The machine
`entity_retirement` record binds canonical entity paths to historical owners and
tombstones. A member that disappears from a still-documentable source keeps its
page and authored content; native reads expose `llm-wiki/source-retirement`.
Known historical evidence stays historical, and unknown provenance is not
upgraded. This observation never authors human reviews or concept lifecycle.

Retained generated defaults support attribution when the exact owner revives.
Current generated descriptions can update while authored descriptions, cells and
custom context survive. Duplicate suffix removal requires a distinguishable,
unchanged surviving prefix under recorded defaults and full entity observations;
ambiguous shifts stop before writes. Captured sources without documentable inventory require parser qualification.
A valid empty module remains a current source owner; syntax failures, aliases and
unavailable coverage cannot establish removal authority.

`retained_empty_module_paths` reads the owning source marker only to select an
actual parser request. The marker does not mint current evidence. The source
module is reconstructed by its language parser, and its former members retain
the independent historical retirement policy.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_evidence` | `entity_observation_hash` |
| `.sync_analysis` | `_recorded_entity_pages` |
| `.sync_manifest` | `ManifestPageSource`, `SyncManifest`, `SyncManifestError`, `generated_semantics_for_file` |
| `.validation` | `portable_path_key` |
| `.wiki_surface` | `PageKind`, `WikiSurfaceError`, `canonical_path` |
| `__future__` | `annotations` |
| `collections` | `Counter` |
| `collections.abc` | `Mapping` |
| `pathlib` | `PurePosixPath` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/source_retirement.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/source_retirement.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (9) |
| Outbound | `src` (5) |

> All 13 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [SourceRetirementError](../entities/SourceRetirementError.md) | 23 | `ValueError` | A retirement record cannot be reconciled with authoritative ownership. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `retained_empty_module_paths` | `(manifest: SyncManifest \| None) -> tuple[str, ...]` | — | Return source paths whose last owning run retained a parser-empty module. |
| `retained_empty_module_paths_from_wiki` | `(wiki_dir) -> tuple[str, ...]` | — | Read only the configured manifest to select parser retention, not evidence. |
| `read_entity_retirement_state` | `(generation_inputs: Mapping[str, object]) -> dict[str, ManifestPageSource]` | — | Decode exact machine records without deriving ownership from Markdown. |
| `entity_owner_present` | `(owner: ManifestPageSource, sources: Mapping[str, Mapping]) -> bool` | — | Compare the exact declaration occurrence with captured source membership. |
| `retired_entity_mappings` | `(manifest: SyncManifest) -> dict[str, ManifestPageSource]` | — | Validate committed retirements against mappings and historical tombstones. |
| `with_entity_retirement_state` | `(generation_inputs: Mapping[str, object], mappings: Mapping[str, ManifestPageSource], *, generated_semantics: Mapping[str, dict] \| None = None) -> dict[str, object]` | — | Retain the planned coordinates without minting evidence or lifecycle. |
| `historical_entity_semantics` | `(manifest: SyncManifest, owner: ManifestPageSource) -> dict \| None` | — | Return recorded generated defaults for attribution when the owner revives. |
| `discover_retired_entities` | `(manifest: SyncManifest, inventory: Mapping[str, Mapping]) -> dict[str, ManifestPageSource]` | — | Plan fresh removals and recover exact persisted, previously unmarked owners. |
| `_check_duplicate_removal_custody` | `(manifest, inventory, recorded) -> None` | — | Require an unchanged, distinguishable surviving prefix before retiring suffixes. |