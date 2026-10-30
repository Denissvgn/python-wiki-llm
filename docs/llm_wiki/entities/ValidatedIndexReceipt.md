# _ValidatedIndexReceipt

**Location:** `src/llm_wiki_cli/services/knowledge_index.py:391`
**Kind:** Class
**Bases:** —
**Module:** [knowledge_index](../modules/knowledge_index.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

_Auto-generated from `_ValidatedIndexReceipt` in `src/llm_wiki_cli/services/knowledge_index.py`._

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `model` | `KnowledgeIndex` | *required* | — |
| `content` | `bytes` | *required* | — |
| `wiki_root` | `Path` | *required* | — |
| `_proof` | `_IndexValidationProof \| None` | `field(default=None, init=False, repr=False, compare=False)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__deepcopy__` | `(memo)` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_ValidatedIndexReceipt (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n2["_validated_index_receipt (src/llm_wiki_cli/services/knowledge_index.py)"]
    n3["build_knowledge_index (src/llm_wiki_cli/services/knowledge_index.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/knowledge_index.md"
    click n1 "../modules/knowledge_artifacts.md"
    click n2 "../modules/knowledge_index.md"
    click n3 "../modules/knowledge_index.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [knowledge_index](../modules/knowledge_index.md) | 1 | `_proof`, `content`, `model`, `wiki_root` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_artifacts` | import | [knowledge_artifacts](../modules/knowledge_artifacts.md) | — |
| `_validated_index_receipt` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
| `_validated_index_receipt` | type_reference | [knowledge_index](../modules/knowledge_index.md) | — |
| `build_knowledge_index` | call | [knowledge_index](../modules/knowledge_index.md) | 1 |
