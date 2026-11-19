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
| `llm_wiki_engine.host` | `emit` |
| `os` | `os` |
| `typing` | `Literal`, `TextIO` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/extraction_jobs.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/extraction_jobs.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (11) |
| Outbound | `src` (1) |

> All 12 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [ExtractionJobRequest](../entities/ExtractionJobRequest.md) | 15 | — | The user-facing extractor job request and its resolved worker limit. |
| [ExtractionJobsAction](../entities/ExtractionJobsAction.md) | 40 | `argparse.Action` | Resolve ``--jobs`` while preserving whether automatic sizing was requested. |
| [ExtractionJobPlan](../entities/ExtractionJobPlan.md) | 53 | — | A deterministic description of the extraction work about to run. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `extraction_job_request_for` | `(jobs: int \| None, requested_jobs: int \| str \| None = None) -> ExtractionJobRequest` | — | Build a request from resolved ``jobs`` and the raw request, if any. |
| `extraction_job_request_from_args` | `(args) -> ExtractionJobRequest` | — | Build a request from an argparse-compatible namespace. |
| `format_extraction_job_plan` | `(plan: ExtractionJobPlan) -> str` | — | — |
| `print_extraction_job_plan` | `(plan: ExtractionJobPlan, *, file: TextIO \| None = None) -> None` | — | — |
