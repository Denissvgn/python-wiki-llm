# ContextPacketPathPolicyError

**Location:** `src/llm_wiki_cli/services/context_packet.py:262`
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
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextPacketPathPolicyError (src/llm_wiki_cli/services/context_packet.py)"]
    n1["ContextPacketError (src/llm_wiki_cli/services/context_packet.py)"]
    n2["_reject_machine_local_path (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_repository_path (src/llm_wiki_cli/services/context_packet.py)"]
    n4["capture_context_read (src/llm_wiki_cli/services/context_packet.py)"]
    n5["validate_context_packet (src/llm_wiki_cli/services/context_packet.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/context_packet.md"
    click n1 "../modules/context_packet.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_packet.md"
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
| `_reject_machine_local_path` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_repository_path` | call | [context_packet](../modules/context_packet.md) | 1 |
| `capture_context_read` | call | [context_packet](../modules/context_packet.md) | 1 |
| `validate_context_packet` | call | [context_packet](../modules/context_packet.md) | 1 |
