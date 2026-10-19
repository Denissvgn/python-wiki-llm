# search_discovery_capture Module

**Path:** `src/llm_wiki_cli/services/search_discovery_capture.py`

## Description

Guarded snapshot inputs for opt-in discovery; no extraction or writes.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_artifacts` | `_decode_json_object` |
| `.knowledge_model` | `parse_knowledge_index` |
| `.knowledge_storage` | `ROOT_FILENAME`, `LOGICAL_SCHEMA`, `MAX_ROOT_BYTES`, `KnowledgeStorageError`, `canonical_bytes`, `digest` |
| `.knowledge_storage_access` | `ScopedKnowledgeRead`, `capture_knowledge_slice` |
| `.knowledge_storage_io` | `StorageReadSession` |
| `.maintenance_protocol` | `ADOPTION_FILENAME`, `MaintenanceProtocolError`, `guard_maintenance_owner` |
| `.maintenance_status` | `build_maintenance_status` |
| `.search_source` | `captured_manifest` |
| `.sync_manifest` | `MANIFEST_FILENAME`, `SyncManifest` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n1["src/llm_wiki_cli/services/knowledge_model.py"]
    n2["src/llm_wiki_cli/services/knowledge_storage.py"]
    n3["src/llm_wiki_cli/services/knowledge_storage_access.py"]
    n4["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n5["src/llm_wiki_cli/services/maintenance_protocol.py"]
    n6["src/llm_wiki_cli/services/maintenance_status.py"]
    n7["src/llm_wiki_cli/services/search_discovery_capture.py"]
    n8["src/llm_wiki_cli/services/search_service.py"]
    n9["src/llm_wiki_cli/services/search_source.py"]
    n10["src/llm_wiki_cli/services/sync_manifest.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n4
    n0 --> n5
    n0 --> n10
    n2 --> n1
    n3 --> n0
    n3 --> n1
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n10
    n4 --> n2
    n5 --> n2
    n5 --> n4
    n5 --> n10
    n6 --> n2
    n7 --> n0
    n7 --> n1
    n7 --> n2
    n7 --> n3
    n7 --> n4
    n7 --> n5
    n7 --> n6
    n7 --> n9
    n7 --> n10
    n8 --> n2
    n8 --> n4
    n8 --> n7
    n8 --> n9
    n9 --> n0
    n9 --> n2
    n9 --> n4
    n9 --> n10
    n10 --> n2
    n10 --> n4
    click n0 "../modules/knowledge_artifacts.md"
    click n1 "../modules/knowledge_model.md"
    click n2 "../modules/knowledge_storage.md"
    click n3 "../modules/knowledge_storage_access.md"
    click n4 "../modules/knowledge_storage_io.md"
    click n5 "../modules/maintenance_protocol.md"
    click n6 "../modules/maintenance_status.md"
    click n7 "../modules/search_discovery_capture.md"
    click n8 "../modules/search_service.md"
    click n9 "../modules/search_source.md"
    click n10 "../modules/sync_manifest.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [search_service](../modules/search_service.md) |
| Outbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Outbound | [knowledge_model](../modules/knowledge_model.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_access](../modules/knowledge_storage_access.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [maintenance_protocol](../modules/maintenance_protocol.md) |
| Outbound | [maintenance_status](../modules/maintenance_status.md) |
| Outbound | [search_source](../modules/search_source.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [DiscoveryCapture](../entities/DiscoveryCapture.md) | 22 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_optional_read` | `(reads, relative, maximum, absent)` | — | — |
| `capture_discovery` | `(wiki_root: Path, reads: StorageReadSession, pages_by_path: dict, *, manifest: SyncManifest \| None = None) -> DiscoveryCapture` | — | Read one adopted owner and one selected native concepts/sections slice. |
