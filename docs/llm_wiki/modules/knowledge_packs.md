# knowledge_packs Module

**Path:** `src/llm_wiki_cli/services/knowledge_packs.py`

## Description

Implements the explicit packed knowledge v3 format while retaining the v2 logical object model. Stable hash buckets group objects into bounded immutable ZIP files. Separate bounded catalogs map logical object hashes to member coordinates and pack buckets to container commitments. Selected reads authenticate individual ranges and disclose unread archive scope; full reads additionally validate complete ZIP structure, pack hashes and exact membership. Both stored and individually compressed members preserve the same native records.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_storage` | `COLLECTIONS`, `MAX_EXPANDED_BYTES`, `MAX_OBJECT_BYTES`, `MAX_READ_OBJECTS`, `MAX_ROOT_BYTES`, `OBJECT_SCHEMA`, `KnowledgeSlice`, `KnowledgeStorageError`, `KnowledgeStorePlan`, `KnowledgeStoreReader`, `build_knowledge_store`, `canonical_bytes`, `decode_bytes`, `digest`, `parse_store_root`, `_fields`, `_hash`, `_integer` |
| `__future__` | `annotations` |
| `collections` | `defaultdict` |
| `collections.abc` | `Callable`, `Mapping` |
| `hashlib` | `hashlib` |
| `io` | `io` |
| `json` | `json` |
| `re` | `re` |
| `struct` | `struct` |
| `typing` | `Any`, `NoReturn` |
| `zipfile` | `zipfile` |
| `zlib` | `zlib` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n1["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n2["src/llm_wiki_cli/services/knowledge_packs.py"]
    n3["src/llm_wiki_cli/services/knowledge_reuse.py"]
    n4["src/llm_wiki_cli/services/knowledge_storage.py"]
    n5["src/llm_wiki_cli/services/knowledge_storage_access.py"]
    n6["src/llm_wiki_cli/services/knowledge_storage_diagnostics.py"]
    n7["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n8["src/llm_wiki_cli/services/task_context_v2.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n2 --> n4
    n3 --> n1
    n3 --> n2
    n5 --> n1
    n5 --> n2
    n5 --> n4
    n6 --> n1
    n6 --> n2
    n6 --> n4
    n6 --> n7
    n7 --> n1
    n7 --> n2
    n7 --> n4
    n8 --> n2
    n8 --> n4
    n8 --> n5
    click n0 "../modules/documentation_wiki_input.md"
    click n1 "../modules/knowledge_artifacts.md"
    click n2 "../modules/knowledge_packs.md"
    click n3 "../modules/knowledge_reuse.md"
    click n4 "../modules/knowledge_storage.md"
    click n5 "../modules/knowledge_storage_access.md"
    click n6 "../modules/knowledge_storage_diagnostics.md"
    click n7 "../modules/knowledge_storage_lifecycle.md"
    click n8 "../modules/task_context_v2.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| Inbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Inbound | [knowledge_reuse](../modules/knowledge_reuse.md) |
| Inbound | [knowledge_storage_access](../modules/knowledge_storage_access.md) |
| Inbound | [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md) |
| Inbound | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) |
| Inbound | [task_context_v2](../modules/task_context_v2.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [PackedKnowledgeStoreReader](../entities/PackedKnowledgeStoreReader.md) | 328 | `KnowledgeStoreReader` | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_fail` | `(field: str, message: str, code: str = 'storage-invalid') -> NoReturn` | — | — |
| `_bits` | `(hexadecimal: str) -> str` | — | — |
| `_bucket` | `(member: str) -> str` | — | — |
| `_member_name` | `(raw: bytes) -> str` | — | — |
| `pack_path` | `(descriptor: Mapping[str, Any]) -> str` | — | — |
| `index_path` | `(commitment: str) -> str` | — | — |
| `_index_descriptor` | `(value: Any) -> dict[str, Any]` | — | — |
| `_pack_descriptor` | `(value: Any) -> dict[str, Any]` | — | — |
| `parse_packed_root` | `(raw: bytes) -> dict[str, Any]` | — | — |
| `_zip_bytes` | `(members: Mapping[str, bytes], compression: str) -> tuple[bytes, dict[str, list[Any]]]` | — | — |
| `build_packed_store` | `(payload: Mapping[str, Any], *, compression: str = 'stored') -> KnowledgeStorePlan` | — | — |
| `_coordinates` | `(value: Any) -> tuple[str, list[Any]]` | — | — |
| `_position` | `(value: Any, descriptor: dict[str, Any]) -> tuple[dict[str, Any], list[Any]]` | — | — |
| `decode_member` | `(raw: bytes, position: list[Any], compression: str, commitment: str) -> bytes` | — | — |
| `validate_pack` | `(raw: bytes, descriptor: dict[str, Any], compression: str) -> dict[str, list[Any]]` | — | Validate a complete bounded archive, including all otherwise unread metadata. |
| `inspect_pack` | `(raw: bytes, relative: str) -> dict[str, Any]` | — | Recognize a complete generated archive for diagnostics and orphan cleanup. |
| `open_knowledge_store` | `(root_bytes: bytes, read_file: Callable[[str, int], bytes], *, read_range: RangeReader \| None = None, **limits) -> KnowledgeStoreReader` | — | — |
| `physical_objects` | `(reader: KnowledgeStoreReader) -> Mapping[str, bytes]` | — | — |
| `build_storage` | `(payload: Mapping[str, Any], storage_format: str) -> KnowledgeStorePlan` | — | — |