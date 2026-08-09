# ConsumedInputKind

**Location:** `src/llm_wiki_cli/services/knowledge_envelope.py:97`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [knowledge_envelope](../modules/knowledge_envelope.md)

## Description

Known classes of repository/configuration input consumed by a run.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `SOURCE` | `'source'` | — |
| `DOCKER` | `'docker'` | — |
| `COMPOSE` | `'compose'` | — |
| `YAML` | `'yaml'` | — |
| `PACKAGE` | `'package'` | — |
| `OPENAPI` | `'openapi'` | — |
| `PLUGIN` | `'plugin'` | — |
| `SELECTION` | `'selection'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ConsumedInputKind (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/services/documentation_native.py"]
    n4["_canonical_consumed_input_kind (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n5["consumed_inputs_from_captured_hashes (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n6["ConsumedInput.from_bytes (src/llm_wiki_cli/services/knowledge_envelope.py)"]
    n7["_merge_explicit_consumed_input (src/llm_wiki_cli/services/knowledge_orchestration.py)"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    click n0 "../modules/knowledge_envelope.md"
    click n3 "../modules/documentation_native.md"
    click n4 "../modules/knowledge_envelope.md"
    click n5 "../modules/knowledge_envelope.md"
    click n6 "../modules/knowledge_envelope.md"
    click n7 "../modules/knowledge_orchestration.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_envelope](../modules/knowledge_envelope.md) | 0 | `COMPOSE`, `DOCKER`, `OPENAPI`, `PACKAGE`, `PLUGIN`, `SELECTION`, `SOURCE`, `YAML` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `documentation_native` | import | [documentation_native](../modules/documentation_native.md) |
| `_canonical_consumed_input_kind` | call | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_canonical_consumed_input_kind` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `consumed_inputs_from_captured_hashes` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `ConsumedInput.from_bytes` | type_reference | [knowledge_envelope](../modules/knowledge_envelope.md) |
| `_merge_explicit_consumed_input` | type_reference | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
