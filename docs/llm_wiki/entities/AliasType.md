# AliasType

**Location:** `src/llm_wiki_cli/services/concept_identity.py:85`
**Kind:** Enum
**Bases:** `str`, `Enum`
**Module:** [concept_identity](../modules/concept_identity.md)

## Description

The two coordinate namespaces that may retain historical aliases.

## Attributes

| Name | Declared value | Description |
|------|-------|-------------|
| `LOCATOR` | `'locator'` | — |
| `NATURAL_KEY` | `'natural-key'` | — |

## Methods

*No public methods. Inherits from base classes.*

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["AliasType (src/llm_wiki_cli/services/concept_identity.py)"]
    n1["Enum"]
    n2["str"]
    n3["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n4["add_identity_alias (src/llm_wiki_cli/services/concept_identity.py)"]
    n5["identity_coordinate_key (src/llm_wiki_cli/services/concept_identity.py)"]
    n6["validate_alias_type (src/llm_wiki_cli/services/concept_identity.py)"]
    n7["validate_alias_value (src/llm_wiki_cli/services/concept_identity.py)"]
    n8["src/llm_wiki_cli/services/knowledge_governance.py"]
    n0 --> n1
    n0 --> n2
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    click n0 "../modules/concept_identity.md"
    click n3 "../modules/migrate_cmd.md"
    click n4 "../modules/concept_identity.md"
    click n5 "../modules/concept_identity.md"
    click n6 "../modules/concept_identity.md"
    click n7 "../modules/concept_identity.md"
    click n8 "../modules/knowledge_governance.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [concept_identity](../modules/concept_identity.md) | 0 | `LOCATOR`, `NATURAL_KEY` |

### Structure

| Kind | Entity | Module |
|---|---|---|
| Base | `Enum` | — |
| Base | `str` | — |

### References

| Reference | Kind | Source |
|---|---|---|
| `migrate_cmd` | import | [migrate_cmd](../modules/migrate_cmd.md) |
| `add_identity_alias` | type_reference | [concept_identity](../modules/concept_identity.md) |
| `identity_coordinate_key` | type_reference | [concept_identity](../modules/concept_identity.md) |
| `validate_alias_type` | call | [concept_identity](../modules/concept_identity.md) |
| `validate_alias_type` | type_reference | [concept_identity](../modules/concept_identity.md) |
| `validate_alias_value` | type_reference | [concept_identity](../modules/concept_identity.md) |
| `knowledge_governance` | import | [knowledge_governance](../modules/knowledge_governance.md) |
