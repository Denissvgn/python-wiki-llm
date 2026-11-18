# task_compact_delivery Module

**Path:** `src/llm_wiki_cli/services/task_compact_delivery.py`

## Description

One-shot compact delivery through the owned, locked task read lifecycle.

## Imports

| Source | Symbols |
|--------|---------|
| `.` | `analysis_compatibility` |
| `.context_session` | `ContextSession` |
| `.task_compact` | `CompactTaskContext` |
| `__future__` | `annotations` |
| `llm_wiki_engine.path_policy` | `DEFAULT_WIKI_DIR` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/services/analysis_compatibility.py"]
    n2["src/llm_wiki_cli/services/context_session.py"]
    n3["src/llm_wiki_cli/services/task_compact.py"]
    n4["src/llm_wiki_cli/services/task_compact_delivery.py"]
    n5["src/llm_wiki_engine/path_policy.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n4
    n2 --> n1
    n2 --> n3
    n2 --> n5
    n4 --> n1
    n4 --> n2
    n4 --> n3
    n4 --> n5
    click n0 "../modules/api.md"
    click n1 "../modules/analysis_compatibility.md"
    click n2 "../modules/context_session.md"
    click n3 "../modules/task_compact.md"
    click n4 "../modules/task_compact_delivery.md"
    click n5 "../modules/path_policy.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Outbound | [analysis_compatibility](../modules/analysis_compatibility.md) |
| Outbound | [context_session](../modules/context_session.md) |
| Outbound | [task_compact](../modules/task_compact.md) |
| Outbound | [path_policy](../modules/path_policy.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `build_compact_task_context` | `(request, *, view_options = None, src_dir = '.', wiki_dir = DEFAULT_WIKI_DIR, profile = None, policy = None, counter = None, allow_external_src = False, source_selection = None, helper_cache_dir = None, cancelled = None) -> CompactTaskContext` | `@ac.bound_comparison` | Return a complete current view and its exact separately budgeted receipt. |
