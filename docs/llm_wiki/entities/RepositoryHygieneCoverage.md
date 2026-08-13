# RepositoryHygieneCoverage

**Location:** `src/llm_wiki_cli/services/instruction_ownership.py:130`
**Kind:** Class
**Bases:** —
**Module:** [instruction_ownership](../modules/instruction_ownership.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Always-inline ownership reservation for repository safeguards.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `name` | `str` | *required* | — |
| `contract` | `str` | *required* | — |
| `owner` | `InstructionOwner` | `InstructionOwner.KERNEL` | — |
| `always_inline` | `bool` | `True` | — |
| `profiles` | `tuple[SchemaRenderProfile, ...]` | `tuple(SchemaRenderProfile)` | — |
| `agent_targets` | `tuple[str, ...]` | `tuple(SCHEMA_FILENAMES)` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
*No generated relationships detected.*

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [instruction_ownership](../modules/instruction_ownership.md) | 0 | `agent_targets`, `always_inline`, `contract`, `name`, `owner`, `profiles` |
