# KnowledgeGraphError

**Location:** `src/llm_wiki_cli/services/knowledge_graph.py:109`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_graph](../modules/knowledge_graph.md)

## Description

Field-specific typed-graph contract or materialization failure.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(field: str, message: str)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeGraphError (src/llm_wiki_cli/services/knowledge_graph.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/documentation_queries.py"]
    n3["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n4["src/llm_wiki_cli/services/knowledge_generation.py"]
    n5["_aggregate_flow_coverage (src/llm_wiki_cli/services/knowledge_graph.py)"]
    n6["_array (src/llm_wiki_cli/services/knowledge_graph.py)"]
    n7["_canonical_json (src/llm_wiki_cli/services/knowledge_graph.py)"]
    n8["_enum (src/llm_wiki_cli/services/knowledge_graph.py)"]
    n9["_external_uri (src/llm_wiki_cli/services/knowledge_graph.py)"]
    n10["_hash (src/llm_wiki_cli/services/knowledge_graph.py)"]
    n11["_json_value (src/llm_wiki_cli/services/knowledge_graph.py)"]
    n12["_limitation (src/llm_wiki_cli/services/knowledge_graph.py)"]
    n13["_limitations (src/llm_wiki_cli/services/knowledge_graph.py)"]
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
    click n0 "../modules/knowledge_graph.md"
    click n2 "../modules/documentation_queries.md"
    click n3 "../modules/knowledge_artifacts.md"
    click n4 "../modules/knowledge_generation.md"
    click n5 "../modules/knowledge_graph.md"
    click n6 "../modules/knowledge_graph.md"
    click n7 "../modules/knowledge_graph.md"
    click n8 "../modules/knowledge_graph.md"
    click n9 "../modules/knowledge_graph.md"
    click n10 "../modules/knowledge_graph.md"
    click n11 "../modules/knowledge_graph.md"
    click n12 "../modules/knowledge_graph.md"
    click n13 "../modules/knowledge_graph.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_graph](../modules/knowledge_graph.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `documentation_queries` | import | [documentation_queries](../modules/documentation_queries.md) | — |
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `knowledge_generation` | import | [knowledge_generation](../modules/knowledge_generation.md) | — |
| `_aggregate_flow_coverage` | call | [knowledge_graph](../modules/knowledge_graph.md) | 2 |
| `_array` | call | [knowledge_graph](../modules/knowledge_graph.md) | 1 |
| `_canonical_json` | call | [knowledge_graph](../modules/knowledge_graph.md) | 1 |
| `_enum` | call | [knowledge_graph](../modules/knowledge_graph.md) | 1 |
| `_external_uri` | call | [knowledge_graph](../modules/knowledge_graph.md) | 3 |
| `_hash` | call | [knowledge_graph](../modules/knowledge_graph.md) | 1 |
| `_json_value` | call | [knowledge_graph](../modules/knowledge_graph.md) | 5 |
| `_limitation` | call | [knowledge_graph](../modules/knowledge_graph.md) | 1 |
| `_limitations` | call | [knowledge_graph](../modules/knowledge_graph.md) | 1 |

> References: showing 12 of 43 logical references; 31 omitted by the 12-row generated summary limit.
