# runtime_output Module

**Path:** `src/llm_wiki_cli/services/runtime_output.py`

## Description

Best-effort implicit output and preflighted operator-selected destinations.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections.abc` | `Callable` |
| `dataclasses` | `dataclass` |
| `os` | `os` |
| `pathlib` | `Path` |
| `sys` | `sys` |
| `tempfile` | `tempfile` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/ci_check_cmd.py"]
    n2["src/llm_wiki_cli/services/inventory_cache.py"]
    n3["src/llm_wiki_cli/services/runtime_output.py"]
    n0 --> n1
    n0 --> n3
    n1 --> n2
    n1 --> n3
    n2 --> n3
    click n0 "../modules/cli.md"
    click n1 "../modules/ci_check_cmd.md"
    click n2 "../modules/inventory_cache.md"
    click n3 "../modules/runtime_output.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Inbound | [ci_check_cmd](../modules/ci_check_cmd.md) |
| Inbound | [inventory_cache](../modules/inventory_cache.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [RuntimeOutputError](../entities/RuntimeOutputError.md) | 13 | `ValueError` | An explicitly requested runtime destination is unusable. |
| [RuntimeDestination](../entities/RuntimeDestination.md) | 37 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `stderr_warning` | `(message: str) -> None` | — | Warnings do not interfere with machine-readable stdout or computation. |
| `warn` | `(sink: WarningSink \| None, message: str) -> None` | — | — |
| `preflight_output_path` | `(path: Path) -> None` | — | Probe same-directory creation/replacement without touching the real output. |
| `prepare_destination` | `(path: Path \| None, *, kind: str, explicit: bool = False, warning: WarningSink \| None = None) -> RuntimeDestination` | — | — |
