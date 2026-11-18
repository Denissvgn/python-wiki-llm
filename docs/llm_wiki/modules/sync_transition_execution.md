# sync_transition_execution Module

**Path:** `src/llm_wiki_cli/services/sync_transition_execution.py`

## Description

Guarded execution of source-page moves, with retained failure recovery data.

## Imports

| Source | Symbols |
|--------|---------|
| `.knowledge_storage` | `MAX_EXPANDED_BYTES`, `KnowledgeStorageError` |
| `.knowledge_storage_io` | `StorageReadSession`, `read_guarded` |
| `.sync_transitions` | `PageTransitionError`, `PageTransitionPlan` |
| `__future__` | `annotations` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `llm_wiki_engine.filesystem_guard` | `atomic_write_guarded_bytes`, `atomic_write_private_bytes`, `ensure_guarded_directory`, `guarded_tree_manifest`, `remove_guarded_tree`, `unlink_guarded_bytes` |
| `llm_wiki_engine.host` | `emit` |
| `llm_wiki_engine.markdown_sections` | `normalize_markdown` |
| `llm_wiki_engine.protected_artifacts` | `ProtectedArtifactStore` |
| `llm_wiki_engine.validation` | `portable_path_key` |
| `pathlib` | `Path` |
| `stat` | `stat` |
| `uuid` | `uuid` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/knowledge_storage.py"]
    n1["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n2["src/llm_wiki_cli/services/sync_runtime.py"]
    n3["src/llm_wiki_cli/services/sync_transition_execution.py"]
    n4["src/llm_wiki_cli/services/sync_transitions.py"]
    n5["src/llm_wiki_engine/filesystem_guard.py"]
    n6["src/llm_wiki_engine/host.py"]
    n7["src/llm_wiki_engine/markdown_sections.py"]
    n8["src/llm_wiki_engine/protected_artifacts.py"]
    n9["src/llm_wiki_engine/validation.py"]
    n1 --> n0
    n1 --> n5
    n1 --> n9
    n2 --> n0
    n2 --> n1
    n2 --> n3
    n2 --> n4
    n2 --> n6
    n2 --> n7
    n2 --> n9
    n3 --> n0
    n3 --> n1
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n3 --> n9
    n4 --> n0
    n4 --> n1
    n4 --> n7
    n4 --> n9
    n8 --> n5
    n8 --> n9
    click n0 "../modules/knowledge_storage.md"
    click n1 "../modules/knowledge_storage_io.md"
    click n2 "../modules/sync_runtime.md"
    click n3 "../modules/sync_transition_execution.md"
    click n4 "../modules/sync_transitions.md"
    click n5 "../modules/filesystem_guard.md"
    click n6 "../modules/host.md"
    click n7 "../modules/markdown_sections.md"
    click n8 "../modules/protected_artifacts.md"
    click n9 "../modules/validation.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [sync_runtime](../modules/sync_runtime.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [sync_transitions](../modules/sync_transitions.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [host](../modules/host.md) |
| Outbound | [markdown_sections](../modules/markdown_sections.md) |
| Outbound | [protected_artifacts](../modules/protected_artifacts.md) |
| Outbound | [validation](../modules/validation.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [PageTransitionExecution](../entities/PageTransitionExecution.md) | 48 | — | Keep rename originals until the surrounding generation/commit succeeds. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `assert_no_pending_page_moves` | `(wiki_dir: Path) -> None` | — | — |
| `_decode` | `(content: bytes) -> str` | — | — |
