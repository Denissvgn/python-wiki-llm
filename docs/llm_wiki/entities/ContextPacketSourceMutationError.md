# ContextPacketSourceMutationError

**Location:** `src/llm_wiki_cli/services/context_packet.py:244`
**Kind:** Class
**Bases:** `ContextPacketError`
**Module:** [context_packet](../modules/context_packet.md)

## Description

A captured source or wiki anchor changed before packet return.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(facet: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextPacketSourceMutationError (src/llm_wiki_cli/services/context_packet.py)"]
    n1["ContextPacketError (src/llm_wiki_cli/services/context_packet.py)"]
    n2["_assert_selection_unchanged (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_assert_source_inputs_unchanged (src/llm_wiki_cli/services/context_packet.py)"]
    n4["_assert_source_unchanged (src/llm_wiki_cli/services/context_packet.py)"]
    n5["_assert_wiki_unchanged (src/llm_wiki_cli/services/context_packet.py)"]
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
| `_assert_selection_unchanged` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_assert_source_inputs_unchanged` | call | [context_packet](../modules/context_packet.md) | 2 |
| `_assert_source_unchanged` | call | [context_packet](../modules/context_packet.md) | 2 |
| `_assert_wiki_unchanged` | call | [context_packet](../modules/context_packet.md) | 2 |
