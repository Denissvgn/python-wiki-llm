# publication_cmd Module

**Path:** `src/llm_wiki_cli/commands/publication_cmd.py`

## Description

Read-only public wiki impact and explicit review record preparation.

## Imports

| Source | Symbols |
|--------|---------|
| `..services.filesystem_guard` | `atomic_write_private_bytes`, `ensure_guarded_directory` |
| `..services.knowledge_evidence` | `hash_json` |
| `..services.knowledge_storage` | `KnowledgeStorageError` |
| `..services.knowledge_storage_io` | `StorageReadSession`, `_absolute_path` |
| `..services.publication_config` | `load_publication_config` |
| `..services.publication_impact` | `IMPACT_SCHEMA`, `MAX_JSON_BYTES`, `capture_publication_basis`, `compare_publication_impact`, `read_publication_document`, `render_publication_impact`, `resolve_publication_finding` |
| `__future__` | `annotations` |
| `argparse` | `argparse` |
| `json` | `json` |
| `pathlib` | `Path` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/docs_cmd.py"]
    n2["src/llm_wiki_cli/commands/publication_candidate_cmd.py"]
    n3["src/llm_wiki_cli/commands/publication_cmd.py"]
    n4["src/llm_wiki_cli/services/filesystem_guard.py"]
    n5["src/llm_wiki_cli/services/knowledge_evidence.py"]
    n6["src/llm_wiki_cli/services/knowledge_storage.py"]
    n7["src/llm_wiki_cli/services/knowledge_storage_io.py"]
    n8["src/llm_wiki_cli/services/publication_config.py"]
    n9["src/llm_wiki_cli/services/publication_impact.py"]
    n0 --> n1
    n0 --> n3
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n2 --> n3
    n2 --> n4
    n2 --> n6
    n2 --> n7
    n2 --> n8
    n2 --> n9
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n3 --> n9
    n7 --> n4
    n7 --> n6
    n9 --> n5
    n9 --> n7
    n9 --> n8
    click n0 "../modules/cli.md"
    click n1 "../modules/docs_cmd.md"
    click n2 "../modules/publication_candidate_cmd.md"
    click n3 "../modules/publication_cmd.md"
    click n4 "../modules/filesystem_guard.md"
    click n5 "../modules/knowledge_evidence.md"
    click n6 "../modules/knowledge_storage.md"
    click n7 "../modules/knowledge_storage_io.md"
    click n8 "../modules/publication_config.md"
    click n9 "../modules/publication_impact.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Inbound | [docs_cmd](../modules/docs_cmd.md) |
| Inbound | [publication_candidate_cmd](../modules/publication_candidate_cmd.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [knowledge_storage](../modules/knowledge_storage.md) |
| Outbound | [knowledge_storage_io](../modules/knowledge_storage_io.md) |
| Outbound | [publication_config](../modules/publication_config.md) |
| Outbound | [publication_impact](../modules/publication_impact.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_common` | `(parser, *, child = False)` | — | — |
| `add_impact_command` | `(docs_sub)` | — | — |
| `_artifact_path` | `(args, value)` | — | — |
| `_same_file` | `(left: Path, right: Path) -> bool` | — | — |
| `_inside_input_tree` | `(destination: Path, source: Path) -> bool` | — | — |
| `_declared_files` | `(config)` | — | — |
| `_document_bytes` | `(value)` | — | — |
| `_write` | `(args, value, *, expected_document = None, input_basis = None)` | — | — |
| `_error_report` | `(message)` | — | — |
| `run` | `(args)` | — | — |
