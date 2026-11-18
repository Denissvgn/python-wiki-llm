# InventoryResult

**Location:** `src/llm_wiki_cli/services/extraction_service.py:188`
**Kind:** Class
**Bases:** —
**Module:** [extraction_service](../modules/extraction_service.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Complete extraction outcome shared by generation, context, review, and
validation callers. Alongside merged inventory it carries per-extractor
statuses, the effective job plan, cache statistics, plugin producer metadata,
the exact source snapshot, and optional observation maps. The `failed`
property gives callers a single fail-closed check across extractor statuses.

The `failed` property covers extractor statuses. A successful diagnostic helper batch may still report file-scoped syntax/read failures, so consumers making source or member-retirement decisions inspect the exact path outcome and its parsed record. Batch failure, unavailable coverage and omitted outcomes remain separate from valid empty records.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `inventory` | `dict` | *required* | — |
| `statuses` | `dict[str, ExtractorStatus]` | *required* | — |
| `cache_stats` | `InventoryCacheStats \| None` | `None` | — |
| `extraction_job_plan` | `ExtractionJobPlan` | `field(default_factory=ExtractionJobPlan)` | — |
| `extractor_registry` | `dict[str, str]` | `field(default_factory=dict)` | — |
| `plugin_components` | `tuple[dict, ...]` | `()` | — |
| `producer_plugin_components` | `tuple[dict, ...]` | `()` | — |
| `plugin_lock_path` | `str \| None` | `None` | — |
| `plugin_lock_hash` | `str \| None` | `None` | — |
| `source_snapshot` | `SourceSnapshot \| None` | `None` | — |
| `analysis_components` | `dict \| None` | `field(default=None, repr=False, compare=False)` | — |
| `data_effect_observations` | `dict \| None` | `field(default=None, repr=False, compare=False)` | — |
| `import_observations` | `dict \| None` | `field(default=None, repr=False, compare=False)` | — |
| `implementation_observations` | `dict \| None` | `field(default=None, repr=False, compare=False)` | — |
| `path_outcomes` | `dict` | `field(default_factory=dict)` | — |
| `extraction_cache_hashes` | `dict[str, str]` | `field(default_factory=dict, repr=False, compare=False)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `analysis_input_status` | `()` | `@property` | — |
| `job_plan` | `() -> ExtractionJobPlan` | `@property` | — |
| `failed` | `() -> list[ExtractorStatus]` | `@property` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["InventoryResult (src/llm_wiki_cli/services/extraction_service.py)"]
    n1["_finalize_bootstrap (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n2["_finalize_bootstrap_artifacts (src/llm_wiki_cli/services/bootstrap_runtime.py)"]
    n3["src/llm_wiki_cli/services/context_packet_builder.py"]
    n4["_build_context_knowledge_view (src/llm_wiki_cli/services/context_service.py)"]
    n5["_build_protocol_enrichment (src/llm_wiki_cli/services/context_service.py)"]
    n6["_capture_protocol_enrichment_session (src/llm_wiki_cli/services/context_service.py)"]
    n7["get_inventory (src/llm_wiki_cli/services/context_service.py)"]
    n8["_build_inventory_result (src/llm_wiki_cli/services/extraction_service.py)"]
    n9["_completed_inventory_result (src/llm_wiki_cli/services/extraction_service.py)"]
    n10["_extractor_failure_message (src/llm_wiki_cli/services/extraction_service.py)"]
    n11["ensure_complete_inventory (src/llm_wiki_cli/services/extraction_service.py)"]
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
    click n0 "../modules/extraction_service.md"
    click n1 "../modules/bootstrap_runtime.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/context_packet_builder.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/context_service.md"
    click n6 "../modules/context_service.md"
    click n7 "../modules/context_service.md"
    click n8 "../modules/extraction_service.md"
    click n9 "../modules/extraction_service.md"
    click n10 "../modules/extraction_service.md"
    click n11 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extraction_service](../modules/extraction_service.md) | 3 | `analysis_components`, `cache_stats`, `data_effect_observations`, `extraction_cache_hashes`, `extraction_job_plan`, `extractor_registry`, `implementation_observations`, `import_observations`, `inventory`, `path_outcomes`, `plugin_components`, `plugin_lock_hash` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_finalize_bootstrap` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `_finalize_bootstrap_artifacts` | type_reference | [bootstrap_runtime](../modules/bootstrap_runtime.md) | — |
| `context_packet_builder` | import | [context_packet_builder](../modules/context_packet_builder.md) | — |
| `_build_context_knowledge_view` | type_reference | [context_service](../modules/context_service.md) | — |
| `_build_protocol_enrichment` | type_reference | [context_service](../modules/context_service.md) | — |
| `_capture_protocol_enrichment_session` | type_reference | [context_service](../modules/context_service.md) | — |
| `get_inventory` | type_reference | [context_service](../modules/context_service.md) | — |
| `_build_inventory_result` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_completed_inventory_result` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `_completed_inventory_result` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_extractor_failure_message` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `ensure_complete_inventory` | type_reference | [extraction_service](../modules/extraction_service.md) | — |

> References: showing 12 of 25 logical references; 13 omitted by the 12-row generated summary limit.
