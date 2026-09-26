# health_details Module

**Path:** `src/llm_wiki_cli/services/health_details.py`

## Description

Capture detailed health once from an operation's already evaluated inputs.

This module performs no I/O or source extraction. Serialized capture prevents
later changes to a caller's view, source files or installed version from
rewriting the evidence subsequently rendered by doctor or CI.

## Imports

| Source | Symbols |
|--------|---------|
| `.contracts` | `HEALTH_DETAILS_SCHEMA_VERSION` |
| `.health_contract` | `COMPARABLE_STATES`, `EXAMPLE_LIMIT`, `FRESHNESS_STATES`, `HealthDetailsError` |
| `.knowledge_artifacts` | `require_validated_artifacts` |
| `.knowledge_consumption` | `KnowledgeReadView` |
| `.knowledge_envelope` | `hash_source_snapshot` |
| `.knowledge_evidence` | `canonical_json_text`, `hash_json` |
| `.knowledge_freshness` | `structural_freshness_modeled` |
| `.knowledge_model` | `ProducerComponent`, `ProducerRecord` |
| `.source_snapshot` | `SourceSnapshot` |
| `__future__` | `annotations` |
| `bisect` | `insort` |
| `collections` | `Counter` |
| `dataclasses` | `dataclass` |
| `json` | `json` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/contracts.py"]
    n1["src/llm_wiki_cli/services/doctor_service.py"]
    n2["src/llm_wiki_cli/services/health_contract.py"]
    n3["src/llm_wiki_cli/services/health_details.py"]
    n4["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n5["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n6["src/llm_wiki_cli/services/knowledge_envelope.py"]
    n7["src/llm_wiki_cli/services/knowledge_evidence.py"]
    n8["src/llm_wiki_cli/services/knowledge_freshness.py"]
    n9["src/llm_wiki_cli/services/knowledge_model.py"]
    n10["src/llm_wiki_cli/services/lint_service.py"]
    n11["src/llm_wiki_cli/services/source_snapshot.py"]
    n1 --> n0
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n9
    n1 --> n10
    n2 --> n0
    n2 --> n8
    n2 --> n9
    n3 --> n0
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n3 --> n9
    n3 --> n11
    n4 --> n0
    n4 --> n6
    n4 --> n7
    n4 --> n9
    n5 --> n4
    n5 --> n8
    n5 --> n9
    n6 --> n0
    n6 --> n7
    n6 --> n9
    n8 --> n0
    n8 --> n4
    n8 --> n7
    n8 --> n9
    n9 --> n0
    n9 --> n7
    n10 --> n3
    n10 --> n4
    n10 --> n5
    n10 --> n9
    n10 --> n11
    n11 --> n6
    click n0 "../modules/services_contracts.md"
    click n1 "../modules/doctor_service.md"
    click n2 "../modules/health_contract.md"
    click n3 "../modules/health_details.md"
    click n4 "../modules/knowledge_artifacts.md"
    click n5 "../modules/knowledge_consumption.md"
    click n6 "../modules/knowledge_envelope.md"
    click n7 "../modules/knowledge_evidence.md"
    click n8 "../modules/knowledge_freshness.md"
    click n9 "../modules/knowledge_model.md"
    click n10 "../modules/lint_service.md"
    click n11 "../modules/source_snapshot.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [doctor_service](../modules/doctor_service.md) |
| Inbound | [lint_service](../modules/lint_service.md) |
| Outbound | [services_contracts](../modules/services_contracts.md) |
| Outbound | [health_contract](../modules/health_contract.md) |
| Outbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Outbound | [knowledge_consumption](../modules/knowledge_consumption.md) |
| Outbound | [knowledge_envelope](../modules/knowledge_envelope.md) |
| Outbound | [knowledge_evidence](../modules/knowledge_evidence.md) |
| Outbound | [knowledge_freshness](../modules/knowledge_freshness.md) |
| Outbound | [knowledge_model](../modules/knowledge_model.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [CapturedHealthDetails](../entities/CapturedHealthDetails.md) | 33 | — | An immutable capture with independently owned output dictionaries. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_component` | `(component: ProducerComponent) -> dict[str, Any]` | — | — |
| `_producer` | `(producer: ProducerRecord, schema: str, options_hash: str) -> dict[str, Any]` | — | — |
| `capture_health_details` | `(view: KnowledgeReadView \| None, *, wiki_dir: str, src_dir: str, source_snapshot: SourceSnapshot \| None = None, evaluation_failed: bool = False) -> CapturedHealthDetails` | — | Capture inventory, exact comparison basis and bounded primary examples. |
