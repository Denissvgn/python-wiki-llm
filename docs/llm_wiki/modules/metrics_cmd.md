# metrics_cmd Module

**Path:** `src/llm_wiki_cli/commands/metrics_cmd.py`

## Description

_Auto-generated from `src/llm_wiki_cli/commands/metrics_cmd.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `DEFAULT_WIKI_DIR`, `validate_path`, `validate_source_root` |
| `..services.metrics` | `load_events`, `summarize_events` |
| `__future__` | `annotations` |
| `json` | `json` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/metrics_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/metrics.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    n3 --> n2
    click n0 "../modules/cli.md"
    click n1 "../modules/metrics_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/metrics.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [metrics](../modules/metrics.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_fmt_percent` | `(value) -> str` | — | — |
| `_fmt_ms` | `(value) -> str` | — | — |
| `_fmt_counts` | `(value: object) -> str` | — | — |
| `render_text` | `(summary: dict, last: str) -> str` | — | — |
| `_fmt_phase_durations` | `(value: object) -> str` | — | — |
| `run` | `(args) -> None` | — | — |
