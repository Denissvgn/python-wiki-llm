# storage_spool Module

**Path:** `src/llm_wiki_engine/storage_spool.py`

## Description

Provides request-owned byte and JSON spill buffers with bounded metadata and disk quotas. Stored byte commitments are verified on reads. A staged artifact exposes its original byte interface while its owner keeps the spool context open; closing that context releases the private data.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_storage` | `MAX_OBJECT_BYTES`, `MAX_EXPANDED_BYTES`, `KnowledgeStorageError`, `canonical_bytes` |
| `__future__` | `annotations` |
| `collections` | `OrderedDict` |
| `collections.abc` | `Iterator`, `MutableMapping` |
| `dataclasses` | `dataclass` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `pickle` | `pickle` |
| `tempfile` | `tempfile` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/sync_runtime.py"]
    n1["src/llm_wiki_engine/knowledge_artifacts.py"]
    n2["src/llm_wiki_engine/knowledge_audit.py"]
    n3["src/llm_wiki_engine/knowledge_packs.py"]
    n4["src/llm_wiki_engine/knowledge_storage.py"]
    n5["src/llm_wiki_engine/knowledge_storage_lifecycle.py"]
    n6["src/llm_wiki_engine/knowledge_stream_audit.py"]
    n7["src/llm_wiki_engine/maintenance_protocol.py"]
    n8["src/llm_wiki_engine/storage_spool.py"]
    n0 --> n1
    n0 --> n4
    n0 --> n5
    n0 --> n7
    n0 --> n8
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n7
    n1 --> n8
    n2 --> n4
    n2 --> n8
    n3 --> n1
    n3 --> n4
    n3 --> n8
    n4 --> n2
    n5 --> n1
    n5 --> n3
    n5 --> n4
    n5 --> n7
    n5 --> n8
    n6 --> n2
    n6 --> n3
    n6 --> n4
    n6 --> n8
    n7 --> n3
    n7 --> n4
    n7 --> n8
    n8 --> n4
    click n0 "../modules/sync_runtime.md"
    click n1 "../modules/knowledge_artifacts.md"
    click n2 "../modules/knowledge_audit.md"
    click n3 "../modules/knowledge_packs.md"
    click n4 "../modules/knowledge_storage.md"
    click n5 "../modules/knowledge_storage_lifecycle.md"
    click n6 "../modules/knowledge_stream_audit.md"
    click n7 "../modules/maintenance_protocol.md"
    click n8 "../modules/storage_spool.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [sync_runtime](../modules/sync_runtime.md) |
| Inbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Inbound | [knowledge_audit](../modules/knowledge_audit.md) |
| Inbound | [knowledge_packs](../modules/knowledge_packs.md) |
| Inbound | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) |
| Inbound | [knowledge_stream_audit](../modules/knowledge_stream_audit.md) |
| Inbound | [maintenance_protocol](../modules/maintenance_protocol.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [ByteSpool](../entities/ByteSpool.md) | 21 | `MutableMapping[str, bytes]` | One private file, bounded index and byte quota, with synchronous backpressure. |
| [SpooledArtifactWrite](../entities/SpooledArtifactWrite.md) | 103 | — | Byte-compatible planned write whose buffers live in a request-owned spool. |
| [JsonSpool](../entities/JsonSpool.md) | 139 | `MutableMapping` | JSON values backed by one explicitly owned byte spool. |
| [DecodeCache](../entities/DecodeCache.md) | 162 | `MutableMapping` | Bound encoded cache weight; never reuse this cache across captures. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `spool_write` | `(write, spool: ByteSpool) -> SpooledArtifactWrite` | — | — |
