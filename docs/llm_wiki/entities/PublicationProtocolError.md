# PublicationProtocolError

**Location:** `src/llm_wiki_cli/services/publication_contracts.py:37`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [publication_contracts](../modules/publication_contracts.md)

## Description

An imported publication document violates its versioned contract.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["PublicationProtocolError (src/llm_wiki_cli/services/publication_contracts.py)"]
    n1["ValueError"]
    n2["_fail (src/llm_wiki_cli/services/publication_contracts.py)"]
    n3["_guard (src/llm_wiki_cli/services/publication_contracts.py)"]
    n4["_hash (src/llm_wiki_cli/services/publication_contracts.py)"]
    n5["_path (src/llm_wiki_cli/services/publication_contracts.py)"]
    n6["_invalid_constant (src/llm_wiki_cli/services/publication_impact.py)"]
    n7["_target_hash (src/llm_wiki_cli/services/publication_impact.py)"]
    n8["_topic_versions (src/llm_wiki_cli/services/publication_impact.py)"]
    n9["_unique_object (src/llm_wiki_cli/services/publication_impact.py)"]
    n10["capture_publication_basis (src/llm_wiki_cli/services/publication_impact.py)"]
    n11["compare_publication_impact (src/llm_wiki_cli/services/publication_impact.py)"]
    n12["read_publication_document (src/llm_wiki_cli/services/publication_impact.py)"]
    n13["resolve_publication_finding (src/llm_wiki_cli/services/publication_impact.py)"]
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
    click n0 "../modules/publication_contracts.md"
    click n2 "../modules/publication_contracts.md"
    click n3 "../modules/publication_contracts.md"
    click n4 "../modules/publication_contracts.md"
    click n5 "../modules/publication_contracts.md"
    click n6 "../modules/publication_impact.md"
    click n7 "../modules/publication_impact.md"
    click n8 "../modules/publication_impact.md"
    click n9 "../modules/publication_impact.md"
    click n10 "../modules/publication_impact.md"
    click n11 "../modules/publication_impact.md"
    click n12 "../modules/publication_impact.md"
    click n13 "../modules/publication_impact.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [publication_contracts](../modules/publication_contracts.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_fail` | call | [publication_contracts](../modules/publication_contracts.md) | 1 |
| `_guard` | call | [publication_contracts](../modules/publication_contracts.md) | 1 |
| `_hash` | call | [publication_contracts](../modules/publication_contracts.md) | 1 |
| `_path` | call | [publication_contracts](../modules/publication_contracts.md) | 1 |
| `_invalid_constant` | call | [publication_impact](../modules/publication_impact.md) | 1 |
| `_target_hash` | call | [publication_impact](../modules/publication_impact.md) | 1 |
| `_topic_versions` | call | [publication_impact](../modules/publication_impact.md) | 1 |
| `_unique_object` | call | [publication_impact](../modules/publication_impact.md) | 1 |
| `capture_publication_basis` | call | [publication_impact](../modules/publication_impact.md) | 5 |
| `compare_publication_impact` | call | [publication_impact](../modules/publication_impact.md) | 2 |
| `read_publication_document` | call | [publication_impact](../modules/publication_impact.md) | 2 |
| `resolve_publication_finding` | call | [publication_impact](../modules/publication_impact.md) | 6 |
