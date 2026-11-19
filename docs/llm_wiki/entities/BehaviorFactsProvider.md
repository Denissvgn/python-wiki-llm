# BehaviorFactsProvider

**Location:** `src/llm_wiki_cli/services/reference_providers.py:175`
**Kind:** Class
**Bases:** `ReferenceProvider`
**Module:** [reference_providers](../modules/reference_providers.md)

## Description

The installed behavior facts; dependencies may select one fact group.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `normalize_selector` | `(dependency: Mapping[str, Any], field: str) -> dict[str, Any]` | — | — |
| `capture` | `() -> Any` | — | — |
| `validate_contract` | `(contract: Any) -> None` | — | — |
| `select` | `(contract: Any, dependency: Mapping[str, Any]) -> str \| None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["BehaviorFactsProvider (src/llm_wiki_cli/services/reference_providers.py)"]
    n1["ReferenceProvider (src/llm_wiki_cli/services/reference_providers.py)"]
    n2["src/llm_wiki_cli/engine/__init__.py"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/reference_providers.md"
    click n1 "../modules/reference_providers.md"
    click n2 "../modules/engine___init__.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [reference_providers](../modules/reference_providers.md) | 4 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ReferenceProvider` | [reference_providers](../modules/reference_providers.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
