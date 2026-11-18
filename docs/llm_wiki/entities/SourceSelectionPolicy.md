# SourceSelectionPolicy

**Location:** `src/llm_wiki_engine/source_selection.py:181`
**Kind:** Class
**Bases:** —
**Module:** [source_selection](../modules/source_selection.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Validated, immutable source-selection policy bound to one repository.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `schema_version` | `str` | *required* | — |
| `include` | `tuple[str, ...]` | *required* | — |
| `exclude` | `tuple[str, ...]` | *required* | — |
| `source_root` | `Path` | *required* | — |
| `path` | `str` | *required* | — |
| `origin` | `str` | *required* | — |
| `raw_content_hash` | `str` | *required* | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__post_init__` | `() -> None` | — | — |
| `fingerprint` | `() -> str` | `@property` | Return the canonical semantic policy fingerprint. |
| `identity` | `() -> dict[str, str]` | `@property` | Return the canonical persisted selection identity. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SourceSelectionPolicy (src/llm_wiki_engine/source_selection.py)"]
    n1["src/llm_wiki_cli/services/documentation_policy.py"]
    n2["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n3["_build_extract_source_snapshot (src/llm_wiki_cli/services/extraction_service.py)"]
    n4["_diff_block_is_selected (src/llm_wiki_cli/services/extraction_service.py)"]
    n5["filter_source_diff (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["_source_selection_pin (src/llm_wiki_cli/services/mcp_server.py)"]
    n7["McpWikiService._assert_source_selection_pin_current (src/llm_wiki_cli/services/mcp_server.py)"]
    n8["_captured_snapshot_candidates (src/llm_wiki_cli/services/source_snapshot.py)"]
    n9["_captured_snapshot_inputs (src/llm_wiki_cli/services/source_snapshot.py)"]
    n10["_empty_source_snapshot (src/llm_wiki_cli/services/source_snapshot.py)"]
    n11["_hash_extra_inventory_path (src/llm_wiki_cli/services/source_snapshot.py)"]
    n12["_new_snapshot_buckets (src/llm_wiki_cli/services/source_snapshot.py)"]
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
    n12 --> n0
    click n0 "../modules/source_selection.md"
    click n1 "../modules/documentation_policy.md"
    click n2 "../modules/documentation_run_dependencies.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/extraction_service.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/mcp_server.md"
    click n7 "../modules/mcp_server.md"
    click n8 "../modules/source_snapshot.md"
    click n9 "../modules/source_snapshot.md"
    click n10 "../modules/source_snapshot.md"
    click n11 "../modules/source_snapshot.md"
    click n12 "../modules/source_snapshot.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_selection](../modules/source_selection.md) | 3 | `exclude`, `include`, `origin`, `path`, `raw_content_hash`, `schema_version`, `source_root` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `documentation_policy` | import | [documentation_policy](../modules/documentation_policy.md) | — |
| `dependencies` | import | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) | — |
| `_build_extract_source_snapshot` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_diff_block_is_selected` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `filter_source_diff` | type_reference | [extraction_service](../modules/extraction_service.md) | — |
| `_source_selection_pin` | type_reference | [mcp_server](../modules/mcp_server.md) | — |
| `McpWikiService._assert_source_selection_pin_current` | type_reference | [mcp_server](../modules/mcp_server.md) | — |
| `_captured_snapshot_candidates` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |
| `_captured_snapshot_inputs` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |
| `_empty_source_snapshot` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |
| `_hash_extra_inventory_path` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |
| `_new_snapshot_buckets` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |

> References: showing 12 of 28 logical references; 16 omitted by the 12-row generated summary limit.
