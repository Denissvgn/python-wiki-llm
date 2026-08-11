# DocumentationModelRoutingRequest

**Location:** `src/llm_wiki_cli/services/documentation_model_policy.py:501`
**Kind:** Class
**Bases:** —
**Module:** [documentation_model_policy](../modules/documentation_model_policy.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One credential-free request to choose a wiki-update agent model.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `mode` | `str` | *required* | — |
| `signals` | `tuple[str, ...]` | `()` | — |
| `override` | `DocumentationModelOverride \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'DocumentationModelRoutingRequest'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationModelRoutingRequest (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1["src/llm_wiki_cli/api.py"]
    n2["_selection (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n3["DocumentationModelRoutingRequest.from_dict (src/llm_wiki_cli/services/documentation_model_policy.py)"]
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
| [documentation_model_policy](../modules/documentation_model_policy.md) | 3 | `mode`, `override`, `signals` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `_selection` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `DocumentationModelRoutingRequest.from_dict` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `select_documentation_model` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
| `validate_documentation_model_selection` | type_reference | [documentation_model_policy](../modules/documentation_model_policy.md) | — |
