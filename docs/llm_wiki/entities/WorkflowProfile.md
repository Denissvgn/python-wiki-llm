# WorkflowProfile

**Location:** `src/llm_wiki_cli/services/workflow_profile.py:116`
**Kind:** Class
**Bases:** —
**Module:** [workflow_profile](../modules/workflow_profile.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

An immutable canonical profile with detached settings and a content identity. Activation is explicit. Loading a profile does not change source, wiki, agent configuration, helper state or permissions.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `_bytes` | `bytes` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `()` | — | — |
| `profile_id` | `() -> str` | `@property` | — |
| `to_payload` | `() -> dict[str, Any]` | — | — |
| `settings` | `() -> dict[str, Any]` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WorkflowProfile (src/llm_wiki_cli/services/workflow_profile.py)"]
    n1["apply_task_delta (src/llm_wiki_cli/api.py)"]
    n2["build_compact_task_context (src/llm_wiki_cli/api.py)"]
    n3["build_task_context (src/llm_wiki_cli/api.py)"]
    n4["expand_compact_task_context (src/llm_wiki_cli/api.py)"]
    n5["load_workflow_profile (src/llm_wiki_cli/api.py)"]
    n6["open_context_session (src/llm_wiki_cli/api.py)"]
    n7["reconcile_task_context (src/llm_wiki_cli/api.py)"]
    n8["render_compact_task_context (src/llm_wiki_cli/api.py)"]
    n9["validate_compact_task_context (src/llm_wiki_cli/api.py)"]
    n10["validate_task_context (src/llm_wiki_cli/api.py)"]
    n11["McpWikiService.__init__ (src/llm_wiki_cli/services/mcp_server.py)"]
    n12["build_task_read (src/llm_wiki_cli/services/task_context.py)"]
    n1 --> n0
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
    click n0 "../modules/workflow_profile.md"
    click n1 "../modules/api.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/api.md"
    click n5 "../modules/api.md"
    click n6 "../modules/api.md"
    click n7 "../modules/api.md"
    click n8 "../modules/api.md"
    click n9 "../modules/api.md"
    click n10 "../modules/api.md"
    click n11 "../modules/mcp_server.md"
    click n12 "../modules/task_context.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [workflow_profile](../modules/workflow_profile.md) | 4 | `_bytes` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `apply_task_delta` | type_reference | [api](../modules/api.md) | — |
| `build_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `build_task_context` | type_reference | [api](../modules/api.md) | — |
| `expand_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `load_workflow_profile` | type_reference | [api](../modules/api.md) | — |
| `open_context_session` | type_reference | [api](../modules/api.md) | — |
| `reconcile_task_context` | type_reference | [api](../modules/api.md) | — |
| `render_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `validate_compact_task_context` | type_reference | [api](../modules/api.md) | — |
| `validate_task_context` | type_reference | [api](../modules/api.md) | — |
| `McpWikiService.__init__` | type_reference | [mcp_server](../modules/mcp_server.md) | — |
| `build_task_read` | type_reference | [task_context](../modules/task_context.md) | — |

> References: showing 12 of 16 logical references; 4 omitted by the 12-row generated summary limit.
