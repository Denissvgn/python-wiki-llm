# ReferenceSelectorError

**Location:** `src/llm_wiki_cli/services/reference_providers.py:40`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [reference_providers](../modules/reference_providers.md)

## Description

A topic dependency selects a reference in a way its provider refuses.

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
    n0["ReferenceSelectorError (src/llm_wiki_cli/services/reference_providers.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/publication_config.py"]
    n3["_CommandSelector.normalize_selector (src/llm_wiki_cli/services/reference_providers.py)"]
    n4["_selector_fields (src/llm_wiki_cli/services/reference_providers.py)"]
    n5["BehaviorFactsProvider.normalize_selector (src/llm_wiki_cli/services/reference_providers.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/reference_providers.md"
    click n2 "../modules/publication_config.md"
    click n3 "../modules/reference_providers.md"
    click n4 "../modules/reference_providers.md"
    click n5 "../modules/reference_providers.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [reference_providers](../modules/reference_providers.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `publication_config` | import | [publication_config](../modules/publication_config.md) | — |
| `_CommandSelector.normalize_selector` | call | [reference_providers](../modules/reference_providers.md) | 3 |
| `_selector_fields` | call | [reference_providers](../modules/reference_providers.md) | 2 |
| `BehaviorFactsProvider.normalize_selector` | call | [reference_providers](../modules/reference_providers.md) | 1 |
