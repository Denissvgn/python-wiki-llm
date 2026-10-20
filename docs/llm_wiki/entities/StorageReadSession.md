# StorageReadSession

**Location:** `src/llm_wiki_cli/services/knowledge_storage_io.py:313`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_storage_io](../modules/knowledge_storage_io.md)

## Description

Retains request-owned observations of complete files and pack ranges. It counts actual bytes and read operations, enforces a cumulative budget and rejects inconsistent file identities across members of a pack. Final rechecks reread the consumed bytes through the same guarded filesystem owner; cache reuse never substitutes for this validation.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(wiki_dir: str \| Path, *, max_bytes: int = MAX_EXPANDED_BYTES, max_handles: int = 128, cancelled = None, coalesce_rechecks: bool = False)` | — | — |
| `phase` | `()` | `@contextmanager` | Keep observations provisional until successful phase validation and release. |
| `_read_guarded` | `(*args, **kwargs)` | — | — |
| `read` | `(relative: str, maximum: int) -> bytes` | — | — |
| `recheck` | `() -> None` | — | — |
| `read_range` | `(relative: str, offset: int, length: int, file_bytes: int) -> bytes` | — | Read and retain an authenticated member range, without reading its whole pack. |
| `_remember_range` | `(key, observed)` | — | — |
| `read_ranges` | `(ranges)` | — | Coalesce exact neighbours only: zero speculative or uncharged bytes. |
| `recheck_work` | `()` | — | — |
| `receipt` | `() -> dict[str, Any]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["StorageReadSession (src/llm_wiki_cli/services/knowledge_storage_io.py)"]
    n1["_plan_source_page_transitions (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["inspect_targets (src/llm_wiki_cli/services/analysis_targets.py)"]
    n3["validate_knowledge_artifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n4["preflight (src/llm_wiki_cli/services/knowledge_maintenance.py)"]
    n5["capture_knowledge_slice (src/llm_wiki_cli/services/knowledge_storage_access.py)"]
    n6["_committed_inputs (src/llm_wiki_cli/services/knowledge_storage_lifecycle.py)"]
    n7["_recover_knowledge_storage (src/llm_wiki_cli/services/knowledge_storage_lifecycle.py)"]
    n8["restore_pruned_storage (src/llm_wiki_cli/services/knowledge_storage_lifecycle.py)"]
    n9["capture_discovery (src/llm_wiki_cli/services/search_discovery_capture.py)"]
    n10["search_prevalidated_roots (src/llm_wiki_cli/services/search_service.py)"]
    n11["capture_source_index (src/llm_wiki_cli/services/search_source.py)"]
    n12["captured_manifest (src/llm_wiki_cli/services/search_source.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    n12 --> n0
    click n0 "../modules/knowledge_storage_io.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/analysis_targets.md"
    click n3 "../modules/knowledge_artifacts.md"
    click n4 "../modules/knowledge_maintenance.md"
    click n5 "../modules/knowledge_storage_access.md"
    click n6 "../modules/knowledge_storage_lifecycle.md"
    click n7 "../modules/knowledge_storage_lifecycle.md"
    click n8 "../modules/knowledge_storage_lifecycle.md"
    click n9 "../modules/search_discovery_capture.md"
    click n10 "../modules/search_service.md"
    click n11 "../modules/search_source.md"
    click n12 "../modules/search_source.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_storage_io](../modules/knowledge_storage_io.md) | 10 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_plan_source_page_transitions` | call | [sync_cmd](../modules/sync_cmd.md) | 1 |
| `inspect_targets` | call | [analysis_targets](../modules/analysis_targets.md) | 1 |
| `validate_knowledge_artifacts` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 2 |
| `preflight` | call | [knowledge_maintenance](../modules/knowledge_maintenance.md) | 1 |
| `capture_knowledge_slice` | call | [knowledge_storage_access](../modules/knowledge_storage_access.md) | 1 |
| `_committed_inputs` | call | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | 1 |
| `_recover_knowledge_storage` | call | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | 1 |
| `restore_pruned_storage` | call | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | 1 |
| `capture_discovery` | type_reference | [search_discovery_capture](../modules/search_discovery_capture.md) | — |
| `search_prevalidated_roots` | call | [search_service](../modules/search_service.md) | 2 |
| `capture_source_index` | type_reference | [search_source](../modules/search_source.md) | — |
| `captured_manifest` | type_reference | [search_source](../modules/search_source.md) | — |

> References: showing 12 of 18 logical references; 6 omitted by the 12-row generated summary limit.
