# DocumentationModelRoutingPolicy

**Location:** `src/llm_wiki_cli/services/documentation_model_policy.py:253`
**Kind:** Class
**Bases:** —
**Module:** [documentation_model_policy](../modules/documentation_model_policy.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Complete low-cost-first routing configuration for wiki updates.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `routes` | `tuple[DocumentationModelRoute, ...]` | *required* | — |
| `mode_defaults` | `Mapping[str, str]` | *required* | — |
| `escalation_rules` | `tuple[DocumentationModelEscalationRule, ...]` | `()` | — |
| `schema_version` | `str` | `DOCUMENTATION_MODEL_ROUTING_SCHEMA_VERSION` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `policy_hash` | `() -> str` | `@property` | Return the stable hash used to audit a selection. |
| `route_for_reference` | `(reference: str) -> DocumentationModelRoute` | — | Resolve a route id or configured alias without provider assumptions. |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `to_json` | `() -> str` | — | Return canonical JSON suitable for hashing and checked-in policy files. |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'DocumentationModelRoutingPolicy'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationModelRoutingPolicy (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1["src/llm_wiki_cli/api.py"]
    n2["_resolve_override (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n3["_selection (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n4["DocumentationModelRoutingPolicy.from_dict (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n5["select_documentation_model (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n6["validate_documentation_model_selection (src/llm_wiki_cli/services/documentation_model_policy.py)"]
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
| [documentation_model_policy](../modules/documentation_model_policy.md) | 6 | `escalation_rules`, `mode_defaults`, `routes`, `schema_version` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `_resolve_override` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `_selection` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `DocumentationModelRoutingPolicy.from_dict` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `select_documentation_model` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `validate_documentation_model_selection` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
