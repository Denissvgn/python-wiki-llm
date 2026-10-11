# KnowledgeStorageError

**Location:** `src/llm_wiki_cli/services/knowledge_storage.py:45`
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
    n0["KnowledgeStorageError (src/llm_wiki_cli/services/knowledge_storage.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/api.py"]
    n3["src/llm_wiki_cli/commands/task_cmd.py"]
    n4["build_knowledge_commit_plan (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n5["validate_knowledge_artifacts (src/llm_wiki_cli/services/knowledge_artifacts.py)"]
    n6["audit_logical_records (src/llm_wiki_cli/services/knowledge_audit.py)"]
    n7["audit_spilled_records (src/llm_wiki_cli/services/knowledge_audit.py)"]
    n8["expected_records (src/llm_wiki_cli/services/knowledge_audit.py)"]
    n9["_fail (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n10["_pack_structure (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n11["decode_member (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n12["inspect_pack (src/llm_wiki_cli/services/knowledge_packs.py)"]
    n13["_concept_aliases (src/llm_wiki_cli/services/knowledge_storage.py)"]
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
    click n3 "../modules/task_cmd.md"
    click n4 "../modules/knowledge_artifacts.md"
    click n5 "../modules/knowledge_artifacts.md"
    click n6 "../modules/knowledge_audit.md"
    click n7 "../modules/knowledge_audit.md"
    click n8 "../modules/knowledge_audit.md"
    click n9 "../modules/knowledge_packs.md"
    click n10 "../modules/knowledge_packs.md"
    click n11 "../modules/knowledge_packs.md"
    click n12 "../modules/knowledge_packs.md"
    click n13 "../modules/knowledge_storage.md"
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
| `api` | import | [api](../modules/api.md) | — |
| `task_cmd` | import | [task_cmd](../modules/task_cmd.md) | — |
| `build_knowledge_commit_plan` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 2 |
| `validate_knowledge_artifacts` | call | [knowledge_artifacts](../modules/knowledge_artifacts.md) | 5 |
| `audit_logical_records` | call | [knowledge_audit](../modules/knowledge_audit.md) | 3 |
| `audit_spilled_records` | call | [knowledge_audit](../modules/knowledge_audit.md) | 2 |
| `expected_records` | call | [knowledge_audit](../modules/knowledge_audit.md) | 1 |
| `_fail` | call | [knowledge_packs](../modules/knowledge_packs.md) | 1 |
| `_pack_structure` | call | [knowledge_packs](../modules/knowledge_packs.md) | 1 |
| `decode_member` | call | [knowledge_packs](../modules/knowledge_packs.md) | 1 |
| `inspect_pack` | call | [knowledge_packs](../modules/knowledge_packs.md) | 1 |
| `_concept_aliases` | call | [knowledge_storage](../modules/knowledge_storage.md) | 1 |

> References: showing 12 of 83 logical references; 71 omitted by the 12-row generated summary limit.
