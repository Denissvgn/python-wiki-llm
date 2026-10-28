# ContextKnowledgeContractError

**Location:** `src/llm_wiki_cli/services/context_knowledge_contract.py:1393`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [context_knowledge_contract](../modules/context_knowledge_contract.md)

## Description

A serialized context-knowledge contract violates the frozen shape.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ContextKnowledgeContractError (src/llm_wiki_cli/services/context_knowledge_contract.py)"]
    n1["ValueError"]
    n2["_contract_snapshot (src/llm_wiki_cli/services/context_knowledge_contract.py)"]
    n3["_matrix_by_state (src/llm_wiki_cli/services/context_knowledge_contract.py)"]
    n4["_validate_context_knowledge_contract (src/llm_wiki_cli/services/context_knowledge_contract.py)"]
    n5["validate_context_knowledge_contract (src/llm_wiki_cli/services/context_knowledge_contract.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    click n0 "../modules/context_knowledge_contract.md"
    click n2 "../modules/context_knowledge_contract.md"
    click n3 "../modules/context_knowledge_contract.md"
    click n4 "../modules/context_knowledge_contract.md"
    click n5 "../modules/context_knowledge_contract.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_knowledge_contract](../modules/context_knowledge_contract.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_contract_snapshot` | call | [context_knowledge_contract](../modules/context_knowledge_contract.md) | 1 |
| `_matrix_by_state` | call | [context_knowledge_contract](../modules/context_knowledge_contract.md) | 6 |
| `_validate_context_knowledge_contract` | call | [context_knowledge_contract](../modules/context_knowledge_contract.md) | 58 |
| `validate_context_knowledge_contract` | call | [context_knowledge_contract](../modules/context_knowledge_contract.md) | 1 |
