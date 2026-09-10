# KnowledgeRequiredUnavailableError

**Location:** `src/llm_wiki_cli/services/context_service.py:191`
**Kind:** Class
**Bases:** `RuntimeError`
**Module:** [context_service](../modules/context_service.md)

## Description

Explicit required mode could not produce ready qualified knowledge.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(*, availability: str, reason: str, fallback_evidence: list[str], recovery_command: str) -> None` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["KnowledgeRequiredUnavailableError (src/llm_wiki_cli/services/context_service.py)"]
    n1["RuntimeError"]
    n2["_fit_knowledge_packet_response (src/llm_wiki_cli/services/context_packet.py)"]
    n3["_build_explicit_knowledge_response (src/llm_wiki_cli/services/context_service.py)"]
    n4["_fit_explicit_knowledge_response (src/llm_wiki_cli/services/context_service.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/context_service.md"
    click n2 "../modules/context_packet.md"
    click n3 "../modules/context_service.md"
    click n4 "../modules/context_service.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [context_service](../modules/context_service.md) | 1 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `RuntimeError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_fit_knowledge_packet_response` | call | [context_packet](../modules/context_packet.md) | 1 |
| `_build_explicit_knowledge_response` | call | [context_service](../modules/context_service.md) | 1 |
| `_fit_explicit_knowledge_response` | call | [context_service](../modules/context_service.md) | 1 |
