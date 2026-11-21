# context_session Module

**Path:** `src/llm_wiki_cli/services/context_session.py`

## Description

Provides bounded context reuse with private workspace ownership and authoritative on-disk validation. Scoped entries may share identical immutable byte buffers while retaining separate dependency observations; retained-memory accounting counts shared objects once. Read-only Git discovery is batched and uses disconnected stdin, so session identity commands cannot inherit a host protocol stream. Branch and index observations remain authoritative, and mutable producer sources remain fully checked. Supported deltas reconstruct the exact request/result schema; events are hints and unsaved buffers remain outside the on-disk contract.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `context_packet_builder` |
| `..` | `__version__` |
| `.task_compact` | `CompactTaskContext`, `_CheckedCounter`, `normalize_view_options`, `render_compact_task_context` |
| `.task_context` | `TaskCancelledError`, `TaskRead`, `_counter`, `build_task_read`, `plan_source_read`, `validate_task_context` |
| `.task_context_v2` | `ScopedTaskState` |
| `__future__` | `annotations` |
| `collections` | `OrderedDict` |
| `collections.abc` | `Callable`, `Mapping` |
| `dataclasses` | `dataclass`, `fields`, `is_dataclass`, `replace` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `llm_wiki_engine` | `analysis_compatibility` |
| `llm_wiki_engine.host` | `current_host` |
| `llm_wiki_engine.immutable` | `freeze` |
| `llm_wiki_engine.io` | `first_unsafe_path_component` |
| `llm_wiki_engine.path_policy` | `DEFAULT_WIKI_DIR`, `validate_path`, `validate_source_root` |
| `llm_wiki_engine.task_contract` | `TaskContext`, `normalize_task_request`, `TASK_REQUEST_SCHEMA_V2`, `TASK_RESULT_SCHEMA_V2` |
| `llm_wiki_engine.workflow_profile` | `WorkflowRequestError`, `bounded_int`, `canonical_json`, `content_id`, `exact_fields` |
| `math` | `math` |
| `os` | `os` |
| `pathlib` | `Path` |
| `shutil` | `shutil` |
| `subprocess` | `subprocess` |
| `sys` | `sys` |
| `threading` | `RLock` |
| `time` | `time` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/context_session.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/context_session.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (2) |
| Outbound | `src` (12) |

> All 14 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [SessionReply](../entities/SessionReply.md) | 127 | — | Portable content and separate non-identity session work telemetry. |
| [CompactSessionReply](../entities/CompactSessionReply.md) | 141 | — | — |
| [CanonicalReceipt](../entities/CanonicalReceipt.md) | 155 | — | — |
| [_Receipt](../entities/Receipt.md) | 167 | — | — |
| [_Entry](../entities/Entry.md) | 180 | — | — |
| [ContextSession](../entities/context_session_ContextSession.md) | 224 | — | A single trusted workspace. Methods serialize; events are hints only. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_memory_size` | `(value, seen = None)` | — | — |
| `_root_stamp` | `(path)` | — | — |
| `_git_identity` | `(root, metrics = None)` | — | Hash local branch/index metadata; commands are fixed read-only Git queries. |
| `_producer_identity` | `(metrics = None)` | — | — |
| `json_detach` | `(value)` | — | — |
| `build_delta` | `(base: TaskContext, current: TaskContext) -> dict[str, Any]` | — | — |
| `apply_task_delta` | `(base: str, delta: Mapping[str, Any], request: Mapping[str, Any], **options) -> TaskContext` | — | — |
