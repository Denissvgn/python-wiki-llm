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
| `..services.ci_report` | `build_ci_check_payload` |
| `..services.extraction_jobs` | `extraction_job_request_from_args`, `print_extraction_job_plan` |
| `..services.inventory_cache` | `InventoryCacheStats`, `cache_options_from_args`, `format_cache_stats`, `prepare_cache_options` |
| `..services.io` | `write_bytes_atomic` |
| `..services.lint_service` | `build_report`, `render_markdown`, `render_text` |
| `..services.metrics` | `record_validation_event` |
| `..services.progress` | `observed_phase` |
| `..services.runtime_output` | `RuntimeDestination`, `RuntimeOutputError`, `prepare_destination`, `stderr_warning` |
| `__future__` | `annotations` |
| `dataclasses` | `replace` |
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
    n3["src/llm_wiki_cli/services/ci_report.py"]
    n4["src/llm_wiki_cli/services/extraction_jobs.py"]
    n5["src/llm_wiki_cli/services/inventory_cache.py"]
    n6["src/llm_wiki_cli/services/io.py"]
    n7["src/llm_wiki_cli/services/lint_service.py"]
    n8["src/llm_wiki_cli/services/metrics.py"]
    n9["src/llm_wiki_cli/services/progress.py"]
    n10["src/llm_wiki_cli/services/runtime_output.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n4
    n0 --> n7
    n0 --> n9
    n0 --> n10
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n1 --> n7
    n1 --> n8
    n1 --> n9
    n1 --> n10
    n2 --> n6
    n3 --> n7
    n5 --> n2
    n5 --> n6
    n5 --> n9
    n5 --> n10
    n7 --> n2
    n7 --> n4
    n7 --> n5
    n7 --> n6
    n7 --> n8
    n7 --> n9
    n8 --> n2
    n8 --> n7
    click n0 "../modules/cli.md"
    click n1 "../modules/ci_check_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/ci_report.md"
    click n4 "../modules/extraction_jobs.md"
    click n5 "../modules/inventory_cache.md"
    click n6 "../modules/io.md"
    click n7 "../modules/lint_service.md"
    click n8 "../modules/metrics.md"
    click n9 "../modules/progress.md"
    click n10 "../modules/runtime_output.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [ci_report](../modules/ci_report.md) |
| Outbound | [extraction_jobs](../modules/extraction_jobs.md) |
| Outbound | [inventory_cache](../modules/inventory_cache.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [lint_service](../modules/lint_service.md) |
| Outbound | [metrics](../modules/metrics.md) |
| Outbound | [progress](../modules/progress.md) |
| Outbound | [runtime_output](../modules/runtime_output.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_render_console` | `(report, output_format: str, **payload_options) -> str` | — | — |
| `_report_destination` | `(args) -> RuntimeDestination` | — | — |
| `_persist_report` | `(destination: RuntimeDestination, report) -> int` | `@observed_phase('report_persistence')` | — |
| `run` | `(args) -> None` | — | — |