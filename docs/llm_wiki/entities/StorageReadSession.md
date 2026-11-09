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
    n1["_write (src/llm_wiki_cli/commands/publication_candidate_cmd.py)"]
    n2["_write (src/llm_wiki_cli/commands/publication_cmd.py)"]
    n3["run (src/llm_wiki_cli/commands/reference_cmd.py)"]
    n4["_plan_source_page_transitions (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n5["inspect_targets (src/llm_wiki_cli/services/analysis_targets.py)"]
    n6["validate_knowledge_artifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n7["preflight (src/llm_wiki_cli/services/knowledge_maintenance.py)"]
    n8["maintenance_reuse_check (src/llm_wiki_cli/services/knowledge_reuse.py)"]
    n9["capture_knowledge_slice (src/llm_wiki_cli/services/knowledge_storage_access.py)"]
    n10["_referenced_storage_report (src/llm_wiki_cli/services/knowledge_storage_diagnostics.py)"]
    n11["_committed_inputs (src/llm_wiki_cli/services/knowledge_storage_lifecycle.py)"]
    n12["_recover_knowledge_storage (src/llm_wiki_cli/services/knowledge_storage_lifecycle.py)"]
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
    click n1 "../modules/publication_candidate_cmd.md"
    click n2 "../modules/publication_cmd.md"
    click n3 "../modules/reference_cmd.md"
    click n4 "../modules/sync_cmd.md"
    click n5 "../modules/analysis_targets.md"
    click n6 "../modules/knowledge_artifacts.md"
    click n7 "../modules/knowledge_maintenance.md"
    click n8 "../modules/knowledge_reuse.md"
    click n9 "../modules/knowledge_storage_access.md"
    click n10 "../modules/knowledge_storage_diagnostics.md"
    click n11 "../modules/knowledge_storage_lifecycle.md"
    click n12 "../modules/knowledge_storage_lifecycle.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_storage_io](../modules/knowledge_storage_io.md) | 10 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_write` | call | [publication_candidate_cmd](../modules/publication_candidate_cmd.md) | 1 |
| `_write` | call | [publication_cmd](../modules/publication_cmd.md) | 1 |
| `run` | call | [reference_cmd](../modules/reference_cmd.md) | 1 |
| `_plan_source_page_transitions` | call | [sync_cmd](../modules/sync_cmd.md) | 1 |
| `inspect_targets` | call | [analysis_targets](../modules/analysis_targets.md) | 1 |
| `validate_knowledge_artifacts` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 2 |
| `preflight` | call | [knowledge_maintenance](../modules/knowledge_maintenance.md) | 1 |
| `maintenance_reuse_check` | call | [knowledge_reuse](../modules/knowledge_reuse.md) | 1 |
| `capture_knowledge_slice` | call | [knowledge_storage_access](../modules/knowledge_storage_access.md) | 1 |
| `_referenced_storage_report` | call | [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md) | 1 |
| `_committed_inputs` | call | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | 1 |
| `_recover_knowledge_storage` | call | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) | 1 |

> References: showing 12 of 31 logical references; 19 omitted by the 12-row generated summary limit.
