# ContextPacketPathPolicyError

**Location:** `src/llm_wiki_engine/context_packet.py:191`
**Kind:** Class
**Bases:** `ContextPacketError`
**Module:** [context_packet](../modules/context_packet.md)

## Description

A structural packet field violates its declared path policy.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str, *, relative_path: str \| None = None)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextPacketPathPolicyError (src/llm_wiki_engine/context_packet.py)"]
    n1["ContextPacketError (src/llm_wiki_engine/context_packet.py)"]
    n2["capture_context_read (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n3["confirmed_missing_source_paths (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n4["_path_policy_receipt (src/llm_wiki_engine/context_packet.py)"]
    n5["_reject_machine_local_path (src/llm_wiki_engine/context_packet.py)"]
    n6["_repository_path (src/llm_wiki_engine/context_packet.py)"]
    n7["_validate_context_packet_bytes (src/llm_wiki_engine/context_packet.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/context_packet.md"
    click n1 "../modules/context_packet.md"
    click n2 "../modules/context_packet_builder.md"
    click n3 "../modules/context_packet_builder.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_packet.md"
    click n6 "../modules/context_packet.md"
    click n7 "../modules/context_packet.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_packet](../modules/context_packet.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ContextPacketError` | [context_packet](../modules/context_packet.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `capture_context_read` | call | [context_packet_builder](../modules/context_packet_builder.md) | 1 |
| `confirmed_missing_source_paths` | call | [context_packet_builder](../modules/context_packet_builder.md) | 1 |
| `_path_policy_receipt` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_reject_machine_local_path` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_repository_path` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_validate_context_packet_bytes` | call | [context_packet](../modules/context_packet.md) | 1 |
