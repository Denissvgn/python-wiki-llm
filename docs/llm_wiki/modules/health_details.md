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
| `.` | `analysis_compatibility` |
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
    n0["src"]
    n1["src/llm_wiki_cli/services/health_details.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/health_details.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (2) |
| Outbound | `src` (10) |

> All 12 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [CapturedHealthDetails](../entities/CapturedHealthDetails.md) | 34 | — | An immutable capture with independently owned output dictionaries. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_component` | `(component: ProducerComponent) -> dict[str, Any]` | — | — |
| `_producer` | `(producer: ProducerRecord, schema: str, options_hash: str) -> dict[str, Any]` | — | — |
| `capture_health_details` | `(view: KnowledgeReadView \| None, *, wiki_dir: str, src_dir: str, source_snapshot: SourceSnapshot \| None = None, evaluation_failed: bool = False) -> CapturedHealthDetails` | — | Capture inventory, exact comparison basis and bounded primary examples. |
