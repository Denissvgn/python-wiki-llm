# DocumentationTransitionError

**Location:** `src/llm_wiki_cli/services/documentation_run/contracts.py:243`
**Kind:** Class
**Bases:** `DocumentationRunError`
**Module:** [documentation_run_contracts](../modules/documentation_run_contracts.md)

## Description

Raised when a stage transition violates the lifecycle graph.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["DocumentationTransitionError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n1["DocumentationRunError (src/llm_wiki_cli/services/documentation_run/contracts.py)"]
    n2["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n3["export_documentation_run (src/llm_wiki_cli/services/documentation_run/export.py)"]
    n4["_assert_packet_stage (src/llm_wiki_cli/services/documentation_run/integrity.py)"]
    n5["build_documentation_agent_packet (src/llm_wiki_cli/services/documentation_run/packet.py)"]
    n6["_approve_review_ledger (src/llm_wiki_cli/services/documentation_run/record.py)"]
    n7["_verify_user_docs_gate (src/llm_wiki_cli/services/documentation_run/record.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/documentation_run_contracts.md"
    click n1 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run___init__.md"
    click n3 "../modules/export.md"
    click n4 "../modules/integrity.md"
    click n5 "../modules/packet.md"
    click n6 "../modules/record.md"
    click n7 "../modules/record.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [documentation_run_contracts](../modules/documentation_run_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `DocumentationRunError` | [documentation_run_contracts](../modules/documentation_run_contracts.md) |

### References

| Reference | Kind | Source |
|---|---|---|
| `__init__` | import | [documentation_run___init__](../modules/documentation_run___init__.md) |
| `export_documentation_run` | call | [export](../modules/export.md) |
| `_assert_packet_stage` | call | [integrity](../modules/integrity.md) |
| `_assert_packet_stage` | call | [integrity](../modules/integrity.md) |
| `build_documentation_agent_packet` | call | [packet](../modules/packet.md) |
| `_approve_review_ledger` | call | [record](../modules/record.md) |
| `_approve_review_ledger` | call | [record](../modules/record.md) |
| `_verify_user_docs_gate` | call | [record](../modules/record.md) |
| `_verify_user_docs_gate` | call | [record](../modules/record.md) |
| `_verify_user_docs_gate` | call | [record](../modules/record.md) |
| `_verify_user_docs_gate` | call | [record](../modules/record.md) |
| `_verify_user_docs_gate` | call | [record](../modules/record.md) |
