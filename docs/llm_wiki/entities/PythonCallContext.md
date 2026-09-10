# PythonCallContext

**Location:** `src/llm_wiki_cli/services/python_calls.py:14`
**Kind:** Class
**Bases:** —
**Module:** [python_calls](../modules/python_calls.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `PythonCallContext` in `src/llm_wiki_cli/services/python_calls.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `callable` | `dict` | *required* | — |
| `call_index` | `int` | *required* | — |
| `resolver` | `ModulePathResolver` | *required* | — |
| `class_name` | `str \| None` | `None` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PythonCallContext (src/llm_wiki_cli/services/python_calls.py)"]
    n1["_call_observations_for_file (src/llm_wiki_cli/services/extraction_service.py)"]
    n2["_edges_for_file (src/llm_wiki_cli/services/extraction_service.py)"]
    n3["_resolve_call (src/llm_wiki_cli/services/extraction_service.py)"]
    n4["_resolve_call_observation (src/llm_wiki_cli/services/extraction_service.py)"]
    n5["_workflow_call_chain (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["resolve_python_call (src/llm_wiki_cli/services/python_calls.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/python_calls.md"
    click n1 "../modules/extraction_service.md"
    click n2 "../modules/extraction_service.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extraction_service.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/python_calls.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [python_calls](../modules/python_calls.md) | 0 | `call_index`, `callable`, `class_name`, `resolver` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_call_observations_for_file` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `_edges_for_file` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `_resolve_call` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_resolve_call_observation` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_workflow_call_chain` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `resolve_python_call` | type_reference | [python_calls](../modules/python_calls.md) | — |
