# KnowledgeEnvelopeError

**Location:** `src/llm_wiki_cli/services/knowledge_envelope.py:88`
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
    n7["_extensions_copy (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n8["_hash_structured (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n9["_normalized_allowlist (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n10["_normalized_markdown_bytes (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n11["_plugin_metadata_mapping (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n12["_reject_unknown_option_keys (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n13["_remote_mapping (src/llm_wiki_cli/services/knowledge_envelope.py)"]
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
    click n0 "../modules/knowledge_envelope.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/documentation_wiki_input.md"
    click n4 "../modules/knowledge_envelope.md"
    click n5 "../modules/knowledge_envelope.md"
    click n6 "../modules/knowledge_envelope.md"
    click n7 "../modules/knowledge_envelope.md"
    click n8 "../modules/knowledge_envelope.md"
    click n9 "../modules/knowledge_envelope.md"
    click n10 "../modules/knowledge_envelope.md"
    click n11 "../modules/knowledge_envelope.md"
    click n12 "../modules/knowledge_envelope.md"
    click n13 "../modules/knowledge_envelope.md"
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

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `context_packet` | import | [context_packet](../modules/context_packet.md) | — |
| `documentation_wiki_input` | import | [documentation_wiki_input](../modules/documentation_wiki_input.md) | — |
| `_build_component` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 5 |
| `_canonical_consumed_input_kind` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 4 |
| `_evaluated_revision` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 2 |
| `_extensions_copy` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 2 |
| `_hash_structured` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 1 |
| `_normalized_allowlist` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 4 |
| `_normalized_markdown_bytes` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 3 |
| `_plugin_metadata_mapping` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 2 |
| `_reject_unknown_option_keys` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 2 |
| `_remote_mapping` | call | [knowledge_envelope](../modules/knowledge_envelope.md) | 3 |

> References: showing 12 of 38 logical references; 26 omitted by the 12-row generated summary limit.
