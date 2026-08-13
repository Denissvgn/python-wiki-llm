# ExtractionJobPlan

**Location:** `src/llm_wiki_cli/services/extraction_jobs.py:52`
**Kind:** Class
**Bases:** —
**Module:** [extraction_jobs](../modules/extraction_jobs.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A deterministic description of the extraction work about to run.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `requested_jobs` | `RequestedJobs` | `1` | — |
| `resolved_jobs` | `int` | `1` | — |
| `eligible_parallel_plans` | `int` | `0` | — |
| `effective_workers` | `int` | `0` | — |
| `parallel_plan_ids` | `tuple[str, ...]` | `()` | — |
| `sequential_plan_ids` | `tuple[str, ...]` | `()` | — |
| `cache_elided_plan_ids` | `tuple[str, ...]` | `()` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `to_dict` | `() -> dict[str, object]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ExtractionJobPlan (src/llm_wiki_cli/services/extraction_jobs.py)"]
    n1["src/llm_wiki_cli/commands/sync_cmd.py"]
    n2["build_qualified_context (src/llm_wiki_cli/services/context_packet.py)"]
    n3["capture_context_read (src/llm_wiki_cli/services/context_packet.py)"]
    n4["reconcile_context_packet (src/llm_wiki_cli/services/context_packet.py)"]
    n5["_build_context (src/llm_wiki_cli/services/context_service.py)"]
    n6["_build_context_impl (src/llm_wiki_cli/services/context_service.py)"]
    n7["get_inventory (src/llm_wiki_cli/services/context_service.py)"]
    n8["format_extraction_job_plan (src/llm_wiki_cli/services/extraction_jobs.py)"]
    n9["print_extraction_job_plan (src/llm_wiki_cli/services/extraction_jobs.py)"]
    n10["_build_extraction_job_plan (src/llm_wiki_cli/services/extraction_service.py)"]
    n11["_completed_inventory_result (src/llm_wiki_cli/services/extraction_service.py)"]
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
    click n0 "../modules/extraction_jobs.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_service.md"
    click n6 "../modules/context_service.md"
    click n7 "../modules/context_service.md"
    click n8 "../modules/extraction_jobs.md"
    click n9 "../modules/extraction_jobs.md"
    click n10 "../modules/extraction_service.md"
    click n11 "../modules/extraction_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extraction_jobs](../modules/extraction_jobs.md) | 1 | `cache_elided_plan_ids`, `effective_workers`, `eligible_parallel_plans`, `parallel_plan_ids`, `requested_jobs`, `resolved_jobs`, `sequential_plan_ids` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `sync_cmd` | import | [sync_cmd](../modules/sync_cmd.md) | — |
| `build_qualified_context` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `capture_context_read` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `reconcile_context_packet` | type_reference | [context_packet](../modules/context_packet.md) | — |
| `_build_context` | type_reference | [context_service](../modules/context_service.md) | — |
| `_build_context_impl` | type_reference | [context_service](../modules/context_service.md) | — |
| `get_inventory` | type_reference | [context_service](../modules/context_service.md) | — |
| `format_extraction_job_plan` | type_reference | [extraction_jobs](../modules/extraction_jobs.md) | — |
| `print_extraction_job_plan` | type_reference | [extraction_jobs](../modules/extraction_jobs.md) | — |
| `_build_extraction_job_plan` | call | [extraction_service](../modules/extraction_service.md) | 1 |
| `_build_extraction_job_plan` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_completed_inventory_result` | type_reference | [extraction_service](../modules/extraction_service.md) | — |

> References: showing 12 of 16 logical references; 4 omitted by the 12-row generated summary limit.
