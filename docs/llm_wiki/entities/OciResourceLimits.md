# OciResourceLimits

**Location:** `src/llm_wiki_cli/services/calibration/broker.py:209`
**Kind:** Class
**Bases:** —
**Module:** [broker](../modules/broker.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Portable Docker/Podman resource ceilings.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `pids_limit` | `int` | *required* | — |
| `memory_bytes` | `int` | *required* | — |
| `cpu_millis` | `int` | *required* | — |
| `tmpfs_bytes` | `int` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, int]` | — | — |
| `from_dict` | `(payload: Mapping[str, Any]) -> 'OciResourceLimits'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["OciResourceLimits (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1["OciResourceLimits.from_dict (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1 --> n0
    click n0 "../modules/broker.md"
    click n1 "../modules/broker.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [broker](../modules/broker.md) | 3 | `cpu_millis`, `memory_bytes`, `pids_limit`, `tmpfs_bytes` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `OciResourceLimits.from_dict` | type_reference | [broker](../modules/broker.md) | — |
