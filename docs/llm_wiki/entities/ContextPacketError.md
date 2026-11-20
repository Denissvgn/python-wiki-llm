# ContextPacketError

**Location:** `src/llm_wiki_engine/context_packet.py:171`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [context_packet](../modules/context_packet.md)

## Description

Base failure for context-packet construction and consumption.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextPacketError (src/llm_wiki_engine/context_packet.py)"]
    n1["ValueError"]
    n2["ContextPacketAuthorityError (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n3["ContextPacketSourceMutationError (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n4["ContextPacketUnavailableError (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n5["ContextPacketMalformedError (src/llm_wiki_engine/context_packet.py)"]
    n6["ContextPacketPathPolicyError (src/llm_wiki_engine/context_packet.py)"]
    n7["src/llm_wiki_cli/eval_lite/planner.py"]
    n8["src/llm_wiki_cli/services/context_packet_builder.py"]
    n9["src/llm_wiki_cli/services/context_service.py"]
    n10["src/llm_wiki_cli/services/mcp_server.py"]
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
    click n0 "../modules/context_packet.md"
    click n2 "../modules/context_packet_builder.md"
    click n3 "../modules/context_packet_builder.md"
    click n4 "../modules/context_packet_builder.md"
    click n5 "../modules/context_packet.md"
    click n6 "../modules/context_packet.md"
    click n7 "../modules/planner.md"
    click n8 "../modules/context_packet_builder.md"
    click n9 "../modules/context_service.md"
    click n10 "../modules/mcp_server.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_packet](../modules/context_packet.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |
| Subclass | `ContextPacketAuthorityError` | [context_packet_builder](../modules/context_packet_builder.md) |
| Subclass | `ContextPacketSourceMutationError` | [context_packet_builder](../modules/context_packet_builder.md) |
| Subclass | `ContextPacketUnavailableError` | [context_packet_builder](../modules/context_packet_builder.md) |
| Subclass | `ContextPacketMalformedError` | [context_packet](../modules/context_packet.md) |
| Subclass | `ContextPacketPathPolicyError` | [context_packet](../modules/context_packet.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `planner` | import | [planner](../modules/planner.md) | — |
| `context_packet_builder` | import | [context_packet_builder](../modules/context_packet_builder.md) | — |
| `context_service` | import | [context_service](../modules/context_service.md) | — |
| `mcp_server` | import | [mcp_server](../modules/mcp_server.md) | — |
