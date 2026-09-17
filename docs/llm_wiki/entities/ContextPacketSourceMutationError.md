# ContextPacketSourceMutationError

**Location:** `src/llm_wiki_cli/services/context_packet.py:241`
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
    n5["_assert_wiki_integrity (src/llm_wiki_cli/services/context_packet.py)"]
    n6["_assert_wiki_unchanged (src/llm_wiki_cli/services/context_packet.py)"]
    n7["wrapped (src/llm_wiki_cli/services/context_packet.py)"]
    n8["ContextSession.read (src/llm_wiki_cli/services/context_session.py)"]
    n9["_read_once (src/llm_wiki_cli/services/task_context.py)"]
    n10["build_scoped_task_read (src/llm_wiki_cli/services/task_context_v2.py)"]
    n11["ScopedTaskState.revalidate (src/llm_wiki_cli/services/task_context_v2.py)"]
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
    click n0 "../modules/context_packet.md"
    click n1 "../modules/context_packet.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_packet.md"
    click n6 "../modules/context_packet.md"
    click n7 "../modules/context_packet.md"
    click n8 "../modules/context_session.md"
    click n9 "../modules/task_context.md"
    click n10 "../modules/task_context_v2.md"
    click n11 "../modules/task_context_v2.md"
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
| `_assert_selection_unchanged` | call | [context_packet](../modules/context_packet.md) | 4 |
| `_assert_source_inputs_unchanged` | call | [context_packet](../modules/context_packet.md) | 2 |
| `_assert_source_unchanged` | call | [context_packet](../modules/context_packet.md) | 2 |
| `_assert_wiki_integrity` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_assert_wiki_unchanged` | call | [context_packet](../modules/context_packet.md) | 2 |
| `wrapped` | call | [context_packet](../modules/context_packet.md) | 1 |
| `ContextSession.read` | call | [context_session](../modules/context_session.md) | 1 |
| `_read_once` | call | [task_context](../modules/task_context.md) | 3 |
| `build_scoped_task_read` | call | [task_context_v2](../modules/task_context_v2.md) | 2 |
| `ScopedTaskState.revalidate` | call | [task_context_v2](../modules/task_context_v2.md) | 1 |
