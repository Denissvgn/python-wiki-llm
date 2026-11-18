# ManifestPageSource

**Location:** `src/llm_wiki_engine/sync_manifest.py:152`
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
    n0["ManifestPageSource (src/llm_wiki_engine/sync_manifest.py)"]
    n1["_lint_retired_entity_mappings (src/llm_wiki_cli/services/lint_service.py)"]
    n2["src/llm_wiki_cli/services/publication_contracts.py"]
    n3["src/llm_wiki_cli/services/sync_analysis.py"]
    n4["plan_generated_source_repairs (src/llm_wiki_cli/services/sync_generated_sections.py)"]
    n5["_current_pages (src/llm_wiki_cli/services/sync_transitions.py)"]
    n6["_moved_entity_owner (src/llm_wiki_cli/services/sync_transitions.py)"]
    n7["_moved_module_owner (src/llm_wiki_cli/services/sync_transitions.py)"]
    n8["_Ownership.add (src/llm_wiki_cli/services/sync_transitions.py)"]
    n9["_Ownership.resolve (src/llm_wiki_cli/services/sync_transitions.py)"]
    n10["_prior_ownership (src/llm_wiki_cli/services/sync_transitions.py)"]
    n11["find_missing_source_pages (src/llm_wiki_cli/services/sync_transitions.py)"]
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
    click n1 "../modules/lint_service.md"
    click n2 "../modules/publication_contracts.md"
    click n3 "../modules/sync_analysis.md"
    click n4 "../modules/sync_generated_sections.md"
    click n5 "../modules/sync_transitions.md"
    click n6 "../modules/sync_transitions.md"
    click n7 "../modules/sync_transitions.md"
    click n8 "../modules/sync_transitions.md"
    click n9 "../modules/sync_transitions.md"
    click n10 "../modules/sync_transitions.md"
    click n11 "../modules/sync_transitions.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_manifest](../modules/sync_manifest.md) | 3 | `entity_name`, `occurrence`, `scope`, `source_path` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_lint_retired_entity_mappings` | type_reference | [lint_service](../modules/lint_service.md) | — |
| `publication_contracts` | import | [publication_contracts](../modules/publication_contracts.md) | — |
| `sync_analysis` | import | [sync_analysis](../modules/sync_analysis.md) | — |
| `plan_generated_source_repairs` | type_reference | [sync_generated_sections](../modules/sync_generated_sections.md) | — |
| `_current_pages` | call | [sync_transitions](../modules/sync_transitions.md) | 2 |
| `_current_pages` | type_reference | [sync_transitions](../modules/sync_transitions.md) | — |
| `_moved_entity_owner` | type_reference | [sync_transitions](../modules/sync_transitions.md) | — |
| `_moved_module_owner` | type_reference | [sync_transitions](../modules/sync_transitions.md) | — |
| `_Ownership.add` | type_reference | [sync_transitions](../modules/sync_transitions.md) | — |
| `_Ownership.resolve` | type_reference | [sync_transitions](../modules/sync_transitions.md) | — |
| `_prior_ownership` | call | [sync_transitions](../modules/sync_transitions.md) | 4 |
| `find_missing_source_pages` | type_reference | [sync_transitions](../modules/sync_transitions.md) | — |

> References: showing 12 of 30 logical references; 18 omitted by the 12-row generated summary limit.
