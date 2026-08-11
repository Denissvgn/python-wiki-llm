# ContextPacketUnavailableError

**Location:** `src/llm_wiki_cli/services/context_packet.py:256`
**Kind:** Class
**Bases:** `ContextPacketError`
**Module:** [context_packet](../modules/context_packet.md)

## Description

A required read-only packet capability is unavailable.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextPacketUnavailableError (src/llm_wiki_cli/services/context_packet.py)"]
    n1["ContextPacketError (src/llm_wiki_cli/services/context_packet.py)"]
    n2["_fit_knowledge_packet_response (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_packet_basis (src/llm_wiki_cli/services/context_packet.py)"]
    n4["capture_context_read (src/llm_wiki_cli/services/context_packet.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/context_packet.md"
    click n1 "../modules/context_packet.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_packet.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_packet](../modules/context_packet.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ContextPacketError` | [context_packet](../modules/context_packet.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `_fit_knowledge_packet_response` | call | [context_packet](../modules/context_packet.md) |
| `_fit_knowledge_packet_response` | call | [context_packet](../modules/context_packet.md) |
| `_packet_basis` | call | [context_packet](../modules/context_packet.md) |
| `capture_context_read` | call | [context_packet](../modules/context_packet.md) |
| `capture_context_read` | call | [context_packet](../modules/context_packet.md) |
| `capture_context_read` | call | [context_packet](../modules/context_packet.md) |
