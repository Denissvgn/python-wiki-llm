# Lifecycle

**Location:** `src/llm_wiki_cli/services/knowledge_model.py:162`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_model](../modules/knowledge_model.md)

## Description

_Auto-generated from `Lifecycle` in `src/llm_wiki_cli/services/knowledge_model.py`._

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `UNKNOWN` | `'unknown'` | — |
| `DRAFT` | `'draft'` | — |
| `ACTIVE` | `'active'` | — |
| `DEPRECATED` | `'deprecated'` | — |
| `SUPERSEDED` | `'superseded'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["Lifecycle (src/llm_wiki_cli/services/knowledge_model.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/knowledge_cmd.py"]
    n4["src/llm_wiki_cli/services/context_packet.py"]
    n5["_lifecycle_event_digest_payload (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n6["_lifecycle_event_summary (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n7["_ordered_lifecycle_events (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n8["_parse_lifecycle_event (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n9["_validate_concept_summary (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n10["_validate_lifecycle_event_fields (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n11["_validate_lifecycle_histories (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n12["_validate_lifecycle_summary (src/llm_wiki_cli/services/knowledge_governance.py)"]
    n0 --> n1
    n0 --> n2
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
    click n0 "../modules/knowledge_model.md"
    click n3 "../modules/knowledge_cmd.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/knowledge_governance.md"
    click n6 "../modules/knowledge_governance.md"
    click n7 "../modules/knowledge_governance.md"
    click n8 "../modules/knowledge_governance.md"
    click n9 "../modules/knowledge_governance.md"
    click n10 "../modules/knowledge_governance.md"
    click n11 "../modules/knowledge_governance.md"
    click n12 "../modules/knowledge_governance.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_model](../modules/knowledge_model.md) | 0 | `ACTIVE`, `DEPRECATED`, `DRAFT`, `SUPERSEDED`, `UNKNOWN` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `knowledge_cmd` | import | [knowledge_cmd](../modules/knowledge_cmd.md) |
| `context_packet` | import | [context_packet](../modules/context_packet.md) |
| `_lifecycle_event_digest_payload` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_lifecycle_event_summary` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_ordered_lifecycle_events` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_parse_lifecycle_event` | call | [knowledge_governance](../modules/knowledge_governance.md) |
| `_parse_lifecycle_event` | call | [knowledge_governance](../modules/knowledge_governance.md) |
| `_parse_lifecycle_event` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_validate_concept_summary` | call | [knowledge_governance](../modules/knowledge_governance.md) |
| `_validate_lifecycle_event_fields` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_validate_lifecycle_histories` | type_reference | [knowledge_governance](../modules/knowledge_governance.md) |
| `_validate_lifecycle_summary` | call | [knowledge_governance](../modules/knowledge_governance.md) |
