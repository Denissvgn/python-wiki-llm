# ci_check_cmd Module

**Path:** `src/llm_wiki_cli/commands/ci_check_cmd.py`

## Description

Runs the lint service in strict mode for automation. The command validates
source and wiki paths, emits the selected console format, always writes a
Markdown report, records best-effort local metrics, and returns a failing exit
status when blocking wiki issues remain.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `DEFAULT_WIKI_DIR`, `validate_path`, `validate_source_root` |
| `..services.extraction_jobs` | `extraction_job_request_from_args`, `print_extraction_job_plan` |
| `..services.inventory_cache` | `InventoryCacheOptions` |
| `..services.lint_service` | `build_report`, `render_markdown`, `render_text`, `report_to_dict` |
| `..services.metrics` | `record_validation_event` |
| `__future__` | `annotations` |
| `json` | `json` |
| `pathlib` | `Path` |
| `sys` | `sys` |
| `time` | `time` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/ci_check_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/extraction_jobs.py"]
    n4["src/llm_wiki_cli/services/inventory_cache.py"]
    n5["src/llm_wiki_cli/services/lint_service.py"]
    n6["src/llm_wiki_cli/services/metrics.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n5
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n4 --> n2
    n5 --> n2
    n5 --> n3
    n5 --> n4
    n5 --> n6
    n6 --> n2
    n6 --> n5
    click n0 "../modules/cli.md"
    click n1 "../modules/ci_check_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/extraction_jobs.md"
    click n4 "../modules/inventory_cache.md"
    click n5 "../modules/lint_service.md"
    click n6 "../modules/metrics.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [extraction_jobs](../modules/extraction_jobs.md) |
| Outbound | [inventory_cache](../modules/inventory_cache.md) |
| Outbound | [lint_service](../modules/lint_service.md) |
| Outbound | [metrics](../modules/metrics.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_render_console` | `(report, output_format: str) -> str` | — | — |
| `run` | `(args) -> None` | — | — |