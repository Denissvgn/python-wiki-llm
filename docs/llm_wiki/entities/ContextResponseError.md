# ContextResponseError

**Location:** `src/llm_wiki_cli/services/context_response_format.py:41`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [context_response_format](../modules/context_response_format.md)

## Description

A context protocol response does not follow its format.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextResponseError (src/llm_wiki_cli/services/context_response_format.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/engine/__init__.py"]
    n3["_exact (src/llm_wiki_cli/services/context_response_format.py)"]
    n4["_object (src/llm_wiki_cli/services/context_response_format.py)"]
    n5["_request (src/llm_wiki_cli/services/context_response_format.py)"]
    n6["_text (src/llm_wiki_cli/services/context_response_format.py)"]
    n7["_validate (src/llm_wiki_cli/services/context_response_format.py)"]
    n8["_validate_error (src/llm_wiki_cli/services/context_response_format.py)"]
    n9["_validate_success (src/llm_wiki_cli/services/context_response_format.py)"]
    n10["validate_context_response (src/llm_wiki_cli/services/context_response_format.py)"]
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
    click n0 "../modules/context_response_format.md"
    click n2 "../modules/engine___init__.md"
    click n3 "../modules/context_response_format.md"
    click n4 "../modules/context_response_format.md"
    click n5 "../modules/context_response_format.md"
    click n6 "../modules/context_response_format.md"
    click n7 "../modules/context_response_format.md"
    click n8 "../modules/context_response_format.md"
    click n9 "../modules/context_response_format.md"
    click n10 "../modules/context_response_format.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_response_format](../modules/context_response_format.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `_exact` | call | [context_response_format](../modules/context_response_format.md) | 2 |
| `_object` | call | [context_response_format](../modules/context_response_format.md) | 1 |
| `_request` | call | [context_response_format](../modules/context_response_format.md) | 3 |
| `_text` | call | [context_response_format](../modules/context_response_format.md) | 1 |
| `_validate` | call | [context_response_format](../modules/context_response_format.md) | 2 |
| `_validate_error` | call | [context_response_format](../modules/context_response_format.md) | 4 |
| `_validate_success` | call | [context_response_format](../modules/context_response_format.md) | 10 |
| `validate_context_response` | call | [context_response_format](../modules/context_response_format.md) | 1 |
