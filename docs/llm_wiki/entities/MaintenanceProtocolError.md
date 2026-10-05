# MaintenanceProtocolError

**Location:** `src/llm_wiki_cli/services/maintenance_protocol.py:30`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [maintenance_protocol](../modules/maintenance_protocol.md)

## Description

_Auto-generated from `MaintenanceProtocolError` in `src/llm_wiki_cli/services/maintenance_protocol.py`._

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(reason: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["MaintenanceProtocolError (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/commands/sync_cmd.py"]
    n3["src/llm_wiki_cli/services/knowledge_loader.py"]
    n4["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n5["governance_writer_lock (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n6["guard_maintenance_owner (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n7["load_adoption_marker (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n8["maintenance_write_operation (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n9["save_recovery_snapshot (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n10["snapshot_wiki (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n11["unlink_maintenance_page (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n12["WikiWriteBasis.after_write (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n13["WikiWriteBasis.assert_current (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    n13 --> n0
    click n0 "../modules/maintenance_protocol.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/knowledge_loader.md"
    click n4 "../modules/knowledge_storage_lifecycle.md"
    click n5 "../modules/maintenance_protocol.md"
    click n6 "../modules/maintenance_protocol.md"
    click n7 "../modules/maintenance_protocol.md"
    click n8 "../modules/maintenance_protocol.md"
    click n9 "../modules/maintenance_protocol.md"
    click n10 "../modules/maintenance_protocol.md"
    click n11 "../modules/maintenance_protocol.md"
    click n12 "../modules/maintenance_protocol.md"
    click n13 "../modules/maintenance_protocol.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [maintenance_protocol](../modules/maintenance_protocol.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `sync_cmd` | import | [sync_cmd](../modules/sync_cmd.md) | — |
| `knowledge_loader` | import | [knowledge_loader](../modules/knowledge_loader.md) | — |
| `knowledge_storage_lifecycle` | import | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | — |
| `governance_writer_lock` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 1 |
| `guard_maintenance_owner` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 7 |
| `load_adoption_marker` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 1 |
| `maintenance_write_operation` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 1 |
| `save_recovery_snapshot` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 1 |
| `snapshot_wiki` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 1 |
| `unlink_maintenance_page` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 1 |
| `WikiWriteBasis.after_write` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 2 |
| `WikiWriteBasis.assert_current` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 1 |

> References: showing 12 of 23 logical references; 11 omitted by the 12-row generated summary limit.
