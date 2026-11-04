# WikiWriteBasis

**Location:** `src/llm_wiki_cli/services/maintenance_protocol.py:200`
**Kind:** Class
**Bases:** —
**Module:** [maintenance_protocol](../modules/maintenance_protocol.md)

**Decorators:** `@dataclass`

## Description

_Auto-generated from `WikiWriteBasis` in `src/llm_wiki_cli/services/maintenance_protocol.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `root` | `Path` | *required* | — |
| `expected` | `MutableMapping[str, bytes]` | *required* | — |
| `source_snapshot` | `SourceSnapshot \| None` | `None` | — |
| `recovery_directory` | `Path \| None` | `None` | — |
| `eligible_images` | `dict[str, list[str \| None]] \| None` | `None` | — |
| `include_transient` | `bool` | `False` | — |
| `recovery_marker` | `dict \| None` | `None` | — |
| `recovery_started` | `bool` | `True` | — |
| `changed` | `bool` | `False` | — |
| `preimages` | `Mapping[str, bytes]` | `field(init=False)` | — |
| `_storage_staging` | `_StorageStagingAuthority \| None` | `field(default=None, init=False, repr=False)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `()` | — | — |
| `_relative` | `(path: Path) -> str \| None` | — | — |
| `bind_committed_state` | `(state: CommittedKnowledgeState) -> None` | — | Bind one owning sync's validated prior closure, never a caller skip flag. |
| `_close_storage_staging` | `() -> None` | — | — |
| `_is_unreferenced_storage_staging` | `(relative, content, previous, current) -> bool` | — | — |
| `before_write` | `(path: Path, content: bytes \| None) -> None` | — | — |
| `after_write` | `(path: Path, content: bytes \| None) -> None` | — | — |
| `assert_current` | `() -> None` | `@observed_phase('maintenance_verification')` | — |
| `assert_source_current` | `() -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["WikiWriteBasis (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n1["bootstrap_write_operation (src/llm_wiki_cli/services/bootstrap_recovery.py)"]
    n2["maintenance_write_operation (src/llm_wiki_cli/services/maintenance_protocol.py)"]
    n3["_capture_basis (src/llm_wiki_cli/services/maintenance_service.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/maintenance_protocol.md"
    click n1 "../modules/bootstrap_recovery.md"
    click n2 "../modules/maintenance_protocol.md"
    click n3 "../modules/maintenance_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [maintenance_protocol](../modules/maintenance_protocol.md) | 9 | `_storage_staging`, `changed`, `eligible_images`, `expected`, `include_transient`, `preimages`, `recovery_directory`, `recovery_marker`, `recovery_started`, `root`, `source_snapshot` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `bootstrap_write_operation` | call | [bootstrap_recovery](../modules/bootstrap_recovery.md) | 1 |
| `maintenance_write_operation` | call | [maintenance_protocol](../modules/maintenance_protocol.md) | 1 |
| `_capture_basis` | call | [maintenance_service](../modules/maintenance_service.md) | 1 |
