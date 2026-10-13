# _InvalidYaml

**Location:** `src/llm_wiki_cli/services/yaml_syntax.py:26`
**Kind:** Class
**Bases:** `ValueError`
**Module:** [yaml_syntax](../modules/yaml_syntax.md)

## Description

An unsupported or over-budget YAML observation.

## Attributes

*No annotated attributes found.*

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["_InvalidYaml (src/llm_wiki_cli/services/yaml_syntax.py)"]
    n1["ValueError"]
    n2["_check_events (src/llm_wiki_cli/services/yaml_syntax.py)"]
    n3["_convert_mapping (src/llm_wiki_cli/services/yaml_syntax.py)"]
    n4["_convert_node (src/llm_wiki_cli/services/yaml_syntax.py)"]
    n0 --> n1
    n2 --> n0
    n3 --> n0
    n4 --> n0
    click n0 "../modules/yaml_syntax.md"
    click n2 "../modules/yaml_syntax.md"
    click n3 "../modules/yaml_syntax.md"
    click n4 "../modules/yaml_syntax.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [yaml_syntax](../modules/yaml_syntax.md) | 0 | — |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `ValueError` | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_check_events` | call | [yaml_syntax](../modules/yaml_syntax.md) | 3 |
| `_convert_mapping` | call | [yaml_syntax](../modules/yaml_syntax.md) | 5 |
| `_convert_node` | call | [yaml_syntax](../modules/yaml_syntax.md) | 5 |
