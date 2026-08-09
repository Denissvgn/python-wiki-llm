# ProducerComponentInput

**Location:** `src/llm_wiki_cli/services/knowledge_envelope.py:215`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_envelope](../modules/knowledge_envelope.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Safe, already selected producer metadata.

``configuration`` must be an application-owned allowlist of effective,
non-secret, behavior-affecting values.  ``None`` explicitly means that the
complete safe configuration basis was unavailable.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `component_id` | `str` | *required* | — |
| `version` | `str \| None` | *required* | — |
| `configuration` | `Mapping[str, Any] \| None` | `None` | — |
| `limitations` | `tuple[str, ...]` | `()` | — |
| `extensions` | `Mapping[str, Any]` | `field(default_factory=dict)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ProducerComponentInput (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n1["_build_component (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n2["build_producer_record (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n3["plugin_producer_inputs (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n4["src/llm_wiki_cli/services/knowledge_generation.py"]
    n5["_infrastructure_extractor_component (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n6["_producer_evidence (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n7["build_runtime_knowledge_plan (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n8["build_runtime_live_evaluation (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/knowledge_envelope.md"
    click n1 "../modules/knowledge_envelope.md"
    click n2 "../modules/knowledge_envelope.md"
    click n3 "../modules/knowledge_envelope.md"
    click n4 "../modules/knowledge_generation.md"
    click n5 "../modules/knowledge_orchestration.md"
    click n6 "../modules/knowledge_orchestration.md"
    click n7 "../modules/knowledge_orchestration.md"
    click n8 "../modules/knowledge_orchestration.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_envelope](../modules/knowledge_envelope.md) | 0 | `component_id`, `configuration`, `extensions`, `limitations`, `version` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_build_component` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `build_producer_record` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `plugin_producer_inputs` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `plugin_producer_inputs` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) |
| `_infrastructure_extractor_component` | call | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| `_infrastructure_extractor_component` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| `_producer_evidence` | call | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| `_producer_evidence` | call | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| `_producer_evidence` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| `build_runtime_knowledge_plan` | call | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| `build_runtime_live_evaluation` | call | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
