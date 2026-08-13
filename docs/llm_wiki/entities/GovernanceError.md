# GovernanceError

**Location:** `src/llm_wiki_cli/services/knowledge_governance.py:111`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_governance](../modules/knowledge_governance.md)

## Description

A field-specific governance validation or mutation failure.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str, *, code: str = 'governance-invalid')` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["GovernanceError (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n1["ValueError"]
    n2["GovernanceConflictError (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n3["_assert_bundle_continuity (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n4["_assert_snapshot_unchanged (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n5["_committed_artifact_snapshot (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n6["_concept_for_uid (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n7["_init_ledger (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n8["_load_required_ledger (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n9["_read_bytes (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n10["_run_lifecycle (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n11["_run_review (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n12["_run_status (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n13["_run_verify (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
    n14["_scope_locator_for_uid (src/llm_wiki_cli/commands/knowledge_cmd.py)"]
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
    n14 --> n0
    click n0 "../modules/knowledge_governance.md"
    click n2 "../modules/knowledge_governance.md"
    click n3 "../modules/knowledge_cmd.md"
    click n4 "../modules/knowledge_cmd.md"
    click n5 "../modules/knowledge_cmd.md"
    click n6 "../modules/knowledge_cmd.md"
    click n7 "../modules/knowledge_cmd.md"
    click n8 "../modules/knowledge_cmd.md"
    click n9 "../modules/knowledge_cmd.md"
    click n10 "../modules/knowledge_cmd.md"
    click n11 "../modules/knowledge_cmd.md"
    click n12 "../modules/knowledge_cmd.md"
    click n13 "../modules/knowledge_cmd.md"
    click n14 "../modules/knowledge_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_governance](../modules/knowledge_governance.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |
| Subclass | `GovernanceConflictError` | [knowledge_governance](../modules/knowledge_governance.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_assert_bundle_continuity` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 1 |
| `_assert_snapshot_unchanged` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 1 |
| `_committed_artifact_snapshot` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 2 |
| `_concept_for_uid` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 2 |
| `_init_ledger` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 1 |
| `_load_required_ledger` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 1 |
| `_read_bytes` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 3 |
| `_run_lifecycle` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 1 |
| `_run_review` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 1 |
| `_run_status` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 2 |
| `_run_verify` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 1 |
| `_scope_locator_for_uid` | call | [knowledge_cmd](../modules/knowledge_cmd.md) | 1 |

> References: showing 12 of 73 logical references; 61 omitted by the 12-row generated summary limit.
