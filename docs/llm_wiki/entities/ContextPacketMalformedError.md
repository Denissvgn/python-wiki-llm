# ContextPacketMalformedError

**Location:** `src/llm_wiki_cli/services/context_packet.py:233`
**Kind:** Class
**Bases:** `ContextPacketError`
**Module:** [context_packet](../modules/context_packet.md)

## Description

The supplied bytes do not satisfy the canonical packet contract.

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
    n0["ContextPacketMalformedError (src/llm_wiki_cli/services/context_packet.py)"]
    n1["ContextPacketError (src/llm_wiki_cli/services/context_packet.py)"]
    n2["_coerce_packet_bytes (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_encode_packet_payload (src/llm_wiki_cli/services/context_packet.py)"]
    n4["_exact_fields (src/llm_wiki_cli/services/context_packet.py)"]
    n5["_explicit_response_source_priorities (src/llm_wiki_cli/services/context_packet.py)"]
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

| Reference | Kind | Source |
|---|---|---|
| `_coerce_packet_bytes` | call | [context_packet](../modules/context_packet.md) |
| `_coerce_packet_bytes` | call | [context_packet](../modules/context_packet.md) |
| `_coerce_packet_bytes` | call | [context_packet](../modules/context_packet.md) |
| `_coerce_packet_bytes` | call | [context_packet](../modules/context_packet.md) |
| `_encode_packet_payload` | call | [context_packet](../modules/context_packet.md) |
| `_exact_fields` | call | [context_packet](../modules/context_packet.md) |
| `_exact_fields` | call | [context_packet](../modules/context_packet.md) |
| `_explicit_response_source_priorities` | call | [context_packet](../modules/context_packet.md) |
| `_explicit_response_source_priorities` | call | [context_packet](../modules/context_packet.md) |
| `_explicit_response_source_priorities` | call | [context_packet](../modules/context_packet.md) |
| `_explicit_response_source_priorities` | call | [context_packet](../modules/context_packet.md) |
| `_explicit_response_source_priorities` | call | [context_packet](../modules/context_packet.md) |
