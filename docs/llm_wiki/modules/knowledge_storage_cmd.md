# knowledge_storage_cmd Module

**Path:** `src/llm_wiki_cli/commands/knowledge_storage_cmd.py`

## Description

Adapts explicit storage migration, recovery, export, cleanup, diagnostics and logical review operations to the CLI. It delegates validation and mutation to their owning services, emits structured output and preserves explicit adoption and failure reporting. Logical inspection and comparison use bounded compact JSON output.

## Imports

| Source | Symbols |
|--------|---------|
| `..services.knowledge_storage_diagnostics` | `storage_report`, `review_storage` |
| `..services.knowledge_storage_lifecycle` | `migrate_knowledge_storage`, `recover_knowledge_storage`, `export_knowledge_v1`, `prune_knowledge_storage` |
| `..services.knowledge_stream_audit` | `audit_knowledge_stream` |
| `.knowledge_cmd` | `_wiki_root` |
| `__future__` | `annotations` |
| `json` | `json` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n1["src/llm_wiki_cli/commands/knowledge_storage_cmd.py"]
    n2["src/llm_wiki_cli/services/knowledge_storage_diagnostics.py"]
    n3["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n4["src/llm_wiki_cli/services/knowledge_stream_audit.py"]
    n0 --> n1
    n1 --> n0
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n2 --> n3
    click n0 "../modules/knowledge_cmd.md"
    click n1 "../modules/knowledge_storage_cmd.md"
    click n2 "../modules/knowledge_storage_diagnostics.md"
    click n3 "../modules/knowledge_storage_lifecycle.md"
    click n4 "../modules/knowledge_stream_audit.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [knowledge_cmd](../modules/knowledge_cmd.md) |
| Outbound | [knowledge_cmd](../modules/knowledge_cmd.md) |
| Outbound | [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md) |
| Outbound | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) |
| Outbound | [knowledge_stream_audit](../modules/knowledge_stream_audit.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args) -> None` | — | — |