# ManifestStoreReader

**Location:** `src/llm_wiki_cli/services/manifest_storage.py:153`
**Kind:** Class
**Bases:** —
**Module:** [manifest_storage](../modules/manifest_storage.md)

## Description

Authenticates bounded immutable manifest catalogs for physical v6/logical v5 and adopted physical v8/logical v7. It enforces catalog commitments, canonical encoding, expansion accounting and tree limits. Full materialization verifies the complete logical commitment, including adopted maintenance state; selected header reads retain their explicitly unverified scope.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(root: Mapping[str, Any], read: Reader)` | — | — |
| `_chunks` | `(desc: dict[str, Any], depth: int = 0)` | — | — |
| `field` | `(name: str) -> dict[str, Any]` | — | — |
| `materialize` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ManifestStoreReader (src/llm_wiki_cli/services/manifest_storage.py)"]
    n1["_capture_slice (src/llm_wiki_cli/services/knowledge_storage_access.py)"]
    n2["read_manifest_header (src/llm_wiki_cli/services/manifest_storage.py)"]
    n3["SyncManifest.from_payload (src/llm_wiki_cli/services/sync_manifest.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/manifest_storage.md"
    click n1 "../modules/knowledge_storage_access.md"
    click n2 "../modules/manifest_storage.md"
    click n3 "../modules/sync_manifest.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [manifest_storage](../modules/manifest_storage.md) | 4 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_capture_slice` | call | [knowledge_storage_access](../modules/knowledge_storage_access.md) | 1 |
| `read_manifest_header` | call | [manifest_storage](../modules/manifest_storage.md) | 1 |
| `SyncManifest.from_payload` | call | [sync_manifest](../modules/sync_manifest.md) | 1 |
