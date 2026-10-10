# _IndexValidationProof

**Location:** `src/llm_wiki_cli/services/knowledge_index.py:349`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_index](../modules/knowledge_index.md)

**Decorators:** `@dataclass(frozen=True, init=False)`

## Description

_Auto-generated from `_IndexValidationProof` in `src/llm_wiki_cli/services/knowledge_index.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `model` | `KnowledgeIndex` | *required* | — |
| `content` | `bytes` | *required* | — |
| `operation` | `_IndexValidationOperation` | *required* | — |
| `validator_identity` | `tuple` | *required* | — |
| `_issuer` | `object` | `field(repr=False, compare=False)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(model, content, operation, *, issuer)` | — | — |
| `__deepcopy__` | `(memo)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_IndexValidationProof (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1["_validated_index_receipt (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1 --> n0
    click n0 "../modules/knowledge_index.md"
    click n1 "../modules/knowledge_index.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_index](../modules/knowledge_index.md) | 2 | `_issuer`, `content`, `model`, `operation`, `validator_identity` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_validated_index_receipt` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
