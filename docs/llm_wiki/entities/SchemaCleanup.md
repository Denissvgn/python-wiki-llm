# _SchemaCleanup

**Location:** `src/llm_wiki_cli/commands/uninstall_cmd.py:73`
**Kind:** Class
**Bases:** —
**Module:** [uninstall_cmd](../modules/uninstall_cmd.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

One verified managed-schema cleanup prepared before mutation.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `path` | `Path` | *required* | — |
| `content` | `str` | *required* | — |
| `content_bytes` | `bytes` | *required* | — |
| `stripped` | `str` | *required* | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_SchemaCleanup (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n1["_clean_agent_schemas (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n2["_preflight_agent_schemas (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n3["_validate_schema_plan (src/llm_wiki_cli/commands/uninstall_cmd.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    click n0 "../modules/uninstall_cmd.md"
    click n1 "../modules/uninstall_cmd.md"
    click n2 "../modules/uninstall_cmd.md"
    click n3 "../modules/uninstall_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [uninstall_cmd](../modules/uninstall_cmd.md) | 0 | `content`, `content_bytes`, `path`, `stripped` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_clean_agent_schemas` | type_reference | [uninstall_cmd](../modules/uninstall_cmd.md) | — |
| `_preflight_agent_schemas` | call | [uninstall_cmd](../modules/uninstall_cmd.md) | 1 |
| `_preflight_agent_schemas` | type_reference | [uninstall_cmd](../modules/uninstall_cmd.md) | — |
| `_validate_schema_plan` | type_reference | [uninstall_cmd](../modules/uninstall_cmd.md) | — |
