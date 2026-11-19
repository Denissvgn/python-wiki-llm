# ReferenceProvider

**Location:** `src/llm_wiki_cli/services/reference_providers.py:67`
**Kind:** Class
**Bases:** —
**Module:** [reference_providers](../modules/reference_providers.md)

## Description

The rules of one reference provider kind.

Subclasses set :attr:`kind`, choose :attr:`reads_file` and implement the
hooks. Hooks must be deterministic: publication evidence is rechecked by
running them again.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `kind` | `str` | `''` | — |
| `reads_file` | `bool` | `False` | — |
| `label` | `str` | `'reference'` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `normalize_selector` | `(dependency: Mapping[str, Any], field: str) -> dict[str, Any]` | — | The normalized form of ``dependency`` (which names the provider in ``reference``). |
| `capture` | `() -> Any` | — | The contract observed from the running installation (``reads_file`` false). |
| `parse` | `(raw: bytes) -> Any` | — | The contract read from the configured file (``reads_file`` true). |
| `validate_contract` | `(contract: Any) -> None` | — | Refuse a stored contract this provider could not have captured. |
| `select` | `(contract: Any, dependency: Mapping[str, Any]) -> str \| None` | — | A digest of the part of ``contract`` that ``dependency`` selects. |
| `identity` | `() -> Any` | — | A JSON-ready value that changes whenever this provider's results may change. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ReferenceProvider (src/llm_wiki_cli/services/reference_providers.py)"]
    n1["_CommandSelector (src/llm_wiki_cli/services/reference_providers.py)"]
    n2["BehaviorFactsProvider (src/llm_wiki_cli/services/reference_providers.py)"]
    n3["src/llm_wiki_cli/engine/__init__.py"]
    n4["DomainPack.with_reference_provider (src/llm_wiki_cli/services/domain_pack.py)"]
    n5["check_reference_providers (src/llm_wiki_cli/services/reference_providers.py)"]
    n6["current_reference_providers (src/llm_wiki_cli/services/reference_providers.py)"]
    n7["reference_provider (src/llm_wiki_cli/services/reference_providers.py)"]
    n8["reference_providers_identity (src/llm_wiki_cli/services/reference_providers.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/reference_providers.md"
    click n1 "../modules/reference_providers.md"
    click n2 "../modules/reference_providers.md"
    click n3 "../modules/engine___init__.md"
    click n4 "../modules/domain_pack.md"
    click n5 "../modules/reference_providers.md"
    click n6 "../modules/reference_providers.md"
    click n7 "../modules/reference_providers.md"
    click n8 "../modules/reference_providers.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [reference_providers](../modules/reference_providers.md) | 6 | `kind`, `label`, `reads_file` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Subclass | `_CommandSelector` | [reference_providers](../modules/reference_providers.md) |
| Subclass | `BehaviorFactsProvider` | [reference_providers](../modules/reference_providers.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `DomainPack.with_reference_provider` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
| `check_reference_providers` | type_reference | [reference_providers](../modules/reference_providers.md) | — |
| `current_reference_providers` | type_reference | [reference_providers](../modules/reference_providers.md) | — |
| `reference_provider` | type_reference | [reference_providers](../modules/reference_providers.md) | — |
| `reference_providers_identity` | type_reference | [reference_providers](../modules/reference_providers.md) | — |
