# knowledge_storage_access Module

**Path:** `src/llm_wiki_cli/services/knowledge_storage_access.py`

## Description

Captures selected native observations from explicitly adopted indexed storage. The root and manifest bind one committed generation; version dispatch chooses loose-object reads or authenticated pack ranges. Selected supporting Markdown and governance identities are checked before publication. The receipt identifies validated scope and leaves unread data and live source state unverified.

## Imports

| Source | Symbols |
|--------|---------|
| `.contracts` | `GOVERNANCE_EXTENSION_KEY` |
| `.knowledge_artifacts` | `_decode_json_object` |
| `.knowledge_envelope` | `EvaluatedEnvelope` |
| `.knowledge_governance` | `GOVERNANCE_FILENAME`, `parse_governance_ledger`, `lifecycle_state_by_uid`, `natural_key_for` |
| `.knowledge_model` | `_parse_bundle` |
| `.knowledge_packs` | `PACKED_SCHEMA`, `open_knowledge_store` |
| `.knowledge_storage` | `MAX_EXPANDED_BYTES`, `MAX_OBJECT_BYTES`, `MAX_ROOT_BYTES`, `ROOT_FILENAME`, `STORE_SCHEMA`, `KnowledgeSlice`, `KnowledgeStorageError`, `KnowledgeStoreReader`, `digest` |
| `.knowledge_storage_io` | `StorageReadSession` |
| `.sync_manifest` | `MANIFEST_FILENAME`, `SyncManifest` |
| `__future__` | `annotations` |
| `collections.abc` | `Iterable` |
| `dataclasses` | `dataclass`, `field` |
| `json` | `json` |
| `pathlib` | `Path` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/contracts.py"]
    n1["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n2["src/llm_wiki_cli/services/knowledge_envelope.py"]
    n3["src/llm_wiki_cli/services/knowledge_governance.py"]
    n4["src/llm_wiki_cli/services/knowledge_model.py"]
    n5["src/llm_wiki_cli/services/knowledge_packs.py"]
    n6["src/llm_wiki_cli/services/knowledge_storage.py"]
    n7["src/llm_wiki_cli/services/knowledge_storage_access.py"]
    n8["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n9["src/llm_wiki_cli/services/sync_manifest.py"]
    n10["src/llm_wiki_cli/services/task_context_v2.py"]
    n1 --> n0
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n1 --> n8
    n1 --> n9
    n2 --> n0
    n2 --> n4
    n3 --> n0
    n3 --> n2
    n3 --> n4
    n4 --> n0
    n4 --> n3
    n5 --> n6
    n6 --> n0
    n6 --> n2
    n6 --> n3
    n6 --> n4
    n7 --> n0
    n7 --> n1
    n7 --> n2
    n7 --> n3
    n7 --> n4
    n7 --> n5
    n7 --> n6
    n7 --> n8
    n7 --> n9
    n8 --> n6
    n10 --> n2
    n10 --> n5
    n10 --> n6
    n10 --> n7
    n10 --> n8
    click n0 "../modules/services_contracts.md"
    click n1 "../modules/knowledge_artifacts.md"
    click n2 "../modules/knowledge_envelope.md"
    click n3 "../modules/knowledge_governance.md"
    click n4 "../modules/knowledge_model.md"
    click n5 "../modules/knowledge_packs.md"
    click n6 "../modules/knowledge_storage.md"
    click n7 "../modules/knowledge_storage_access.md"
    click n8 "../modules/knowledge_storage_io.md"
    click n9 "../modules/sync_manifest.md"
    click n10 "../modules/task_context_v2.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [task_context_v2](../modules/task_context_v2.md) |
| Outbound | [services_contracts](../modules/services_contracts.md) |
| Outbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Outbound | [knowledge_envelope](../modules/knowledge_envelope.md) |
| Outbound | [knowledge_governance](../modules/knowledge_governance.md) |
| Outbound | [knowledge_model](../modules/knowledge_model.md) |
| Outbound | [knowledge_packs](../modules/knowledge_packs.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [ScopedKnowledgeRead](../entities/ScopedKnowledgeRead.md) | 27 | — | Request-owned observations that require a final authoritative recheck. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `capture_knowledge_slice` | `(wiki_dir: str \| Path, selectors: Iterable[str], *, max_bytes: int = 8388608, max_records: int = 1000, max_expanded_bytes: int = 16777216, include_graph: bool = False) -> ScopedKnowledgeRead` | — | Capture selected stored observations without enumerating the wiki tree. |