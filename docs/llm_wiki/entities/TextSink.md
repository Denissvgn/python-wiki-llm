# TextSink

**Location:** `src/llm_wiki_engine/host.py:43`
**Kind:** Class
**Bases:** `Protocol`
**Module:** [host](../modules/host.md)

## Description

A writable text stream, such as ``sys.stdout`` or ``io.StringIO``.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `write` | `(text: str, /) -> object` | — | — |
| `flush` | `() -> object` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["TextSink (src/llm_wiki_engine/host.py)"]
    n1["Protocol"]
    n2["Host.__init__ (src/llm_wiki_engine/host.py)"]
    n3["Host.stderr (src/llm_wiki_engine/host.py)"]
    n4["Host.stdout (src/llm_wiki_engine/host.py)"]
    n5["Host.with_output (src/llm_wiki_engine/host.py)"]
    n6["MessageStream._target (src/llm_wiki_engine/host.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    click n0 "../modules/host.md"
    click n2 "../modules/host.md"
    click n3 "../modules/host.md"
    click n4 "../modules/host.md"
    click n5 "../modules/host.md"
    click n6 "../modules/host.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [host](../modules/host.md) | 2 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Protocol` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `Host.__init__` | type_reference | [host](../modules/host.md) | — |
| `Host.stderr` | type_reference | [host](../modules/host.md) | — |
| `Host.stdout` | type_reference | [host](../modules/host.md) | — |
| `Host.with_output` | type_reference | [host](../modules/host.md) | — |
| `MessageStream._target` | type_reference | [host](../modules/host.md) | — |
