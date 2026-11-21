# token_counting Module

**Path:** `src/llm_wiki_cli/services/token_counting.py`

## Description

Provides the host counter contract, a labelled UTF-8 size estimate, and an exact
counter loaded from explicit local tokenizer JSON. Exact counting disables saved
padding and truncation, excludes special-token chat framing, and identifies the
tokenizer bytes by their hash. Loading stays local and does not discover or run
repository-provided counter code.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `hashlib` | `hashlib` |
| `llm_wiki_engine.token_counters` | `EstimatedCounter`, `TokenCounter` |
| `pathlib` | `Path` |
| `sys` | `sys` |
| `tokenizers` | `Tokenizer`, `tokenizers` |
| `typing` | `TYPE_CHECKING` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/api.py"]
    n1["src/llm_wiki_cli/commands/task_cmd.py"]
    n2["src/llm_wiki_cli/services/context_budget.py"]
    n3["src/llm_wiki_cli/services/mcp_server.py"]
    n4["src/llm_wiki_cli/services/token_counting.py"]
    n5["src/llm_wiki_engine/token_counters.py"]
    n0 --> n2
    n0 --> n4
    n1 --> n0
    n1 --> n4
    n2 --> n4
    n3 --> n0
    n3 --> n2
    n3 --> n4
    n4 --> n5
    click n0 "../modules/api.md"
    click n1 "../modules/task_cmd.md"
    click n2 "../modules/context_budget.md"
    click n3 "../modules/mcp_server.md"
    click n4 "../modules/token_counting.md"
    click n5 "../modules/token_counters.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [api](../modules/api.md) |
| Inbound | [task_cmd](../modules/task_cmd.md) |
| Inbound | [context_budget](../modules/context_budget.md) |
| Inbound | [mcp_server](../modules/mcp_server.md) |
| Outbound | [token_counters](../modules/token_counters.md) |

### External packages

| Language | Used packages | Undeclared packages |
|---|---:|---:|
| python | 1 | 0 |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [LocalTokenizerCounter](../entities/LocalTokenizerCounter.md) | 21 | — | Count raw text using immutable local tokenizer JSON, without framing. |
