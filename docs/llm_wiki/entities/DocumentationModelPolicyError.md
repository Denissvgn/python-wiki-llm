# DocumentationModelPolicyError

**Location:** `src/llm_wiki_cli/services/documentation_model_policy.py:82`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [documentation_model_policy](../modules/documentation_model_policy.md)

## Description

Raised when model-routing configuration is unsafe or ambiguous.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationModelPolicyError (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["_normalise_modes (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n4["_object_sequence (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n5["_optional_text (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n6["_reject_sensitive_keys (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n7["_required_text (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n8["_resolve_override (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n9["_text_sequence (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n10["_validate_mode (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n11["_validate_object (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n12["_validate_provider_family (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n13["_validate_public_identifier (src/llm_wiki_cli/services/documentation_model_policy.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    n13 --> n0
    click n0 "../modules/documentation_model_policy.md"
    click n2 "../modules/api.md"
    click n3 "../modules/documentation_model_policy.md"
    click n4 "../modules/documentation_model_policy.md"
    click n5 "../modules/documentation_model_policy.md"
    click n6 "../modules/documentation_model_policy.md"
    click n7 "../modules/documentation_model_policy.md"
    click n8 "../modules/documentation_model_policy.md"
    click n9 "../modules/documentation_model_policy.md"
    click n10 "../modules/documentation_model_policy.md"
    click n11 "../modules/documentation_model_policy.md"
    click n12 "../modules/documentation_model_policy.md"
    click n13 "../modules/documentation_model_policy.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_model_policy](../modules/documentation_model_policy.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `_normalise_modes` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 2 |
| `_object_sequence` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 1 |
| `_optional_text` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 1 |
| `_reject_sensitive_keys` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 1 |
| `_required_text` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 1 |
| `_resolve_override` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 1 |
| `_text_sequence` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 1 |
| `_validate_mode` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 2 |
| `_validate_object` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 3 |
| `_validate_provider_family` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 2 |
| `_validate_public_identifier` | call | [documentation_model_policy](../modules/documentation_model_policy.md) | 5 |

> References: showing 12 of 25 logical references; 13 omitted by the 12-row generated summary limit.
