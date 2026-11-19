# LintRequestError

**Location:** `src/llm_wiki_cli/services/lint_request.py:45`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [lint_request](../modules/lint_request.md)

## Description

The lint request names a path the workspace policy rejects.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["LintRequestError (src/llm_wiki_cli/services/lint_request.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/engine/__init__.py"]
    n4["execute_lint (src/llm_wiki_cli/services/lint_service.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/lint_request.md"
    click n2 "../modules/api.md"
    click n3 "../modules/engine___init__.md"
    click n4 "../modules/lint_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [lint_request](../modules/lint_request.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `execute_lint` | call | [lint_service](../modules/lint_service.md) | 1 |
