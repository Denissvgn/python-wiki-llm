# FlowAnalysisContext

**Location:** `src/llm_wiki_cli/services/entrypoints.py:1201`
**Kind:** Class
**Bases:** —
**Module:** [entrypoints](../modules/entrypoints.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Read-only adjacency indexes for flows over one caller-owned edge list.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `adjacency` | `Mapping[tuple, tuple[dict, ...]]` | *required* | — |

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["FlowAnalysisContext (src/llm_wiki_cli/services/entrypoints.py)"]
    n1["build_flow (src/llm_wiki_cli/services/entrypoints.py)"]
    n2["build_flow_context (src/llm_wiki_cli/services/entrypoints.py)"]
    n3["build_flow_detailed (src/llm_wiki_cli/services/entrypoints.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/entrypoints.md"
    click n1 "../modules/entrypoints.md"
    click n2 "../modules/entrypoints.md"
    click n3 "../modules/entrypoints.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [entrypoints](../modules/entrypoints.md) | 0 | `adjacency` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_flow` | type_reference | [entrypoints](../modules/entrypoints.md) | — |
| `build_flow_context` | call | [entrypoints](../modules/entrypoints.md) | 1 |
| `build_flow_context` | type_reference | [entrypoints](../modules/entrypoints.md) | — |
| `build_flow_detailed` | type_reference | [entrypoints](../modules/entrypoints.md) | — |
