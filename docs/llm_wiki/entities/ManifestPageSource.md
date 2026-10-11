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
    n2["src/llm_wiki_cli/services/sync_analysis.py"]
    n3["plan_generated_source_repairs (src/llm_wiki_cli/services/sync_generated_sections.py)"]
    n4["_legacy_operational_state (src/llm_wiki_cli/services/sync_manifest.py)"]
    n5["_put_page_mapping (src/llm_wiki_cli/services/sync_manifest.py)"]
    n6["ManifestPageSource.from_payload (src/llm_wiki_cli/services/sync_manifest.py)"]
    n7["SyncManifest._validate_basis_mapping (src/llm_wiki_cli/services/sync_manifest.py)"]
    n8["SyncManifest.build_from_inventory (src/llm_wiki_cli/services/sync_manifest.py)"]
    n9["_current_pages (src/llm_wiki_cli/services/sync_transitions.py)"]
    n1 --> n0
    n2 --> n0
    n3 --> n0
    n4 --> n0
    n5 --> n0
    n6 --> n0
    n7 --> n0
    n8 --> n0
    n9 --> n0
    click n0 "../modules/sync_manifest.md"
    click n1 "../modules/knowledge_index.md"
    click n2 "../modules/sync_analysis.md"
    click n3 "../modules/sync_generated_sections.md"
    click n4 "../modules/sync_manifest.md"
    click n5 "../modules/sync_manifest.md"
    click n6 "../modules/sync_manifest.md"
    click n7 "../modules/sync_manifest.md"
    click n8 "../modules/sync_manifest.md"
    click n9 "../modules/sync_transitions.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [sync_manifest](../modules/sync_manifest.md) | 3 | `entity_name`, `occurrence`, `scope`, `source_path` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `knowledge_index` | import | [knowledge_index](../modules/knowledge_index.md) | — |
| `sync_analysis` | import | [sync_analysis](../modules/sync_analysis.md) | — |
| `plan_generated_source_repairs` | type_reference | [sync_generated_sections](../modules/sync_generated_sections.md) | — |
| `_legacy_operational_state` | call | [sync_manifest](../modules/sync_manifest.md) | 3 |
| `_legacy_operational_state` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |
| `_put_page_mapping` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |
| `ManifestPageSource.from_payload` | call | [sync_manifest](../modules/sync_manifest.md) | 1 |
| `ManifestPageSource.from_payload` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |
| `SyncManifest._validate_basis_mapping` | type_reference | [sync_manifest](../modules/sync_manifest.md) | — |
| `SyncManifest.build_from_inventory` | call | [sync_manifest](../modules/sync_manifest.md) | 2 |
| `_current_pages` | call | [sync_transitions](../modules/sync_transitions.md) | 2 |
| `_current_pages` | type_reference | [sync_transitions](../modules/sync_transitions.md) | — |

> References: showing 12 of 17 logical references; 5 omitted by the 12-row generated summary limit.
