# Resolution

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:133`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

_Auto-generated from `Resolution` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `RESOLVED` | `'resolved'` | — |
| `AMBIGUOUS` | `'ambiguous'` | — |
| `EXTERNAL` | `'external'` | — |
| `UNRESOLVED` | `'unresolved'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["Resolution (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/context_packet.py"]
    n4["src/llm_wiki_cli/services/knowledge_index.py"]
    n5["src/llm_wiki_cli/services/knowledge_links.py"]
    n6["src/llm_wiki_cli/services/verification_contracts.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/context_packet.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_links.md"
    click n6 "../modules/verification_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `AMBIGUOUS`, `EXTERNAL`, `RESOLVED`, `UNRESOLVED` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `context_packet` | import | [context_packet](../modules/context_packet.md) |
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) |
| `knowledge_links` | import | [knowledge_links](../modules/knowledge_links.md) |
| `verification_contracts` | import | [verification_contracts](../modules/verification_contracts.md) |
