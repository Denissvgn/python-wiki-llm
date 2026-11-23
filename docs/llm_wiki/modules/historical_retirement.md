# historical_retirement Module

**Path:** `src/llm_wiki_cli/services/historical_retirement.py`

## Description

Plan explicit whole-file archival from the authenticated *prior* source projection.

## Imports

| Source | Symbols |
|--------|---------|
| `.source_snapshot` | `confirmed_missing_source_paths` |
| `.sync_transitions` | `ReleasedPageInputs` |
| `collections` | `Counter` |
| `llm_wiki_engine.contracts` | `SECTION_OWNERSHIP_EXTENSION_KEY` |
| `llm_wiki_engine.historical_sources` | `INPUT`, `SCHEMA`, `bound_records`, `page_matches`, `predecessor_records`, `read_records`, `remove_bound_registry`, `RELEASES`, `latest_released_pages` |
| `llm_wiki_engine.host` | `emit` |
| `llm_wiki_engine.knowledge_artifacts` | `require_validated_artifacts` |
| `llm_wiki_engine.knowledge_evidence` | `is_valid_sha256`, `sha256_bytes` |
| `llm_wiki_engine.knowledge_storage` | `MAX_EXPANDED_BYTES` |
| `llm_wiki_engine.knowledge_storage_io` | `StorageReadSession` |
| `llm_wiki_engine.source_retirement` | `SourceRetirementError` |
| `llm_wiki_engine.sync_manifest` | `ManifestPageSource` |
| `llm_wiki_engine.validation` | `portable_path_key`, `require_repository_relative_path` |
| `llm_wiki_engine.wiki_surface` | `PageKind`, `canonical_path` |
| `pathlib` | `PurePosixPath` |
| `typing` | `NoReturn` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/historical_retirement.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/historical_retirement.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (3) |
| Outbound | `src` (13) |

> All 16 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `refuse` | `(message: str) -> NoReturn` | — | — |
| `_portable_path` | `(path)` | — | — |
| `_selected_paths` | `(values, maximum)` | — | — |
| `selected_sources` | `(values)` | — | — |
| `selected_pages` | `(values)` | — | — |
| `confirm_absence` | `(snapshot, sources)` | — | — |
| `check_prior_pages` | `(wiki_root, previous, next_records)` | — | Bind an imminent write to the exact enrollment preimages, including its index. |
| `_original_owners` | `(manifest, source)` | — | — |
| `released_inputs` | `(manifest, artifacts, source_snapshot)` | — | Associate ordinary revival with the current capture and the previous native page digest. |
| `plan_retirement` | `(options, manifest, committed, snapshot, inventory, page_plan, generation_inputs)` | — | — |
