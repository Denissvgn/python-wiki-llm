# extraction_jobs Module

**Path:** `src/llm_wiki_cli/services/extraction_jobs.py`

## Description

_Auto-generated from `src/llm_wiki_cli/services/extraction_jobs.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `argparse` | `argparse` |
| `dataclasses` | `dataclass` |
| `os` | `os` |
| `sys` | `sys` |
| `typing` | `Literal`, `TextIO` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/ci_check_cmd.py"]
    n2["src/llm_wiki_cli/commands/doctor_cmd.py"]
    n3["src/llm_wiki_cli/commands/sync_cmd.py"]
    n4["src/llm_wiki_cli/services/context_packet.py"]
    n5["src/llm_wiki_cli/services/context_service.py"]
    n6["src/llm_wiki_cli/services/doctor_service.py"]
    n7["src/llm_wiki_cli/services/documentation_native.py"]
    n8["src/llm_wiki_cli/services/extraction_jobs.py"]
    n9["src/llm_wiki_cli/services/extraction_service.py"]
    n10["src/llm_wiki_cli/services/lint_service.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n5
    n0 --> n8
    n0 --> n9
    n0 --> n10
    n1 --> n8
    n1 --> n10
    n2 --> n6
    n2 --> n8
    n3 --> n8
    n3 --> n9
    n4 --> n5
    n4 --> n8
    n4 --> n9
    n5 --> n4
    n5 --> n8
    n5 --> n9
    n6 --> n8
    n6 --> n10
    n7 --> n5
    n7 --> n8
    n7 --> n9
    n9 --> n8
    n10 --> n8
    n10 --> n9
    click n0 "../modules/cli.md"
    click n1 "../modules/ci_check_cmd.md"
    click n2 "../modules/doctor_cmd.md"
    click n3 "../modules/sync_cmd.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_service.md"
    click n6 "../modules/doctor_service.md"
    click n7 "../modules/documentation_native.md"
    click n8 "../modules/extraction_jobs.md"
    click n9 "../modules/extraction_service.md"
    click n10 "../modules/lint_service.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Inbound | [ci_check_cmd](../modules/ci_check_cmd.md) |
| Inbound | [doctor_cmd](../modules/doctor_cmd.md) |
| Inbound | [sync_cmd](../modules/sync_cmd.md) |
| Inbound | [context_packet](../modules/context_packet.md) |
| Inbound | [context_service](../modules/context_service.md) |
| Inbound | [doctor_service](../modules/doctor_service.md) |
| Inbound | [documentation_native](../modules/documentation_native.md) |
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [lint_service](../modules/lint_service.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [ExtractionJobRequest](../entities/ExtractionJobRequest.md) | 14 | — | The user-facing extractor job request and its resolved worker limit. |
| [ExtractionJobsAction](../entities/ExtractionJobsAction.md) | 39 | `argparse.Action` | Resolve ``--jobs`` while preserving whether automatic sizing was requested. |
| [ExtractionJobPlan](../entities/ExtractionJobPlan.md) | 52 | — | A deterministic description of the extraction work about to run. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `extraction_job_request_from_args` | `(args) -> ExtractionJobRequest` | — | Build a request from an argparse-compatible namespace. |
| `format_extraction_job_plan` | `(plan: ExtractionJobPlan) -> str` | — | — |
| `print_extraction_job_plan` | `(plan: ExtractionJobPlan, *, file: TextIO \| None = None) -> None` | — | — |
