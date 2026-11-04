# maintenance_state Module

**Path:** `src/llm_wiki_cli/services/maintenance_state.py`

## Description

Pure durable maintenance authority and explicit source/prose review transitions.

All inputs come from a caller-owned captured basis. This service performs no
filesystem I/O, parsing, generation, storage adoption, or human governance
mutation. The operation owner supplies the implementation validator and holds
the shared writer lock around capture and manifest-last publication.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `implementation_evidence`, `maintenance_shapes`, `python_implementation` |
| `.implementation_evidence` | `validate_implementation_evidence`, `validate_implementation_evidence` |
| `.knowledge_storage` | `canonical_bytes`, `digest` |
| `.maintenance_shapes` | `MaintenanceError`, `VALIDATORS`, `require` |
| `.validation` | `require_repository_relative_path` |
| `__future__` | `annotations` |
| `collections.abc` | `Callable` |
| `contextvars` | `ContextVar` |
| `copy` | `deepcopy` |
| `re` | `re` |
| `typing` | `Any` |
| `urllib.parse` | `quote`, `unquote` |
| `uuid` | `UUID`, `uuid4` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/maintenance_state.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/maintenance_state.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (16) |
| Outbound | `src` (5) |

> All 21 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [MaintenanceCore](../entities/MaintenanceCore.md) | 112 | — | Pure transitions with the installed implementation contract as authority. |
| [_MaintenanceReconciliation](../entities/MaintenanceReconciliation.md) | 1029 | — | One detached reconciliation; only membership-preserving observes are local. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `canonical_hash` | `(value: object) -> str` | — | Canonical maintenance commitments include the storage protocol LF. |
| `new_identity` | `() -> str` | — | Allocate once in the operation owner; persist and replay this identity. |
| `_identity` | `(value: str) -> None` | — | — |
| `_portable` | `(value: Any, field: str) -> str` | — | — |
| `_finite` | `(value: Any, depth: int = 0, active: set[int] \| None = None) -> None` | — | — |
| `maintenance_core` | `() -> MaintenanceCore` | — | Use the installed implementation contract, never a model-only callback. |
| `_detached` | `(value: object) -> dict[str, Any]` | — | — |
| `validate_maintenance_state` | `(value: object) -> dict[str, Any]` | — | — |
| `validate_maintenance_adoption` | `(value: object) -> dict[str, Any]` | — | — |
| `_callable_identity` | `(value)` | — | — |
| `_reconciliation_validator_identity` | `(core, operation)` | — | — |
| `_maintenance_reconciliation` | `(previous_state, core = None)` | — | Private invocation owner; no caller can waive public transition validation. |
| `_has_reconciliation_owner` | `() -> bool` | — | — |
| `maintenance_state_hash` | `(value: object) -> str` | — | — |
