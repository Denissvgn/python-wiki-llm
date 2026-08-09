# circuit_breaker Module

**Path:** `src/llm_wiki_cli/services/circuit_breaker.py`

## Description

_Auto-generated from `src/llm_wiki_cli/services/circuit_breaker.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `datetime` | `datetime`, `timezone` |
| `json` | `json` |
| `math` | `math` |
| `os` | `os` |
| `pathlib` | `Path` |
| `tempfile` | `tempfile` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/status_cmd.py"]
    n1["src/llm_wiki_cli/commands/trigger_cmd.py"]
    n2["src/llm_wiki_cli/services/circuit_breaker.py"]
    n3["src/llm_wiki_cli/services/mcp_server.py"]
    n0 --> n2
    n1 --> n2
    n3 --> n2
    click n0 "../modules/status_cmd.md"
    click n1 "../modules/trigger_cmd.md"
    click n2 "../modules/circuit_breaker.md"
    click n3 "../modules/mcp_server.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [status_cmd](../modules/status_cmd.md) |
| Inbound | [trigger_cmd](../modules/trigger_cmd.md) |
| Inbound | [mcp_server](../modules/mcp_server.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_state_path` | `(git_dir: Path) -> Path` | — | — |
| `load_state` | `(git_dir: Path) -> dict` | — | — |
| `save_state` | `(git_dir: Path, state: dict) -> None` | — | Persist state atomically (write to tmp + rename). |
| `check_breaker` | `(git_dir: Path) -> bool` | — | Return whether an open breaker or active half-open probe blocks execution. |
| `record_success` | `(git_dir: Path) -> None` | — | — |
| `record_failure` | `(git_dir: Path) -> None` | — | — |
| `reset_breaker` | `(git_dir: Path) -> None` | — | — |
| `breaker_ttl_seconds` | `() -> float` | — | Return the configured non-negative automatic-recovery TTL. |
| `_timestamp_expired` | `(value: object, *, ttl_seconds: float) -> bool` | — | — |
