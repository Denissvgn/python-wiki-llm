# ContextSource

**Location:** `src/llm_wiki_cli/services/domain_pack.py:258`
**Kind:** Class
**Bases:** `Protocol`
**Module:** [domain_pack](../modules/domain_pack.md)

**Decorators:** `@runtime_checkable`

## Description

How sources relate and appear in budgeted context.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `related_sources` | `(inventory: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Iterable[str]]` | — | Return ``{source path: related source paths}``. |
| `entry` | `(data: Mapping[str, Any], detail: ContextDetail) -> Mapping[str, Any]` | — | Return the context entry of one source at ``detail``. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextSource (src/llm_wiki_cli/services/domain_pack.py)"]
    n1["Protocol"]
    n2["src/llm_wiki_cli/engine/__init__.py"]
    n3["DomainPack.with_context_source (src/llm_wiki_cli/services/domain_pack.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    click n0 "../modules/domain_pack.md"
    click n2 "../modules/engine___init__.md"
    click n3 "../modules/domain_pack.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [domain_pack](../modules/domain_pack.md) | 2 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Protocol` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `DomainPack.with_context_source` | type_reference | [domain_pack](../modules/domain_pack.md) | — |
