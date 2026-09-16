# WorkflowRequestError

**Location:** `src/llm_wiki_cli/services/workflow_profile.py:28`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [workflow_profile](../modules/workflow_profile.md)

## Description

Identifies an invalid workflow contract field before workspace reads. Public adapters translate the error through their established invalid-request representation.

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
    n0["WorkflowRequestError (src/llm_wiki_cli/services/workflow_profile.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["_root_stamp (src/llm_wiki_cli/services/context_session.py)"]
    n4["apply_task_delta (src/llm_wiki_cli/services/context_session.py)"]
    n5["build_delta (src/llm_wiki_cli/services/context_session.py)"]
    n6["ContextSession.__init__ (src/llm_wiki_cli/services/context_session.py)"]
    n7["ContextSession._roots_current (src/llm_wiki_cli/services/context_session.py)"]
    n8["ContextSession.hint (src/llm_wiki_cli/services/context_session.py)"]
    n9["ContextSession.read (src/llm_wiki_cli/services/context_session.py)"]
    n10["_counter (src/llm_wiki_cli/services/task_context.py)"]
    n11["build_task_read (src/llm_wiki_cli/services/task_context.py)"]
    n12["plan_source_read (src/llm_wiki_cli/services/task_context.py)"]
    n13["validate_task_context (src/llm_wiki_cli/services/task_context.py)"]
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
    click n0 "../modules/workflow_profile.md"
    click n2 "../modules/api.md"
    click n3 "../modules/context_session.md"
    click n4 "../modules/context_session.md"
    click n5 "../modules/context_session.md"
    click n6 "../modules/context_session.md"
    click n7 "../modules/context_session.md"
    click n8 "../modules/context_session.md"
    click n9 "../modules/context_session.md"
    click n10 "../modules/task_context.md"
    click n11 "../modules/task_context.md"
    click n12 "../modules/task_context.md"
    click n13 "../modules/task_context.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [workflow_profile](../modules/workflow_profile.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `_root_stamp` | call | [context_session](../modules/context_session.md) | 2 |
| `apply_task_delta` | call | [context_session](../modules/context_session.md) | 4 |
| `build_delta` | call | [context_session](../modules/context_session.md) | 1 |
| `ContextSession.__init__` | call | [context_session](../modules/context_session.md) | 1 |
| `ContextSession._roots_current` | call | [context_session](../modules/context_session.md) | 2 |
| `ContextSession.hint` | call | [context_session](../modules/context_session.md) | 1 |
| `ContextSession.read` | call | [context_session](../modules/context_session.md) | 6 |
| `_counter` | call | [task_context](../modules/task_context.md) | 4 |
| `build_task_read` | call | [task_context](../modules/task_context.md) | 1 |
| `plan_source_read` | call | [task_context](../modules/task_context.md) | 2 |
| `validate_task_context` | call | [task_context](../modules/task_context.md) | 1 |

> References: showing 12 of 23 logical references; 11 omitted by the 12-row generated summary limit.
