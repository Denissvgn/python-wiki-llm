# wiki_write_basis Module

**Path:** `src/llm_wiki_cli/services/wiki_write_basis.py`

## Description

Operation-local write hooks dispatch adopted compare-and-swap guards first,
then the active sync's new-page observer. The observer retains operation-bound
recovery evidence without granting ownership or replacing adopted full-preimage
protection. Context tokens isolate each operation and are reset on failure.

## Imports

| Source | Symbols |
|--------|---------|
| `.source_snapshot` | `SourceSnapshot` |
| `__future__` | `annotations` |
| `contextvars` | `ContextVar` |
| `pathlib` | `Path` |
| `typing` | `Protocol`, `TYPE_CHECKING` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/documentation_native.py"]
    n1["src/llm_wiki_cli/services/filesystem_guard.py"]
    n2["src/llm_wiki_cli/services/io.py"]
    n3["src/llm_wiki_cli/services/knowledge_governance.py"]
    n4["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n5["src/llm_wiki_cli/services/maintenance_protocol.py"]
    n6["src/llm_wiki_cli/services/maintenance_service.py"]
    n7["src/llm_wiki_cli/services/source_snapshot.py"]
    n8["src/llm_wiki_cli/services/sync_recovery.py"]
    n9["src/llm_wiki_cli/services/wiki_write_basis.py"]
    n0 --> n4
    n0 --> n5
    n0 --> n7
    n0 --> n9
    n1 --> n9
    n2 --> n9
    n3 --> n2
    n3 --> n9
    n4 --> n3
    n4 --> n5
    n4 --> n7
    n4 --> n9
    n5 --> n1
    n5 --> n2
    n5 --> n3
    n5 --> n7
    n5 --> n9
    n6 --> n1
    n6 --> n2
    n6 --> n3
    n6 --> n4
    n6 --> n5
    n6 --> n7
    n6 --> n9
    n7 --> n1
    n8 --> n1
    n8 --> n2
    n8 --> n5
    n8 --> n7
    n8 --> n9
    n9 --> n7
    click n0 "../modules/documentation_native.md"
    click n1 "../modules/filesystem_guard.md"
    click n2 "../modules/io.md"
    click n3 "../modules/knowledge_governance.md"
    click n4 "../modules/knowledge_orchestration.md"
    click n5 "../modules/maintenance_protocol.md"
    click n6 "../modules/maintenance_service.md"
    click n7 "../modules/source_snapshot.md"
    click n8 "../modules/sync_recovery.md"
    click n9 "../modules/wiki_write_basis.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_native](../modules/documentation_native.md) |
| Inbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Inbound | [io](../modules/io.md) |
| Inbound | [knowledge_governance](../modules/knowledge_governance.md) |
| Inbound | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| Inbound | [maintenance_protocol](../modules/maintenance_protocol.md) |
| Inbound | [maintenance_service](../modules/maintenance_service.md) |
| Inbound | [sync_recovery](../modules/sync_recovery.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [WriteBasis](../entities/WriteBasis.md) | 13 | `Protocol` | — |
| [PageWriteObserver](../entities/PageWriteObserver.md) | 22 | `Protocol` | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `before_wiki_write` | `(path: str \| Path, content: bytes \| None) -> None` | — | — |
| `after_wiki_write` | `(path: str \| Path, content: bytes \| None) -> None` | — | — |