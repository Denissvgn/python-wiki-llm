# ProducerComponent

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:302`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_model](../modules/knowledge_model.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `ProducerComponent` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `component_id` | `str` | *required* | — |
| `version` | `str` | *required* | — |
| `configuration_hash` | `Optional[str]` | `None` | — |
| `limitations` | `tuple[str, ...]` | `()` | — |
| `extensions` | `Extensions` | `field(default_factory=dict)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProducerComponent (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["src/llm_wiki_cli/services/health_contract.py"]
    n2["_component (src/llm_wiki_cli/services/health_details.py)"]
    n3["_build_component (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n4["build_producer_record (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n5["plugin_producer_inputs (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n6["_component_basis_payload (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n7["_component_change_reason (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n8["_components_by_id (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n9["_configuration_marked_unknown (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n10["_configuration_unknown (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n11["_version_unknown (src/llm_wiki_cli/services/knowledge_freshness.py)"]
    n1 --> n0
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
    click n0 "../modules/knowledge_model.md"
    click n1 "../modules/health_contract.md"
    click n2 "../modules/health_details.md"
    click n3 "../modules/knowledge_envelope.md"
    click n4 "../modules/knowledge_envelope.md"
    click n5 "../modules/knowledge_envelope.md"
    click n6 "../modules/knowledge_freshness.md"
    click n7 "../modules/knowledge_freshness.md"
    click n8 "../modules/knowledge_freshness.md"
    click n9 "../modules/knowledge_freshness.md"
    click n10 "../modules/knowledge_freshness.md"
    click n11 "../modules/knowledge_freshness.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `component_id`, `configuration_hash`, `extensions`, `limitations`, `version` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `health_contract` | import | [health_contract](../modules/health_contract.md) | — |
| `_component` | type_reference | [health_details](../modules/health_details.md) | — |
| `_build_component` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 1 |
| `_build_component` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `build_producer_record` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `plugin_producer_inputs` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) | — |
| `_component_basis_payload` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_component_change_reason` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_components_by_id` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_configuration_marked_unknown` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_configuration_unknown` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |
| `_version_unknown` | type_reference | [knowledge_freshness](../modules/knowledge_freshness.md) | — |

> References: showing 12 of 19 logical references; 7 omitted by the 12-row generated summary limit.
