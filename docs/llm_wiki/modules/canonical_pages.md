# canonical_pages Module

**Path:** `src/llm_wiki_cli/services/canonical_pages.py`

## Description

Canonical generated page names and explicitly retained removal history.

## Imports

| Source | Symbols |
|--------|---------|
| `.bootstrap_runtime` | `build_entity_occurrence_page_map`, `build_module_page_map` |
| `.infrastructure_sync` | `build_infrastructure_page_map`, `infrastructure_evidence_by_page` |
| `.sync_manifest` | `SyncManifest`, `TOMBSTONE_SOURCE_MISSING` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n1["src/llm_wiki_cli/services/canonical_pages.py"]
    n2["src/llm_wiki_cli/services/infrastructure_sync.py"]
    n3["src/llm_wiki_cli/services/sync_manifest.py"]
    n4["src/llm_wiki_cli/services/team.py"]
    n0 --> n2
    n0 --> n3
    n1 --> n0
    n1 --> n2
    n1 --> n3
    n4 --> n0
    n4 --> n1
    n4 --> n3
    click n0 "../modules/bootstrap_runtime.md"
    click n1 "../modules/canonical_pages.md"
    click n2 "../modules/infrastructure_sync.md"
    click n3 "../modules/sync_manifest.md"
    click n4 "../modules/team.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [team](../modules/team.md) |
| Outbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Outbound | [infrastructure_sync](../modules/infrastructure_sync.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `canonical_generated_pages` | `(inventory: dict, infrastructure_inventory: Mapping[str, object], *, manifest: SyncManifest \| None = None) -> dict[str, set[str]]` | — | Use the generator's mappers; only known removal records extend live names. |
