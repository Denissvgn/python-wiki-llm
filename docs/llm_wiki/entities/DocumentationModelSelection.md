# DocumentationModelSelection

**Location:** `src/llm_wiki_cli/services/documentation_model_policy.py:548`
**Kind:** Class
**Bases:** —
**Module:** [documentation_model_policy](../modules/documentation_model_policy.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Credential-free model selection produced by a routing decision.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `mode` | `str` | *required* | — |
| `route_id` | `str` | *required* | — |
| `provider_family` | `str` | *required* | — |
| `provider_id` | `str` | *required* | — |
| `model_id` | `str` | *required* | — |
| `tier` | `str` | *required* | — |
| `basis` | `str` | *required* | — |
| `policy_hash` | `str` | *required* | — |
| `default_route_id` | `str` | *required* | — |
| `matched_rule_id` | `str \| None` | `None` | — |
| `signals` | `tuple[str, ...]` | `()` | — |
| `schema_version` | `str` | `DOCUMENTATION_MODEL_SELECTION_SCHEMA_VERSION` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, Any]` | — | Return fixed-field model metadata that cannot carry credentials. |
| `to_json` | `() -> str` | — | — |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'DocumentationModelSelection'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationModelSelection (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1["src/llm_wiki_cli/api.py"]
    n2["_selection (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n3["DocumentationModelSelection.from_dict (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n4["select_documentation_model (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n5["validate_documentation_model_selection (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/documentation_model_policy.md"
    click n1 "../modules/api.md"
    click n2 "../modules/documentation_model_policy.md"
    click n3 "../modules/documentation_model_policy.md"
    click n4 "../modules/documentation_model_policy.md"
    click n5 "../modules/documentation_model_policy.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_model_policy](../modules/documentation_model_policy.md) | 4 | `basis`, `default_route_id`, `matched_rule_id`, `mode`, `model_id`, `policy_hash`, `provider_family`, `provider_id`, `route_id`, `schema_version`, `signals`, `tier` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `_selection` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 1 |
| `_selection` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `DocumentationModelSelection.from_dict` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `select_documentation_model` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `validate_documentation_model_selection` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
