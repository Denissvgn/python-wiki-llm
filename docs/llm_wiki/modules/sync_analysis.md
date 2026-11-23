# sync_analysis Module

**Path:** `src/llm_wiki_cli/services/sync_analysis.py`

## Description

Read-only source/manifest diff analysis shared by sync and lint.

## Imports

| Source | Symbols |
|--------|---------|
| `.bootstrap_runtime` | `_module_name_from_path`, `_page_name_for_entity`, `_page_name_for_module`, `build_entity_occurrence_page_map`, `build_entity_page_map`, `build_module_page_map` |
| `__future__` | `annotations` |
| `collections` | `Counter`, `defaultdict` |
| `dataclasses` | `dataclass`, `field` |
| `llm_wiki_engine.knowledge_evidence` | `hash_file`, `semantic_hash_for_file` |
| `llm_wiki_engine.sync_manifest` | `ManifestPageSource`, `SyncManifest` |
| `llm_wiki_engine.sync_ownership` | `SyncOwnershipError` |
| `llm_wiki_engine.validation` | `is_portable_path_component`, `portable_path_key` |
| `pathlib` | `Path` |
| `typing` | `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n1["src/llm_wiki_cli/services/lint_service.py"]
    n2["src/llm_wiki_cli/services/sync_analysis.py"]
    n3["src/llm_wiki_cli/services/sync_runtime.py"]
    n4["src/llm_wiki_cli/services/sync_transitions.py"]
    n5["src/llm_wiki_engine/knowledge_evidence.py"]
    n6["src/llm_wiki_engine/sync_manifest.py"]
    n7["src/llm_wiki_engine/sync_ownership.py"]
    n8["src/llm_wiki_engine/validation.py"]
    n0 --> n6
    n0 --> n8
    n1 --> n0
    n1 --> n2
    n1 --> n6
    n1 --> n8
    n2 --> n0
    n2 --> n5
    n2 --> n6
    n2 --> n7
    n2 --> n8
    n3 --> n0
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n8
    n4 --> n0
    n4 --> n2
    n4 --> n5
    n4 --> n6
    n4 --> n7
    n4 --> n8
    n5 --> n8
    n6 --> n5
    n6 --> n8
    click n0 "../modules/bootstrap_runtime.md"
    click n1 "../modules/lint_service.md"
    click n2 "../modules/sync_analysis.md"
    click n3 "../modules/sync_runtime.md"
    click n4 "../modules/sync_transitions.md"
    click n5 "../modules/knowledge_evidence.md"
    click n6 "../modules/sync_manifest.md"
    click n7 "../modules/sync_ownership.md"
    click n8 "../modules/validation.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [lint_service](../modules/lint_service.md) |
| Inbound | [sync_runtime](../modules/sync_runtime.md) |
| Inbound | [sync_transitions](../modules/sync_transitions.md) |
| Outbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |
| Outbound | [sync_ownership](../modules/sync_ownership.md) |
| Outbound | [validation](../modules/validation.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [_RecordedEntityPages](../entities/RecordedEntityPages.md) | 43 | — | — |
| [SyncDiff](../entities/SyncDiff.md) | 135 | — | Categorised difference between a persisted manifest and live inventory. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_ownership_error` | `(owner: EntityOwner, reason: str) -> SyncOwnershipError` | — | — |
| `_validated_recorded_page` | `(owner: EntityOwner, page: object) -> str` | — | — |
| `_recorded_entity_pages` | `(manifest: SyncManifest) -> _RecordedEntityPages` | — | Reconcile explicit ownership before considering any legacy fallback. |
| `compute_sync_diff` | `(manifest: SyncManifest, inventory: dict, src_dir: str, *, entity_page_cache: dict[tuple[str, str], str] \| None = None, module_page_map: dict[str, str] \| None = None, source_content_hashes: Mapping[str, str] \| None = None) -> SyncDiff` | — | Compare a managed manifest with one live structural inventory. |
