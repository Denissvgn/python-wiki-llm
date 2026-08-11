# DocumentationModelOverride

**Location:** `src/llm_wiki_cli/services/documentation_model_policy.py:440`
**Kind:** Class
**Bases:** —
**Module:** [documentation_model_policy](../modules/documentation_model_policy.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Explicit user choice of a configured route or an inline public model id.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `route_id` | `str \| None` | `None` | — |
| `provider_family` | `str \| None` | `None` | — |
| `provider_id` | `str \| None` | `None` | — |
| `model_id` | `str \| None` | `None` | — |
| `tier` | `str \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'DocumentationModelOverride'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationModelOverride (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1["src/llm_wiki_cli/api.py"]
    n2["_resolve_override (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n3["DocumentationModelOverride.from_dict (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/documentation_model_policy.md"
    click n1 "../modules/api.md"
    click n2 "../modules/documentation_model_policy.md"
    click n3 "../modules/documentation_model_policy.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_model_policy](../modules/documentation_model_policy.md) | 3 | `model_id`, `provider_family`, `provider_id`, `route_id`, `tier` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `_resolve_override` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `DocumentationModelOverride.from_dict` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
