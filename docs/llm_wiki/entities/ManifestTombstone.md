# ManifestTombstone

**Location:** `src/llm_wiki_cli/services/sync_manifest.py:357`
**Kind:** Class
**Bases:** —
**Module:** [sync_manifest](../modules/sync_manifest.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Evidence retained for a stale module/entity page.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `reason` | `str` | *required* | — |
| `last_valid_basis` | `ConceptObservationBasis \| None` | `None` | — |
| `unknown_reason` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_payload` | `() -> dict[str, object]` | — | — |
| `from_payload` | `(value: object, field_name: str) -> ManifestTombstone` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ManifestTombstone (src/llm_wiki_cli/services/sync_manifest.py)"]
    n1["_defer_sources_for_regeneration (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n2["_downgrade_incompatible_tombstones (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n3["_reconcile_active_structural_evidence (src/llm_wiki_cli/services/knowledge_generation.py)"]
    n4["src/llm_wiki_cli/services/knowledge_index.py"]
    n5["ManifestTombstone.from_payload (src/llm_wiki_cli/services/sync_manifest.py)"]
    n6["SyncManifest.build_from_inventory (src/llm_wiki_cli/services/sync_manifest.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/sync_manifest.md"
    click n1 "../modules/knowledge_generation.md"
    click n2 "../modules/knowledge_generation.md"
    click n3 "../modules/knowledge_generation.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/sync_manifest.md"
    click n6 "../modules/sync_manifest.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_manifest](../modules/sync_manifest.md) | 3 | `last_valid_basis`, `reason`, `unknown_reason` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_defer_sources_for_regeneration` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_downgrade_incompatible_tombstones` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_reconcile_active_structural_evidence` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `_reconcile_active_structural_evidence` | call | [knowledge_generation](../modules/knowledge_generation.md) |
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) |
| `ManifestTombstone.from_payload` | type_reference | [sync_manifest](../modules/sync_manifest.md) |
| `SyncManifest.build_from_inventory` | call | [sync_manifest](../modules/sync_manifest.md) |
| `SyncManifest.build_from_inventory` | call | [sync_manifest](../modules/sync_manifest.md) |
| `SyncManifest.build_from_inventory` | call | [sync_manifest](../modules/sync_manifest.md) |
| `SyncManifest.build_from_inventory` | call | [sync_manifest](../modules/sync_manifest.md) |
