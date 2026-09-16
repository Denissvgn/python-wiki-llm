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
    n0["src/llm_wiki_cli/services/context_session.py"]
    n1["src/llm_wiki_cli/services/immutable.py"]
    n2["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n3["src/llm_wiki_cli/services/knowledge_index.py"]
    n4["src/llm_wiki_cli/services/knowledge_model.py"]
    n5["src/llm_wiki_cli/services/knowledge_orchestration.py"]
    n6["src/llm_wiki_cli/services/manifest_storage.py"]
    n7["src/llm_wiki_cli/services/team.py"]
    n0 --> n1
    n2 --> n1
    n2 --> n3
    n2 --> n4
    n2 --> n6
    n3 --> n1
    n3 --> n4
    n4 --> n1
    n5 --> n1
    n5 --> n2
    n5 --> n4
    n6 --> n1
    n6 --> n2
    n7 --> n1
    click n0 "../modules/context_session.md"
    click n1 "../modules/immutable.md"
    click n2 "../modules/knowledge_artifacts.md"
    click n3 "../modules/knowledge_index.md"
    click n4 "../modules/knowledge_model.md"
    click n5 "../modules/knowledge_orchestration.md"
    click n6 "../modules/manifest_storage.md"
    click n7 "../modules/team.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
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
