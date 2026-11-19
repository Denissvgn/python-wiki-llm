# MaintenanceProtocolError

**Location:** `src/llm_wiki_engine/maintenance_protocol.py:38`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [maintenance_protocol](../modules/maintenance_protocol.md)

## Description

_Auto-generated from `MaintenanceProtocolError` in `src/llm_wiki_engine/maintenance_protocol.py`._

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
    n0["MaintenanceProtocolError (src/llm_wiki_engine/maintenance_protocol.py)"]
    n1["ValueError"]
    n2["_invalid (src/llm_wiki_cli/services/bootstrap_recovery.py)"]
    n3["_recover (src/llm_wiki_cli/services/bootstrap_recovery.py)"]
    n4["guard_incomplete_bootstrap (src/llm_wiki_cli/services/bootstrap_recovery.py)"]
    n5["src/llm_wiki_cli/services/context_packet_builder.py"]
    n6["_capture (src/llm_wiki_cli/services/maintenance_service.py)"]
    n7["_load_recovery_snapshot (src/llm_wiki_cli/services/maintenance_service.py)"]
    n8["_outside_recovery (src/llm_wiki_cli/services/maintenance_service.py)"]
    n9["_validate_capture_roots (src/llm_wiki_cli/services/maintenance_service.py)"]
    n10["_validate_status_request (src/llm_wiki_cli/services/maintenance_service.py)"]
    n11["_validated_recovery_snapshot (src/llm_wiki_cli/services/maintenance_service.py)"]
    n12["acknowledge_maintenance_authority (src/llm_wiki_cli/services/maintenance_service.py)"]
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
    click n0 "../modules/maintenance_protocol.md"
    click n2 "../modules/bootstrap_recovery.md"
    click n3 "../modules/bootstrap_recovery.md"
    click n4 "../modules/bootstrap_recovery.md"
    click n5 "../modules/context_packet_builder.md"
    click n6 "../modules/maintenance_service.md"
    click n7 "../modules/maintenance_service.md"
    click n8 "../modules/maintenance_service.md"
    click n9 "../modules/maintenance_service.md"
    click n10 "../modules/maintenance_service.md"
    click n11 "../modules/maintenance_service.md"
    click n12 "../modules/maintenance_service.md"
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
| `_invalid` | call | [bootstrap_recovery](../modules/bootstrap_recovery.md) | 1 |
| `_invalid` | type_reference | [bootstrap_recovery](../modules/bootstrap_recovery.md) | — |
| `_recover` | call | [bootstrap_recovery](../modules/bootstrap_recovery.md) | 3 |
| `guard_incomplete_bootstrap` | call | [bootstrap_recovery](../modules/bootstrap_recovery.md) | 1 |
| `context_packet_builder` | import | [context_packet_builder](../modules/context_packet_builder.md) | — |
| `_capture` | call | [maintenance_service](../modules/maintenance_service.md) | 1 |
| `_load_recovery_snapshot` | call | [maintenance_service](../modules/maintenance_service.md) | 12 |
| `_outside_recovery` | call | [maintenance_service](../modules/maintenance_service.md) | 2 |
| `_validate_capture_roots` | call | [maintenance_service](../modules/maintenance_service.md) | 2 |
| `_validate_status_request` | call | [maintenance_service](../modules/maintenance_service.md) | 1 |
| `_validated_recovery_snapshot` | call | [maintenance_service](../modules/maintenance_service.md) | 1 |
| `acknowledge_maintenance_authority` | call | [maintenance_service](../modules/maintenance_service.md) | 7 |

> References: showing 12 of 34 logical references; 22 omitted by the 12-row generated summary limit.
