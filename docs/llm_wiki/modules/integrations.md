# integrations Module

**Path:** `src/llm_wiki_engine/integrations.py`

## Description

Providers the knowledge core borrows from the application that embeds it.

The knowledge core stores, validates and maintains knowledge without knowing
how sources are analyzed. A few of its checks need that knowledge: concept
implementation evidence comes from a language analysis, source snapshots come
from the application's view of the source tree, and some operations accept
only objects the application issued. The application names a module for each
capability below; the engine imports it on first use and reads its attributes
at call time, so a replaced attribute takes effect immediately.

A capability nobody provided fails closed with :class:`IntegrationUnavailable`.

## Imports

| Source | Symbols |
|--------|---------|
| `__future__` | `annotations` |
| `collections.abc` | `Mapping` |
| `importlib` | `importlib` |
| `re` | `re` |
| `types` | `MappingProxyType`, `ModuleType` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_engine/integrations.py"]
    n0 --> n1
    click n1 "../modules/integrations.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (14) |

> All 14 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [IntegrationUnavailable](../entities/IntegrationUnavailable.md) | 52 | `LookupError` | The application did not provide a capability the knowledge core needs. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `provide` | `(modules: Mapping[str, str]) -> None` | — | Name the provider module of each capability; a capability is provided once. |
| `provider` | `(capability: str) -> ModuleType` | — | Return the module providing *capability*, importing it on first use. |
| `attributes` | `(capability: str, *names: str) -> tuple` | — | Read *names* from the provider of *capability* now, as a lazy import would. |
| `provided` | `() -> Mapping[str, str]` | — | The provider module named for each capability so far. |
