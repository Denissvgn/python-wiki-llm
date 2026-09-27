# immutable Module

**Path:** `src/llm_wiki_cli/services/immutable.py`

## Description

Detached immutable model graphs that retain ordinary JSON container shapes.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `copy` | `deepcopy` |
| `dataclasses` | `fields`, `is_dataclass`, `replace` |
| `typing` | `TypeVar`, `cast` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/analysis_capture.py"]
    n1["src/llm_wiki_cli/services/context_session.py"]
    n2["src/llm_wiki_cli/services/immutable.py"]
    n3["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n4["src/llm_wiki_cli/services/knowledge_index.py"]
    n5["src/llm_wiki_cli/services/knowledge_model.py"]
    n6["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n7["src/llm_wiki_cli/services/manifest_storage.py"]
    n8["src/llm_wiki_cli/services/team.py"]
    n0 --> n2
    n1 --> n2
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n7
    n4 --> n2
    n4 --> n5
    n5 --> n2
    n6 --> n0
    n6 --> n2
    n6 --> n3
    n6 --> n5
    n7 --> n2
    n7 --> n3
    n8 --> n2
    click n0 "../modules/analysis_capture.md"
    click n1 "../modules/context_session.md"
    click n2 "../modules/immutable.md"
    click n3 "../modules/knowledge_artifacts.md"
    click n4 "../modules/knowledge_index.md"
    click n5 "../modules/knowledge_model.md"
    click n6 "../modules/knowledge_orchestration.md"
    click n7 "../modules/manifest_storage.md"
    click n8 "../modules/team.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [analysis_capture](../modules/analysis_capture.md) |
| Inbound | [context_session](../modules/context_session.md) |
| Inbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Inbound | [knowledge_index](../modules/knowledge_index.md) |
| Inbound | [knowledge_model](../modules/knowledge_model.md) |
| Inbound | [knowledge_orchestration](../modules/knowledge_orchestration.md) |
| Inbound | [manifest_storage](../modules/manifest_storage.md) |
| Inbound | [team](../modules/team.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [FrozenDict](../entities/FrozenDict.md) | 17 | `dict` | — |
| [FrozenList](../entities/FrozenList.md) | 28 | `list` | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_immutable` | `(*args, **kwargs)` | — | — |
| `freeze` | `(value: _T) -> _T` | — | Detach parsed, acyclic model data and freeze every mutable descendant. |
