# ContextSession

**Location:** `src/llm_wiki_cli/services/context_session.py:223`
**Kind:** Class
**Bases:** —
**Module:** [context_session](../modules/context_session.md)

## Description

The bounded session implementation owns capture and rendering reuse, input revalidation, expiry and eviction. Caller mutations cannot change retained results. Missing validation capabilities fall back to cold reads, and unsaved buffers require save or defer handling.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(*, src_dir = '.', wiki_dir = DEFAULT_WIKI_DIR, profile = None, policy = None, counter = None, source_selection = None, helper_cache_dir = None, allow_external_src = False, max_entries = 8, max_bytes = 16777216, ttl_seconds: float = 300)` | — | — |
| `_roots_current` | `()` | — | — |
| `_environment` | `()` | — | — |
| `_clear` | `()` | — | — |
| `_identity` | `(entry)` | `@staticmethod` | — |
| `_recount` | `()` | — | — |
| `_touch` | `(identity)` | — | — |
| `_drop_identity` | `(identity)` | — | — |
| `_drop` | `(key)` | — | — |
| `_bound_custody` | `()` | — | — |
| `_expire` | `()` | — | — |
| `_publication_cancelled` | `(cancelled)` | — | — |
| `_check_publication` | `(read, environment, request, profile, counter, cancelled, roots)` | — | — |
| `_share_inputs` | `(read)` | — | Intern immutable bytes within this workspace; receipts stay per entry. |
| `_owns` | `(entry)` | — | — |
| `_reusable_read` | `(read, environment)` | `@staticmethod` | — |
| `_validate` | `(entry, environment, request, profile, counter, *, cold = False, after_portable = None)` | — | — |
| `_build` | `(request, *, cancelled, shared = None)` | — | — |
| `_compatible_capture` | `(normalized, profile, environment)` | — | — |
| `read` | `(request, *, if_result_id = None, delta = False, reuse = True, cancelled: Callable[[], bool] \| None = None) -> SessionReply` | `@ac.bound_comparison` | — |
| `read_compact` | `(request, *, view_options = None, if_result_id = None, if_view_id = None, delta = False, reuse = True, cancelled: Callable[[], bool] \| None = None) -> CompactSessionReply` | `@ac.bound_comparison` | — |
| `_read` | `(request, *, if_result_id = None, delta = False, reuse = True, cancelled = None, view_options = None, if_view_id = None)` | — | — |
| `canonical_receipt` | `(request_id, result_id, *, current = False, cancelled: Callable[[], bool] \| None = None) -> CanonicalReceipt` | `@ac.bound_comparison` | — |
| `_canonical_receipt` | `(request_id, result_id, *, current, cancelled)` | — | — |
| `hint` | `(*, unsaved_buffers = False)` | `@ac.bound_comparison` | — |
| `close` | `()` | `@ac.bound_comparison` | — |
| `__enter__` | `()` | — | — |
| `__exit__` | `(*_)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextSession (src/llm_wiki_cli/services/context_session.py)"]
    n1["ContextSession (src/llm_wiki_cli/api.py)"]
    n2["src/llm_wiki_cli/api.py"]
    n3["build_compact_task_context (src/llm_wiki_cli/services/task_compact_delivery.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/context_session.md"
    click n1 "../modules/api.md"
    click n2 "../modules/api.md"
    click n3 "../modules/task_compact_delivery.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_session](../modules/context_session.md) | 28 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Subclass | `ContextSession` | [api](../modules/api.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `api` | import | [api](../modules/api.md) | — |
| `build_compact_task_context` | call | [task_compact_delivery](../modules/task_compact_delivery.md) | 1 |
