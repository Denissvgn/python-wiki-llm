# search_source Module

**Path:** `src/llm_wiki_cli/services/search_source.py`

## Description

Explicit bounded static-source text indexing for canonical module candidates.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_artifacts` | `_decode_json_object` |
| `.knowledge_storage` | `MAX_EXPANDED_BYTES` |
| `.knowledge_storage_io` | `StorageReadSession` |
| `.source_snapshot` | `SourceSnapshot` |
| `.sync_manifest` | `MANIFEST_FILENAME`, `SyncManifest` |
| `__future__` | `annotations` |
| `collections.abc` | `Iterable`, `Mapping` |
| `hashlib` | `hashlib` |
| `llm_wiki_engine.search_rank` | `MAX_SEARCH_BYTES`, `MAX_SEARCH_PAGES` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n1["src/llm_wiki_cli/services/knowledge_storage.py"]
    n2["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n3["src/llm_wiki_cli/services/search_discovery_capture.py"]
    n4["src/llm_wiki_cli/services/search_service.py"]
    n5["src/llm_wiki_cli/services/search_source.py"]
    n6["src/llm_wiki_cli/services/source_snapshot.py"]
    n7["src/llm_wiki_cli/services/sync_manifest.py"]
    n8["src/llm_wiki_engine/search_rank.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n7
    n2 --> n1
    n3 --> n0
    n3 --> n1
    n3 --> n2
    n3 --> n5
    n3 --> n7
    n4 --> n1
    n4 --> n2
    n4 --> n3
    n4 --> n5
    n4 --> n6
    n4 --> n8
    n5 --> n0
    n5 --> n1
    n5 --> n2
    n5 --> n6
    n5 --> n7
    n5 --> n8
    n7 --> n1
    n7 --> n2
    n7 --> n6
    click n0 "../modules/knowledge_artifacts.md"
    click n1 "../modules/knowledge_storage.md"
    click n2 "../modules/knowledge_storage_io.md"
    click n3 "../modules/search_discovery_capture.md"
    click n4 "../modules/search_service.md"
    click n5 "../modules/search_source.md"
    click n6 "../modules/source_snapshot.md"
    click n7 "../modules/sync_manifest.md"
    click n8 "../modules/search_rank.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [search_discovery_capture](../modules/search_discovery_capture.md) |
| Inbound | [search_service](../modules/search_service.md) |
| Outbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |
| Outbound | [search_rank](../modules/search_rank.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `augment_module_page` | `(page: Mapping[str, Any], source_path: str, raw: bytes) -> dict[str, Any]` | — | Preserve wiki identity separately from the derived searchable text. |
| `capture_source_index` | `(pages: Iterable[dict[str, Any]], snapshot: SourceSnapshot, wiki_reads: StorageReadSession, source_reads: StorageReadSession, *, manifest: SyncManifest \| None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]` | — | Index only manifest-owned module sources inside the captured live boundary. |
| `captured_manifest` | `(reads: StorageReadSession) -> SyncManifest` | — | — |
| `source_page_selected` | `(path: str, snapshot: SourceSnapshot, manifest: SyncManifest) -> bool` | — | — |
