# ManifestPageSource

**Location:** `src/llm_wiki_cli/services/sync_manifest.py:149`
**Kind:** Class
**Bases:** —
**Module:** [sync_manifest](../modules/sync_manifest.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Last observed source coordinate for one module or entity page.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `scope` | `str` | *required* | — |
| `source_path` | `str` | *required* | — |
| `entity_name` | `str \| None` | `None` | — |
| `occurrence` | `int \| None` | `None` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `to_payload` | `() -> dict[str, object]` | — | — |
| `from_payload` | `(value: object, field_name: str) -> ManifestPageSource` | `@classmethod` | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["ManifestPageSource (src/llm_wiki_cli/services/sync_manifest.py)"]
    n1["src/llm_wiki_cli/services/knowledge_index.py"]
    n2["_lint_retired_entity_mappings (src/llm_wiki_cli/services/lint_service.py)"]
    n3["_check_duplicate_removal_custody (src/llm_wiki_cli/services/source_retirement.py)"]
    n4["discover_retired_entities (src/llm_wiki_cli/services/source_retirement.py)"]
    n5["entity_owner_present (src/llm_wiki_cli/services/source_retirement.py)"]
    n6["historical_entity_semantics (src/llm_wiki_cli/services/source_retirement.py)"]
    n7["read_entity_retirement_state (src/llm_wiki_cli/services/source_retirement.py)"]
    n8["retired_entity_mappings (src/llm_wiki_cli/services/source_retirement.py)"]
    n9["with_entity_retirement_state (src/llm_wiki_cli/services/source_retirement.py)"]
    n10["src/llm_wiki_cli/services/sync_analysis.py"]
    n11["plan_generated_source_repairs (src/llm_wiki_cli/services/sync_generated_sections.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    n10 --> n0
    n11 --> n0
    click n0 "../modules/sync_manifest.md"
    click n1 "../modules/knowledge_index.md"
    click n2 "../modules/lint_service.md"
    click n3 "../modules/source_retirement.md"
    click n4 "../modules/source_retirement.md"
    click n5 "../modules/source_retirement.md"
    click n6 "../modules/source_retirement.md"
    click n7 "../modules/source_retirement.md"
    click n8 "../modules/source_retirement.md"
    click n9 "../modules/source_retirement.md"
    click n10 "../modules/sync_analysis.md"
    click n11 "../modules/sync_generated_sections.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_manifest](../modules/sync_manifest.md) | 3 | `entity_name`, `occurrence`, `scope`, `source_path` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) | — |
| `_lint_retired_entity_mappings` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `_check_duplicate_removal_custody` | call | [source_retirement](../modules/source_retirement.md) | 1 |
| `discover_retired_entities` | call | [source_retirement](../modules/source_retirement.md) | 1 |
| `discover_retired_entities` | type_reference | [source_retirement](../modules/source_retirement.md) | — |
| `entity_owner_present` | type_reference | [source_retirement](../modules/source_retirement.md) | — |
| `historical_entity_semantics` | type_reference | [source_retirement](../modules/source_retirement.md) | — |
| `read_entity_retirement_state` | type_reference | [source_retirement](../modules/source_retirement.md) | — |
| `retired_entity_mappings` | type_reference | [source_retirement](../modules/source_retirement.md) | — |
| `with_entity_retirement_state` | type_reference | [source_retirement](../modules/source_retirement.md) | — |
| `sync_analysis` | import | [sync_analysis](../modules/sync_analysis.md) | — |
| `plan_generated_source_repairs` | type_reference | [sync_generated_sections](../modules/sync_generated_sections.md) | — |

> References: showing 12 of 26 logical references; 14 omitted by the 12-row generated summary limit.
