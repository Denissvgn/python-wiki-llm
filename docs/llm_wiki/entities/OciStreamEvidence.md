# OciStreamEvidence

**Location:** `src/llm_wiki_cli/services/calibration/broker.py:763`
**Kind:** Class
**Bases:** —
**Module:** [broker](../modules/broker.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Complete hash/count evidence with only a bounded captured prefix.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `sha256` | `str` | *required* | — |
| `bytes` | `int` | *required* | — |
| `captured_bytes` | `int` | *required* | — |
| `truncated` | `bool` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_dict` | `() -> dict[str, Any]` | — | — |
| `from_dict` | `(payload: Mapping[str, Any], *, label: str) -> 'OciStreamEvidence'` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["OciStreamEvidence (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1["OciStreamEvidence.from_dict (src/llm_wiki_cli/services/calibration/broker.py)"]
    n1 --> n0
    click n0 "../modules/broker.md"
    click n1 "../modules/broker.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [broker](../modules/broker.md) | 3 | `bytes`, `captured_bytes`, `sha256`, `truncated` |

### References

| Reference | Kind | Source |
|---|---|---|
| `OciStreamEvidence.from_dict` | type_reference | [broker](../modules/broker.md) |
