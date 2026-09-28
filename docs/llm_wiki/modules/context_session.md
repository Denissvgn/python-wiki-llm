# context_session Module

**Path:** `src/llm_wiki_cli/services/context_session.py`

## Description

Provides bounded context reuse with private workspace ownership and authoritative on-disk validation. Scoped entries may share identical immutable byte buffers while retaining separate dependency observations; retained-memory accounting counts shared objects once. Read-only Git discovery is batched, and mutable producer sources remain fully checked. Supported deltas reconstruct the exact request/result schema; events are hints and unsaved buffers remain outside the on-disk contract.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `analysis_compatibility`, `context_packet` |
| `..` | `__version__` |
| `..config` | `DEFAULT_WIKI_DIR`, `validate_path`, `validate_source_root` |
| `.immutable` | `freeze` |
| `.io` | `first_unsafe_path_component` |
| `.task_context` | `TaskCancelledError`, `TaskRead`, `_counter`, `build_task_read`, `plan_source_read`, `validate_task_context` |
| `.task_contract` | `TaskContext`, `normalize_task_request`, `TASK_REQUEST_SCHEMA_V2`, `TASK_RESULT_SCHEMA_V2` |
| `.workflow_profile` | `WorkflowRequestError`, `bounded_int`, `canonical_json`, `content_id`, `exact_fields` |
| `__future__` | `annotations` |
| `collections` | `OrderedDict` |
| `collections.abc` | `Callable`, `Mapping` |
| `dataclasses` | `dataclass`, `fields`, `is_dataclass`, `replace` |
| `hashlib` | `hashlib` |
| `json` | `json` |
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
    n0["src/llm_wiki_cli/__init__.py"]
    n1["src/llm_wiki_cli/api.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/analysis_compatibility.py"]
    n4["src/llm_wiki_cli/services/context_packet.py"]
    n5["src/llm_wiki_cli/services/context_session.py"]
    n6["src/llm_wiki_cli/services/immutable.py"]
    n7["src/llm_wiki_cli/services/io.py"]
    n8["src/llm_wiki_cli/services/task_context.py"]
    n9["src/llm_wiki_cli/services/task_contract.py"]
    n10["src/llm_wiki_cli/services/workflow_profile.py"]
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n8
    n1 --> n9
    n1 --> n10
    n2 --> n7
    n4 --> n0
    n4 --> n2
    n5 --> n0
    n5 --> n2
    n5 --> n3
    n5 --> n4
    n5 --> n6
    n5 --> n7
    n5 --> n8
    n5 --> n9
    n5 --> n10
    n8 --> n2
    n8 --> n4
    n8 --> n7
    n8 --> n9
    n8 --> n10
    n9 --> n10
    click n0 "../modules/llm_wiki_cli___init__.md"
    click n1 "../modules/api.md"
    click n2 "../modules/config.md"
    click n3 "../modules/analysis_compatibility.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_session.md"
    click n6 "../modules/immutable.md"
    click n7 "../modules/io.md"
    click n8 "../modules/task_context.md"
    click n9 "../modules/task_contract.md"
    click n10 "../modules/workflow_profile.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Outbound | [llm_wiki_cli___init__](../modules/llm_wiki_cli___init__.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [analysis_compatibility](../modules/analysis_compatibility.md) |
| Outbound | [context_packet](../modules/context_packet.md) |
| Outbound | [immutable](../modules/immutable.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [task_context](../modules/task_context.md) |
| Outbound | [task_contract](../modules/task_contract.md) |
| Outbound | [workflow_profile](../modules/workflow_profile.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [SessionReply](../entities/SessionReply.md) | 124 | — | Portable content and separate non-identity session work telemetry. |
| [_Entry](../entities/Entry.md) | 143 | — | — |
| [ContextSession](../entities/context_session_ContextSession.md) | 187 | — | A single trusted workspace. Methods serialize; events are hints only. |

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