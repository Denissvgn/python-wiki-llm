# wiki_write_basis Module

**Path:** `src/llm_wiki_engine/wiki_write_basis.py`

## Description

Operation-local write hooks dispatch adopted compare-and-swap guards first,
then the active sync's new-page observer. The observer retains operation-bound
recovery evidence without granting ownership or replacing adopted full-preimage
protection. Context tokens isolate each operation and are reset on failure.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections.abc` | `Mapping`, `MutableMapping` |
| `contextvars` | `ContextVar` |
| `pathlib` | `Path` |
| `typing` | `Any`, `Protocol` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/bootstrap_recovery.py"]
    n1["src/llm_wiki_cli/services/documentation_native.py"]
    n2["src/llm_wiki_cli/services/knowledge_governance.py"]
    n3["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n4["src/llm_wiki_cli/services/maintenance_protocol.py"]
    n5["src/llm_wiki_cli/services/maintenance_service.py"]
    n6["src/llm_wiki_cli/services/sync_recovery.py"]
    n7["src/llm_wiki_cli/services/sync_runtime.py"]
    n8["src/llm_wiki_engine/filesystem_guard.py"]
    n9["src/llm_wiki_engine/io.py"]
    n10["src/llm_wiki_engine/wiki_write_basis.py"]
    n0 --> n2
    n0 --> n4
    n0 --> n8
    n0 --> n10
    n1 --> n3
    n1 --> n4
    n1 --> n10
    n2 --> n9
    n2 --> n10
    n3 --> n2
    n3 --> n4
    n3 --> n10
    n4 --> n0
    n4 --> n2
    n4 --> n3
    n4 --> n8
    n4 --> n9
    n4 --> n10
    n5 --> n2
    n5 --> n3
    n5 --> n4
    n5 --> n8
    n5 --> n9
    n5 --> n10
    n6 --> n2
    n6 --> n4
    n6 --> n8
    n6 --> n9
    n6 --> n10
    n7 --> n2
    n7 --> n3
    n7 --> n4
    n7 --> n6
    n7 --> n9
    n7 --> n10
    n8 --> n10
    n9 --> n10
    click n0 "../modules/bootstrap_recovery.md"
    click n1 "../modules/documentation_native.md"
    click n2 "../modules/knowledge_governance.md"
    click n3 "../modules/knowledge_orchestration.md"
    click n4 "../modules/maintenance_protocol.md"
    click n5 "../modules/maintenance_service.md"
    click n6 "../modules/sync_recovery.md"
    click n7 "../modules/sync_runtime.md"
    click n8 "../modules/filesystem_guard.md"
    click n9 "../modules/io.md"
    click n10 "../modules/wiki_write_basis.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [bootstrap_recovery](../modules/bootstrap_recovery.md) |
| Inbound | [documentation_native](../modules/documentation_native.md) |
| Inbound | [knowledge_governance](../modules/knowledge_governance.md) |
| Inbound | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| Inbound | [maintenance_protocol](../modules/maintenance_protocol.md) |
| Inbound | [maintenance_service](../modules/maintenance_service.md) |
| Inbound | [sync_recovery](../modules/sync_recovery.md) |
| Inbound | [sync_runtime](../modules/sync_runtime.md) |
| Inbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Inbound | [io](../modules/io.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [WriteBasis](../entities/WriteBasis.md) | 11 | `Protocol` | — |
| [PageWriteObserver](../entities/PageWriteObserver.md) | 23 | `Protocol` | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `before_wiki_write` | `(path: str \| Path, content: bytes \| None) -> None` | — | — |
| `after_wiki_write` | `(path: str \| Path, content: bytes \| None) -> None` | — | — |
