# _LanguagePlugin

**Location:** `src/llm_wiki_cli/services/dependencies.py:793`
**Kind:** Class
**Bases:** —
**Module:** [services_dependencies](../modules/services_dependencies.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

A manifest parser + import classifier for one language family.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `key` | `str` | *required* | — |
| `languages` | `tuple[str, ...]` | *required* | — |
| `parse` | `Callable[[Path, SourceSnapshot], 'Optional[_Manifest]']` | *required* | — |
| `classify` | `Callable[[str, str, str, 'Optional[_Manifest]'], 'Optional[str]']` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
*No generated relationships detected.*

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [services_dependencies](../modules/services_dependencies.md) | 0 | `classify`, `key`, `languages`, `parse` |
