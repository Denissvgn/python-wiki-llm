# sync_transition_execution Module

**Path:** `src/llm_wiki_cli/services/sync_transition_execution.py`

## Description

Guarded execution of source-page moves, with retained failure recovery data.

## Imports

| Source | Symbols |
|--------|---------|
| `.filesystem_guard` | `atomic_write_guarded_bytes`, `atomic_write_private_bytes`, `ensure_guarded_directory`, `guarded_tree_manifest`, `remove_guarded_tree`, `unlink_guarded_bytes` |
| `.knowledge_storage` | `MAX_EXPANDED_BYTES`, `KnowledgeStorageError` |
| `.knowledge_storage_io` | `StorageReadSession`, `read_guarded` |
| `.markdown_sections` | `normalize_markdown` |
| `.protected_artifacts` | `ProtectedArtifactStore` |
| `.sync_transitions` | `PageTransitionError`, `PageTransitionPlan` |
| `.validation` | `portable_path_key` |
| `__future__` | `annotations` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `pathlib` | `Path` |
| `stat` | `stat` |
| `sys` | `sys` |
| `uuid` | `uuid` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/sync_cmd.py"]
    n1["src/llm_wiki_cli/services/filesystem_guard.py"]
    n2["src/llm_wiki_cli/services/knowledge_storage.py"]
    n3["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n4["src/llm_wiki_cli/services/markdown_sections.py"]
    n5["src/llm_wiki_cli/services/protected_artifacts.py"]
    n6["src/llm_wiki_cli/services/sync_transition_execution.py"]
    n7["src/llm_wiki_cli/services/sync_transitions.py"]
    n8["src/llm_wiki_cli/services/validation.py"]
    n0 --> n4
    n0 --> n6
    n0 --> n7
    n0 --> n8
    n3 --> n1
    n3 --> n2
    n3 --> n8
    n5 --> n1
    n5 --> n8
    n6 --> n1
    n6 --> n2
    n6 --> n3
    n6 --> n4
    n6 --> n5
    n6 --> n7
    n6 --> n8
    n7 --> n2
    n7 --> n3
    n7 --> n4
    n7 --> n8
    click n0 "../modules/sync_cmd.md"
    click n1 "../modules/filesystem_guard.md"
    click n2 "../modules/knowledge_storage.md"
    click n3 "../modules/knowledge_storage_io.md"
    click n4 "../modules/markdown_sections.md"
    click n5 "../modules/protected_artifacts.md"
    click n6 "../modules/sync_transition_execution.md"
    click n7 "../modules/sync_transitions.md"
    click n8 "../modules/validation.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [sync_cmd](../modules/sync_cmd.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [markdown_sections](../modules/markdown_sections.md) |
| Outbound | [protected_artifacts](../modules/protected_artifacts.md) |
| Outbound | [sync_transitions](../modules/sync_transitions.md) |
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
