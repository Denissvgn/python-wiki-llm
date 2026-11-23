# HostCapabilityError

**Location:** `src/llm_wiki_engine/host.py:52`
**Kind:** Class
**Bases:** `PermissionError`
**Module:** [host](../modules/host.md)

## Description

The active host does not grant this capability.

It is an ``OSError``, so callers that already treat an unavailable
executable as a soft failure degrade the same way.

## Attributes

*No annotated attributes found.*

## Methods

*No declared methods.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HostCapabilityError (src/llm_wiki_engine/host.py)"]
    n1["PermissionError"]
    n2["src/llm_wiki_cli/engine/__init__.py"]
    n3["src/llm_wiki_cli/extractors/go_extractor.py"]
    n4["src/llm_wiki_cli/extractors/haskell_extractor.py"]
    n5["src/llm_wiki_cli/extractors/rust_extractor.py"]
    n6["src/llm_wiki_cli/extractors/ts_extractor.py"]
    n7["src/llm_wiki_cli/services/extraction_service.py"]
    n8["src/llm_wiki_cli/services/extractor_helpers.py"]
    n9["NoProcessHost.popen (src/llm_wiki_engine/host.py)"]
    n10["NoProcessHost.run (src/llm_wiki_engine/host.py)"]
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
    click n0 "../modules/host.md"
    click n2 "../modules/engine___init__.md"
    click n3 "../modules/go_extractor.md"
    click n4 "../modules/haskell_extractor.md"
    click n5 "../modules/rust_extractor.md"
    click n6 "../modules/ts_extractor.md"
    click n7 "../modules/extraction_service.md"
    click n8 "../modules/extractor_helpers.md"
    click n9 "../modules/host.md"
    click n10 "../modules/host.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [host](../modules/host.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `PermissionError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
| `go_extractor` | import | [go_extractor](../modules/go_extractor.md) | — |
| `haskell_extractor` | import | [haskell_extractor](../modules/haskell_extractor.md) | — |
| `rust_extractor` | import | [rust_extractor](../modules/rust_extractor.md) | — |
| `ts_extractor` | import | [ts_extractor](../modules/ts_extractor.md) | — |
| `extraction_service` | import | [extraction_service](../modules/extraction_service.md) | — |
| `extractor_helpers` | import | [extractor_helpers](../modules/extractor_helpers.md) | — |
| `NoProcessHost.popen` | call | [host](../modules/host.md) | 1 |
| `NoProcessHost.run` | call | [host](../modules/host.md) | 1 |
