# ExtractionJobRequest

**Location:** `src/llm_wiki_cli/services/extraction_jobs.py:15`
**Kind:** Class
**Bases:** —
**Module:** [extraction_jobs](../modules/extraction_jobs.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

The user-facing extractor job request and its resolved worker limit.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `requested_jobs` | `RequestedJobs` | *required* | — |
| `resolved_jobs` | `int` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `parse` | `(value: object) -> 'ExtractionJobRequest'` | `@classmethod` | — |
| `resolved` | `(value: int) -> 'ExtractionJobRequest'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ExtractionJobRequest (src/llm_wiki_cli/services/extraction_jobs.py)"]
    n1["build_qualified_context (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n2["capture_context_read (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n3["reconcile_context_packet (src/llm_wiki_cli/services/context_packet_builder.py)"]
    n4["_build_context (src/llm_wiki_cli/services/context_service.py)"]
    n5["_build_context_impl (src/llm_wiki_cli/services/context_service.py)"]
    n6["get_inventory (src/llm_wiki_cli/services/context_service.py)"]
    n7["build_doctor_report (src/llm_wiki_cli/services/doctor_service.py)"]
    n8["src/llm_wiki_cli/services/documentation_native.py"]
    n9["extraction_job_request_for (src/llm_wiki_cli/services/extraction_jobs.py)"]
    n10["extraction_job_request_from_args (src/llm_wiki_cli/services/extraction_jobs.py)"]
    n11["ExtractionJobRequest.parse (src/llm_wiki_cli/services/extraction_jobs.py)"]
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
    click n1 "../modules/context_packet_builder.md"
    click n2 "../modules/context_packet_builder.md"
    click n3 "../modules/context_packet_builder.md"
    click n4 "../modules/context_service.md"
    click n5 "../modules/context_service.md"
    click n6 "../modules/context_service.md"
    click n7 "../modules/doctor_service.md"
    click n8 "../modules/documentation_native.md"
    click n9 "../modules/extraction_jobs.md"
    click n10 "../modules/extraction_jobs.md"
    click n11 "../modules/extraction_jobs.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [extraction_jobs](../modules/extraction_jobs.md) | 2 | `requested_jobs`, `resolved_jobs` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `build_qualified_context` | type_reference | [context_packet_builder](../modules/context_packet_builder.md) | — |
| `capture_context_read` | type_reference | [context_packet_builder](../modules/context_packet_builder.md) | — |
| `reconcile_context_packet` | type_reference | [context_packet_builder](../modules/context_packet_builder.md) | — |
| `_build_context` | type_reference | [context_service](../modules/context_service.md) | — |
| `_build_context_impl` | type_reference | [context_service](../modules/context_service.md) | — |
| `get_inventory` | type_reference | [context_service](../modules/context_service.md) | — |
| `build_doctor_report` | type_reference | [doctor_service](../modules/doctor_service.md) | — |
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) | — |
| `extraction_job_request_for` | call | [extraction_jobs](../modules/extraction_jobs.md) | 1 |
| `extraction_job_request_for` | type_reference | [extraction_jobs](../modules/extraction_jobs.md) | — |
| `extraction_job_request_from_args` | type_reference | [extraction_jobs](../modules/extraction_jobs.md) | — |
| `ExtractionJobRequest.parse` | call | [extraction_jobs](../modules/extraction_jobs.md) | 2 |

> References: showing 12 of 19 logical references; 7 omitted by the 12-row generated summary limit.
