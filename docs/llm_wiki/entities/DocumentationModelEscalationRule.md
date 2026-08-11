# DocumentationModelEscalationRule

**Location:** `src/llm_wiki_cli/services/documentation_model_policy.py:161`
**Kind:** Class
**Bases:** —
**Module:** [documentation_model_policy](../modules/documentation_model_policy.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Configured signal-to-route promotion owned by the host supervisor.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `rule_id` | `str` | *required* | — |
| `signals` | `tuple[str, ...]` | *required* | — |
| `target_route_id` | `str` | *required* | — |
| `modes` | `tuple[str, ...]` | *required* | — |
| `from_tiers` | `tuple[str, ...]` | `('low-cost', 'balanced')` | — |
| `priority` | `int` | `100` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'DocumentationModelEscalationRule'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationModelEscalationRule (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1["src/llm_wiki_cli/api.py"]
    n2["DocumentationModelEscalationRule.from_dict (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1 --> n0
    n2 --> n0
    click n0 "../modules/documentation_model_policy.md"
    click n1 "../modules/api.md"
    click n2 "../modules/documentation_model_policy.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_model_policy](../modules/documentation_model_policy.md) | 3 | `from_tiers`, `modes`, `priority`, `rule_id`, `signals`, `target_route_id` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `DocumentationModelEscalationRule.from_dict` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
