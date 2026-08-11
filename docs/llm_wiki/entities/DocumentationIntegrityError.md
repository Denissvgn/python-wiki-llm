# DocumentationIntegrityError

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:247`
**Kind:** Class
**Bases:** `DocumentationRunError`
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Description

Raised when source, input-wiki, or generated ownership changed.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationIntegrityError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["DocumentationRunError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n2["DocumentationPersistedStateError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n3["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n4["_remove_built_site_before_builder (src/llm_wiki_cli/services/documentation_run/export.py)"]
    n5["_run_authorized_builder (src/llm_wiki_cli/services/documentation_run/export.py)"]
    n6["export_documentation_run (src/llm_wiki_cli/services/documentation_run/export.py)"]
    n7["_adopted_input_wiki_tree_hash (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n8["_capture_control_integrity_snapshot (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n9["_hash_exported_skill (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n10["_hash_skill_tree (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n11["_validate_stage_changed_paths (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n12["_verify_initial_integrity_anchors (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n13["_verify_read_only_inputs (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n14["_verify_stage_dispatch_integrity (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
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
    click n0 "../modules/documentation_run_contracts.md"
    click n1 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run_contracts.md"
    click n3 "../modules/documentation_run___init__.md"
    click n4 "../modules/export.md"
    click n5 "../modules/export.md"
    click n6 "../modules/export.md"
    click n7 "../modules/integrity.md"
    click n8 "../modules/integrity.md"
    click n9 "../modules/integrity.md"
    click n10 "../modules/integrity.md"
    click n11 "../modules/integrity.md"
    click n12 "../modules/integrity.md"
    click n13 "../modules/integrity.md"
    click n14 "../modules/integrity.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_run_contracts](../modules/documentation_run_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `DocumentationRunError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Subclass | `DocumentationPersistedStateError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [documentation_run___init__](../modules/documentation_run___init__.md) | — |
| `_remove_built_site_before_builder` | call | [export](../modules/export.md) | 7 |
| `_run_authorized_builder` | call | [export](../modules/export.md) | 1 |
| `export_documentation_run` | call | [export](../modules/export.md) | 5 |
| `_adopted_input_wiki_tree_hash` | call | [integrity](../modules/integrity.md) | 1 |
| `_capture_control_integrity_snapshot` | call | [integrity](../modules/integrity.md) | 2 |
| `_hash_exported_skill` | call | [integrity](../modules/integrity.md) | 3 |
| `_hash_skill_tree` | call | [integrity](../modules/integrity.md) | 1 |
| `_validate_stage_changed_paths` | call | [integrity](../modules/integrity.md) | 3 |
| `_verify_initial_integrity_anchors` | call | [integrity](../modules/integrity.md) | 10 |
| `_verify_read_only_inputs` | call | [integrity](../modules/integrity.md) | 7 |
| `_verify_stage_dispatch_integrity` | call | [integrity](../modules/integrity.md) | 12 |

> References: showing 12 of 60 logical references; 48 omitted by the 12-row generated summary limit.
