# DocumentationModelRoute

**Location:** `src/llm_wiki_cli/services/documentation_model_policy.py:87`
**Kind:** Class
**Bases:** —
**Module:** [documentation_model_policy](../modules/documentation_model_policy.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One configured provider/model route.

``provider_id`` is a public configuration label such as ``anthropic-prod``
or ``local-ollama``.  It is not an endpoint and must not contain a key.
``model_id`` is provider configuration, not a protocol enum.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `route_id` | `str` | *required* | — |
| `provider_family` | `str` | *required* | — |
| `provider_id` | `str` | *required* | — |
| `model_id` | `str` | *required* | — |
| `tier` | `str` | *required* | — |
| `modes` | `tuple[str, ...]` | *required* | — |
| `aliases` | `tuple[str, ...]` | `()` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, Any]` | — | Return deterministic, credential-free route configuration. |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'DocumentationModelRoute'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationModelRoute (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1["src/llm_wiki_cli/api.py"]
    n2["_inline_override_id (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n3["_resolve_override (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n4["_selection (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n5["DocumentationModelRoute.from_dict (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n6["DocumentationModelRoutingPolicy.route_for_reference (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/documentation_model_policy.md"
    click n1 "../modules/api.md"
    click n2 "../modules/documentation_model_policy.md"
    click n3 "../modules/documentation_model_policy.md"
    click n4 "../modules/documentation_model_policy.md"
    click n5 "../modules/documentation_model_policy.md"
    click n6 "../modules/documentation_model_policy.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_model_policy](../modules/documentation_model_policy.md) | 3 | `aliases`, `model_id`, `modes`, `provider_family`, `provider_id`, `route_id`, `tier` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `_inline_override_id` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `_resolve_override` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 1 |
| `_resolve_override` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `_selection` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `DocumentationModelRoute.from_dict` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `DocumentationModelRoutingPolicy.route_for_reference` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
