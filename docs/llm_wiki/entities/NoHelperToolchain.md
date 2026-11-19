# NoHelperToolchain

**Location:** `src/llm_wiki_cli/services/domain_pack.py:703`
**Kind:** Class
**Bases:** `HelperToolchain`
**Module:** [domain_pack](../modules/domain_pack.md)

## Description

Needs and prepares no helpers.

A pack using it should classify only sources that in-process extractors
handle; a source kind whose extractor needs a helper still fails without one.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `languages` | `(snapshot: SourceSnapshot, registry: Mapping[str, str], *, only_files: Iterable[str] \| None = None) -> tuple[str, ...]` | — | — |
| `prepare` | `(snapshot: SourceSnapshot, registry: Mapping[str, str], *, only_files: Iterable[str] \| None = None, cache_dir: str \| None = None) -> tuple[PreparedHelperHandle, ...]` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["NoHelperToolchain (src/llm_wiki_cli/services/domain_pack.py)"]
    n1["HelperToolchain (src/llm_wiki_cli/services/domain_pack.py)"]
    n2["src/llm_wiki_cli/engine/__init__.py"]
    n0 --> n1
    n2 --> n0
    click n0 "../modules/domain_pack.md"
    click n1 "../modules/domain_pack.md"
    click n2 "../modules/engine___init__.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [domain_pack](../modules/domain_pack.md) | 2 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `HelperToolchain` | [domain_pack](../modules/domain_pack.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `__init__` | import | [engine___init__](../modules/engine___init__.md) | — |
