# KnowledgeStorageError

**Location:** `src/llm_wiki_engine/knowledge_storage.py:49`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_storage](../modules/knowledge_storage.md)

## Description

A field-specific storage failure with a stable code for malformed data, incompatible formats, mutation or bounded-work exhaustion. Callers preserve these distinctions when reporting unavailable or invalid native input.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str, *, code: str = 'storage-invalid')` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeStorageError (src/llm_wiki_engine/knowledge_storage.py)"]
    n1["ValueError"]
    n2["_selected_knowledge_records (src/llm_wiki_cli/api.py)"]
    n3["_selected_surface_pages (src/llm_wiki_cli/api.py)"]
    n4["src/llm_wiki_cli/commands/publication_candidate_cmd.py"]
    n5["src/llm_wiki_cli/commands/publication_cmd.py"]
    n6["src/llm_wiki_cli/commands/task_cmd.py"]
    n7["maintenance_reuse_check (src/llm_wiki_cli/services/knowledge_reuse.py)"]
    n8["src/llm_wiki_cli/services/module_coverage.py"]
    n9["_build_snapshot (src/llm_wiki_cli/services/publication_snapshot.py)"]
    n10["src/llm_wiki_cli/services/sync_analysis_cache.py"]
    n11["src/llm_wiki_cli/services/sync_generated_sections.py"]
    n12["src/llm_wiki_cli/services/sync_transitions.py"]
    n13["ScopedTaskState.revalidate (src/llm_wiki_cli/services/task_context_v2.py)"]
    n0 --> n1
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
    n13 --> n0
    click n0 "../modules/knowledge_storage.md"
    click n2 "../modules/api.md"
    click n3 "../modules/api.md"
    click n4 "../modules/publication_candidate_cmd.md"
    click n5 "../modules/publication_cmd.md"
    click n6 "../modules/task_cmd.md"
    click n7 "../modules/knowledge_reuse.md"
    click n8 "../modules/module_coverage.md"
    click n9 "../modules/publication_snapshot.md"
    click n10 "../modules/sync_analysis_cache.md"
    click n11 "../modules/sync_generated_sections.md"
    click n12 "../modules/sync_transitions.md"
    click n13 "../modules/task_context_v2.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_storage](../modules/knowledge_storage.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_selected_knowledge_records` | call | [api](../modules/api.md) | 1 |
| `_selected_surface_pages` | call | [api](../modules/api.md) | 1 |
| `publication_candidate_cmd` | import | [publication_candidate_cmd](../modules/publication_candidate_cmd.md) | — |
| `publication_cmd` | import | [publication_cmd](../modules/publication_cmd.md) | — |
| `task_cmd` | import | [task_cmd](../modules/task_cmd.md) | — |
| `maintenance_reuse_check` | call | [knowledge_reuse](../modules/knowledge_reuse.md) | 2 |
| `module_coverage` | import | [module_coverage](../modules/module_coverage.md) | — |
| `_build_snapshot` | call | [publication_snapshot](../modules/publication_snapshot.md) | 5 |
| `sync_analysis_cache` | import | [sync_analysis_cache](../modules/sync_analysis_cache.md) | — |
| `sync_generated_sections` | import | [sync_generated_sections](../modules/sync_generated_sections.md) | — |
| `sync_transitions` | import | [sync_transitions](../modules/sync_transitions.md) | — |
| `ScopedTaskState.revalidate` | call | [task_context_v2](../modules/task_context_v2.md) | 3 |

> References: showing 12 of 102 logical references; 90 omitted by the 12-row generated summary limit.
