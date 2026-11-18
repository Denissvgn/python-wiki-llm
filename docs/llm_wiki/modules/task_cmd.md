# task_cmd Module

**Path:** `src/llm_wiki_cli/commands/task_cmd.py`

## Description

Adapts explicit task requests and optional profiles to canonical task context. Workspace roots, counter configuration and full-inventory permission are operator options. A response that cannot fit emits no partial context, and read proposals remain data for the host to consider.

## Imports

| Source | Symbols |
|--------|---------|
| `..` | `api` |
| `..services.knowledge_storage` | `KnowledgeStorageError` |
| `..services.knowledge_storage_io` | `read_guarded` |
| `..services.token_counting` | `LocalTokenizerCounter` |
| `json` | `json` |
| `llm_wiki_engine.filesystem_guard` | `atomic_write_guarded_bytes`, `ensure_guarded_directory` |
| `llm_wiki_engine.io` | `write_text_output`, `write_utf8_stdout`, `first_unsafe_path_component` |
| `llm_wiki_engine.request_json` | `load_request` |
| `pathlib` | `Path` |
| `stat` | `stat` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/cli.py"]
    n2["src/llm_wiki_cli/commands/task_cmd.py"]
    n3["src/llm_wiki_cli/services/knowledge_storage.py"]
    n4["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n5["src/llm_wiki_cli/services/token_counting.py"]
    n6["src/llm_wiki_engine/filesystem_guard.py"]
    n7["src/llm_wiki_engine/io.py"]
    n8["src/llm_wiki_engine/request_json.py"]
    n0 --> n3
    n0 --> n5
    n1 --> n2
    n2 --> n0
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n2 --> n6
    n2 --> n7
    n2 --> n8
    n4 --> n3
    n4 --> n6
    n4 --> n7
    click n0 "../modules/api.md"
    click n1 "../modules/cli.md"
    click n2 "../modules/task_cmd.md"
    click n3 "../modules/knowledge_storage.md"
    click n4 "../modules/knowledge_storage_io.md"
    click n5 "../modules/token_counting.md"
    click n6 "../modules/filesystem_guard.md"
    click n7 "../modules/io.md"
    click n8 "../modules/request_json.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [api](../modules/api.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [token_counting](../modules/token_counting.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [request_json](../modules/request_json.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_safe_absolute` | `(value)` | — | — |
| `_parent_stamps` | `(path)` | — | — |
| `_compact_outputs` | `(args)` | — | Pin explicit artifact destinations before any workspace capture. |
| `_publish_compact_outputs` | `(outputs, result)` | — | — |
| `run` | `(args)` | — | — |
