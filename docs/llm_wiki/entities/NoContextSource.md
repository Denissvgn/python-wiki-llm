# NoContextSource

**Location:** `src/llm_wiki_engine/pack_interfaces.py:339`
**Kind:** Class
**Bases:** —
**Module:** [pack_interfaces](../modules/pack_interfaces.md)

## Description

Relates no sources and shows nothing of them in budgeted context.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `related_sources` | `(inventory: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Iterable[str]]` | — | — |
| `entry` | `(data: Mapping[str, Any], detail: ContextDetail) -> Mapping[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["NoContextSource (src/llm_wiki_engine/pack_interfaces.py)"]
    n1["src/llm_wiki_cli/services/domain_pack.py"]
    n1 --> n0
    click n0 "../modules/pack_interfaces.md"
    click n1 "../modules/domain_pack.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [pack_interfaces](../modules/pack_interfaces.md) | 2 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `domain_pack` | import | [domain_pack](../modules/domain_pack.md) | — |
