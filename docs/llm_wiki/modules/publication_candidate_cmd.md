# publication_candidate_cmd Module

**Path:** `src/llm_wiki_cli/commands/publication_candidate_cmd.py`

## Description

Local GitHub wiki candidates and exact-artifact review proposals.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `publication_cmd` |
| `..services.filesystem_guard` | `atomic_write_private_bytes`, `ensure_guarded_directory` |
| `..services.knowledge_storage` | `KnowledgeStorageError` |
| `..services.knowledge_storage_io` | `StorageReadSession`, `_absolute_path` |
| `..services.publication_candidate` | `check_publication_candidate`, `export_publication_candidate`, `review_publication_candidate`, `validate_candidate_target`, `validate_candidate_tree`, `validate_publication_receipt` |
| `..services.publication_config` | `load_publication_config`, `publication_control_overlap`, `publication_input_controls` |
| `..services.publication_contracts` | `validate_publication_basis` |
| `..services.publication_impact` | `MAX_JSON_BYTES`, `read_publication_document` |
| `..services.source_snapshot` | `_is_package_marker` |
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `pathlib` | `Path` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/docs_cmd.py"]
    n1["src/llm_wiki_cli/commands/publication_candidate_cmd.py"]
    n2["src/llm_wiki_cli/commands/publication_cmd.py"]
    n3["src/llm_wiki_cli/services/filesystem_guard.py"]
    n4["src/llm_wiki_cli/services/knowledge_storage.py"]
    n5["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n6["src/llm_wiki_cli/services/publication_candidate.py"]
    n7["src/llm_wiki_cli/services/publication_config.py"]
    n8["src/llm_wiki_cli/services/publication_contracts.py"]
    n9["src/llm_wiki_cli/services/publication_impact.py"]
    n10["src/llm_wiki_cli/services/source_snapshot.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n1 --> n7
    n1 --> n8
    n1 --> n9
    n1 --> n10
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n2 --> n7
    n2 --> n8
    n2 --> n9
    n2 --> n10
    n5 --> n3
    n5 --> n4
    n6 --> n3
    n6 --> n5
    n6 --> n7
    n6 --> n8
    n6 --> n9
    n8 --> n7
    n9 --> n5
    n9 --> n7
    n9 --> n8
    n10 --> n3
    click n0 "../modules/docs_cmd.md"
    click n1 "../modules/publication_candidate_cmd.md"
    click n2 "../modules/publication_cmd.md"
    click n3 "../modules/filesystem_guard.md"
    click n4 "../modules/knowledge_storage.md"
    click n5 "../modules/knowledge_storage_io.md"
    click n6 "../modules/publication_candidate.md"
    click n7 "../modules/publication_config.md"
    click n8 "../modules/publication_contracts.md"
    click n9 "../modules/publication_impact.md"
    click n10 "../modules/source_snapshot.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [docs_cmd](../modules/docs_cmd.md) |
| Outbound | [publication_cmd](../modules/publication_cmd.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [publication_candidate](../modules/publication_candidate.md) |
| Outbound | [publication_config](../modules/publication_config.md) |
| Outbound | [publication_contracts](../modules/publication_contracts.md) |
| Outbound | [publication_impact](../modules/publication_impact.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_common` | `(parser)` | — | — |
| `add_commands` | `(docs_sub)` | — | — |
| `_path` | `(args, value)` | — | — |
| `_read` | `(args, value)` | — | — |
| `_basis_files` | `(basis)` | — | — |
| `_guard_destination` | `(args, value, *, receipt = None, baseline = None)` | — | — |
| `_write` | `(args, destination, value)` | — | — |
| `run` | `(args)` | — | — |
