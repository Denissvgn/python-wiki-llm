# KnowledgeEnvelopeError

**Location:** `src/llm_wiki_cli/services/knowledge_envelope.py:86`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [knowledge_envelope](../modules/knowledge_envelope.md)

## Description

Field-specific validation failure while constructing an envelope.

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
    n0["KnowledgeEnvelopeError (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n1["ValueError"]
    n2["src/llm_wiki_cli/services/context_packet.py"]
    n3["src/llm_wiki_cli/services/documentation_wiki_input.py"]
    n4["_build_component (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n5["_canonical_consumed_input_kind (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n6["_evaluated_revision (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/knowledge_envelope.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/documentation_wiki_input.md"
    click n4 "../modules/knowledge_envelope.md"
    click n5 "../modules/knowledge_envelope.md"
    click n6 "../modules/knowledge_envelope.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_envelope](../modules/knowledge_envelope.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `context_packet` | import | [context_packet](../modules/context_packet.md) |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) |
| `_build_component` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_build_component` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_build_component` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_build_component` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_build_component` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_canonical_consumed_input_kind` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_canonical_consumed_input_kind` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_canonical_consumed_input_kind` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_canonical_consumed_input_kind` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_evaluated_revision` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
