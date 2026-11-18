# sync_analysis_storage Module

**Path:** `src/llm_wiki_cli/services/sync_analysis_storage.py`

## Description

Bounded content-addressed persistence for advisory sync analysis captures.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `llm_wiki_engine.canonical_json` | `canonical_chunks` |
| `llm_wiki_engine.filesystem_guard` | `atomic_write_guarded_bytes`, `ensure_guarded_directory`, `fresh_no_follow_stat`, `remove_guarded_tree`, `unlink_guarded_bytes` |
| `llm_wiki_engine.io` | `first_unsafe_path_component`, `write_bytes_atomic` |
| `llm_wiki_engine.knowledge_governance` | `governance_lock` |
| `llm_wiki_engine.knowledge_storage_io` | `read_guarded` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/sync_analysis_cache.py"]
    n1["src/llm_wiki_cli/services/sync_analysis_storage.py"]
    n2["src/llm_wiki_engine/canonical_json.py"]
    n3["src/llm_wiki_engine/filesystem_guard.py"]
    n4["src/llm_wiki_engine/io.py"]
    n5["src/llm_wiki_engine/knowledge_governance.py"]
    n6["src/llm_wiki_engine/knowledge_storage_io.py"]
    n0 --> n1
    n0 --> n4
    n0 --> n6
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n5 --> n4
    n6 --> n3
    n6 --> n4
    click n0 "../modules/sync_analysis_cache.md"
    click n1 "../modules/sync_analysis_storage.md"
    click n2 "../modules/canonical_json.md"
    click n3 "../modules/filesystem_guard.md"
    click n4 "../modules/io.md"
    click n5 "../modules/knowledge_governance.md"
    click n6 "../modules/knowledge_storage_io.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [sync_analysis_cache](../modules/sync_analysis_cache.md) |
| Outbound | [canonical_json](../modules/canonical_json.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [knowledge_governance](../modules/knowledge_governance.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_decode_json` | `(raw)` | — | — |
| `_container_children` | `(node, *, parts)` | — | — |
| `measure` | `(payload, maximum)` | — | Hash the existing canonical encoding without allocating a whole capture. |
| `_small_bytes` | `(value, maximum)` | — | — |
| `_objects` | `(path)` | — | — |
| `_pending` | `(path)` | — | — |
| `_pending_owner_bytes` | `(path)` | — | — |
| `_current_root` | `(path, maximum)` | — | — |
| `_root_shards` | `(raw)` | — | — |
| `_pending_records` | `(path)` | — | — |
| `_prepare_pending` | `(path)` | — | — |
| `_record_pending` | `(path, records, logical_hash, size)` | — | — |
| `_recover_pending` | `(path, root_limit)` | — | — |
| `_previous_shards` | `(path, root_limit)` | — | — |
| `_remove_superseded_shards` | `(path, published, references, root_limit)` | — | — |
| `_journal_superseded` | `(path, references, owned = None)` | — | — |
| `save` | `(path: Path, payload, *, root_limit: int, total_limit: int, writer = write_bytes_atomic)` | — | Publish all immutable shards before atomically replacing their catalog. |
| `_save_locked` | `(path: Path, payload, *, root_limit: int, total_limit: int, writer)` | — | — |
| `load` | `(path: Path, *, root_limit: int, total_limit: int) -> Any` | — | Read legacy captures or verify every bounded subtree before reuse. |
