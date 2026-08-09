# doctor_cmd Module

**Path:** `src/llm_wiki_cli/commands/doctor_cmd.py`

## Description

CLI adapter for the read-only knowledge health report.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `DEFAULT_WIKI_DIR` |
| `..services.doctor_service` | `build_doctor_report`, `render_doctor_text` |
| `..services.extraction_jobs` | `extraction_job_request_from_args` |
| `__future__` | `annotations` |
| `json` | `json` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/doctor_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/doctor_service.py"]
    n4["src/llm_wiki_cli/services/extraction_jobs.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n4
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n3 --> n2
    n3 --> n4
    click n0 "../modules/cli.md"
    click n1 "../modules/doctor_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/doctor_service.md"
    click n4 "../modules/extraction_jobs.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [doctor_service](../modules/doctor_service.md) |
| Outbound | [extraction_jobs](../modules/extraction_jobs.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args) -> None` | — | — |
