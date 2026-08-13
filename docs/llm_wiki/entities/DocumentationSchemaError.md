# DocumentationSchemaError

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:239`
**Kind:** Class
**Bases:** `DocumentationRunError`
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Description

Raised when a persisted or returned contract is invalid.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationSchemaError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["DocumentationRunError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n2["DocumentationPersistedStateError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n3["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n4["DocumentationAgentResult.from_dict (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n5["DocumentationIntakeBrief.from_dict (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n6["DocumentationIntakeBrief.from_values (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n7["_run_authorized_builder (src/llm_wiki_cli/services/documentation_run/export.py)"]
    n8["build_documentation_agent_packet (src/llm_wiki_cli/services/documentation_run/packet.py)"]
    n9["_prepare_documentation_run_impl (src/llm_wiki_cli/services/documentation_run/prepare.py)"]
    n10["_merge_agent_findings (src/llm_wiki_cli/services/documentation_run/record.py)"]
    n11["_preflight_documentation_native_evidence (src/llm_wiki_cli/services/documentation_run/record.py)"]
    n12["_reconcile_imported_page_edits (src/llm_wiki_cli/services/documentation_run/record.py)"]
    n13["_record_review_ledger_iteration (src/llm_wiki_cli/services/documentation_run/record.py)"]
    n14["_record_site_review_findings (src/llm_wiki_cli/services/documentation_run/record.py)"]
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
    click n4 "../modules/documentation_run_contracts.md"
    click n5 "../modules/documentation_run_contracts.md"
    click n6 "../modules/documentation_run_contracts.md"
    click n7 "../modules/export.md"
    click n8 "../modules/packet.md"
    click n9 "../modules/prepare.md"
    click n10 "../modules/record.md"
    click n11 "../modules/record.md"
    click n12 "../modules/record.md"
    click n13 "../modules/record.md"
    click n14 "../modules/record.md"
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
| `DocumentationAgentResult.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) | 5 |
| `DocumentationIntakeBrief.from_dict` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) | 19 |
| `DocumentationIntakeBrief.from_values` | call | [documentation_run_contracts](../modules/documentation_run_contracts.md) | 11 |
| `_run_authorized_builder` | call | [export](../modules/export.md) | 1 |
| `build_documentation_agent_packet` | call | [packet](../modules/packet.md) | 1 |
| `_prepare_documentation_run_impl` | call | [prepare](../modules/prepare.md) | 13 |
| `_merge_agent_findings` | call | [record](../modules/record.md) | 2 |
| `_preflight_documentation_native_evidence` | call | [record](../modules/record.md) | 6 |
| `_reconcile_imported_page_edits` | call | [record](../modules/record.md) | 1 |
| `_record_review_ledger_iteration` | call | [record](../modules/record.md) | 5 |
| `_record_site_review_findings` | call | [record](../modules/record.md) | 1 |

> References: showing 12 of 37 logical references; 25 omitted by the 12-row generated summary limit.
