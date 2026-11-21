# HelperToolchain

**Location:** `src/llm_wiki_engine/pack_interfaces.py:280`
**Kind:** Class
**Bases:** —
**Module:** [pack_interfaces](../modules/pack_interfaces.md)

## Description

Which analysis helpers a source tree needs, and how they are prepared.

:meth:`languages` lists the source kinds whose extraction needs a
prepared helper. :meth:`prepare` runs before extraction inside a helper
operation: it resolves each needed helper under the operation's policy
(``"never"`` only reuses prepared artifacts, ``"auto"`` may build them),
binds what it found to the operation and returns those handles.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `languages` | `(snapshot: Any, registry: Mapping[str, str], *, only_files: Iterable[str] \| None = None) -> tuple[str, ...]` | — | — |
| `prepare` | `(snapshot: Any, registry: Mapping[str, str], *, only_files: Iterable[str] \| None = None, cache_dir: str \| None = None) -> tuple[Any, ...]` | — | — |
| `__repr__` | `() -> str` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["HelperToolchain (src/llm_wiki_engine/pack_interfaces.py)"]
    n1["BundledHelperToolchain (src/llm_wiki_cli/services/domain_pack.py)"]
    n2["NoHelperToolchain (src/llm_wiki_engine/pack_interfaces.py)"]
    n3["src/llm_wiki_cli/services/domain_pack.py"]
    n4["DomainPack.with_helper_toolchain (src/llm_wiki_engine/pack_interfaces.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/pack_interfaces.md"
    click n1 "../modules/domain_pack.md"
    click n2 "../modules/pack_interfaces.md"
    click n3 "../modules/domain_pack.md"
    click n4 "../modules/pack_interfaces.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [pack_interfaces](../modules/pack_interfaces.md) | 3 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Subclass | `BundledHelperToolchain` | [domain_pack](../modules/domain_pack.md) |
| Subclass | `NoHelperToolchain` | [pack_interfaces](../modules/pack_interfaces.md) |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `domain_pack` | import | [domain_pack](../modules/domain_pack.md) | — |
| `DomainPack.with_helper_toolchain` | type_reference | [pack_interfaces](../modules/pack_interfaces.md) | — |
