# ContextPacketUnavailableError

**Location:** `src/llm_wiki_cli/services/context_packet.py:253`
**Kind:** Class
**Bases:** `ContextPacketError`
**Module:** [context_packet](../modules/context_packet.md)

## Description

A required read-only packet capability is unavailable.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(message: str, *, field: str = 'context')` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextPacketUnavailableError (src/llm_wiki_cli/services/context_packet.py)"]
    n1["ContextPacketError (src/llm_wiki_cli/services/context_packet.py)"]
    n2["_fit_knowledge_packet_response (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_guard_windows_inputs (src/llm_wiki_cli/services/context_packet.py)"]
    n4["_packet_basis (src/llm_wiki_cli/services/context_packet.py)"]
    n5["capture_context_read (src/llm_wiki_cli/services/context_packet.py)"]
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
| `_fit_knowledge_packet_response` | call | [context_packet](../modules/context_packet.md) | 2 |
| `_guard_windows_inputs` | call | [context_packet](../modules/context_packet.md) | 2 |
| `_packet_basis` | call | [context_packet](../modules/context_packet.md) | 1 |
| `capture_context_read` | call | [context_packet](../modules/context_packet.md) | 4 |
