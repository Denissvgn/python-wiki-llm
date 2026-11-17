# sync_analysis_storage Module

**Path:** `src/llm_wiki_cli/services/sync_analysis_storage.py`

## Description

Bounded content-addressed persistence for advisory sync analysis captures.

## Imports

| Source | Symbols |
|--------|---------|
| `.filesystem_guard` | `atomic_write_guarded_bytes`, `ensure_guarded_directory`, `fresh_no_follow_stat`, `remove_guarded_tree`, `unlink_guarded_bytes` |
| `.io` | `first_unsafe_path_component`, `write_bytes_atomic` |
| `.knowledge_governance` | `governance_lock` |
| `.knowledge_storage_io` | `read_guarded` |
| `__future__` | `annotations` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `llm_wiki_engine.canonical_json` | `canonical_chunks` |
| `pathlib` | `Path` |
| `re` | `re` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/filesystem_guard.py"]
    n1["src/llm_wiki_cli/services/io.py"]
    n2["src/llm_wiki_cli/services/knowledge_governance.py"]
    n3["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n4["src/llm_wiki_cli/services/sync_analysis_cache.py"]
    n5["src/llm_wiki_cli/services/sync_analysis_storage.py"]
    n6["src/llm_wiki_engine/canonical_json.py"]
    n2 --> n1
    n3 --> n0
    n3 --> n1
    n4 --> n1
    n4 --> n3
    n4 --> n5
    n5 --> n0
    n5 --> n1
    n5 --> n2
    n5 --> n3
    n5 --> n6
    click n0 "../modules/filesystem_guard.md"
    click n1 "../modules/io.md"
    click n2 "../modules/knowledge_governance.md"
    click n3 "../modules/knowledge_storage_io.md"
    click n4 "../modules/sync_analysis_cache.md"
    click n5 "../modules/sync_analysis_storage.md"
    click n6 "../modules/canonical_json.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [sync_analysis_cache](../modules/sync_analysis_cache.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [knowledge_governance](../modules/knowledge_governance.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [canonical_json](../modules/canonical_json.md) |

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
