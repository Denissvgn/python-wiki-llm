# SourceSelectionPolicy

**Location:** `src/llm_wiki_cli/services/source_selection.py:181`
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
    n0["SourceSelectionPolicy (src/llm_wiki_cli/services/source_selection.py)"]
    n1["_apply_diff (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n2["_build_apply_diff_context (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n3["src/llm_wiki_cli/services/documentation_policy.py"]
    n4["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n5["_build_extract_source_snapshot (src/llm_wiki_cli/services/extraction_service.py)"]
    n6["_diff_block_is_selected (src/llm_wiki_cli/services/extraction_service.py)"]
    n7["filter_source_diff (src/llm_wiki_cli/services/extraction_service.py)"]
    n8["_source_selection_pin (src/llm_wiki_cli/services/mcp_server.py)"]
    n9["_policy_from_content (src/llm_wiki_cli/services/source_selection.py)"]
    n10["_validate_policy_filesystem (src/llm_wiki_cli/services/source_selection.py)"]
    n11["canonical_selection_payload (src/llm_wiki_cli/services/source_selection.py)"]
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
    click n0 "../modules/source_selection.md"
    click n1 "../modules/sync_cmd.md"
    click n2 "../modules/sync_cmd.md"
    click n3 "../modules/documentation_policy.md"
    click n4 "../modules/documentation_run_dependencies.md"
    click n5 "../modules/extraction_service.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/extraction_service.md"
    click n8 "../modules/mcp_server.md"
    click n9 "../modules/source_selection.md"
    click n10 "../modules/source_selection.md"
    click n11 "../modules/source_selection.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_selection](../modules/source_selection.md) | 3 | `exclude`, `include`, `origin`, `path`, `raw_content_hash`, `schema_version`, `source_root` |

### References

| Reference | Kind | Source |
|---|---|---|
| `_apply_diff` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `_build_apply_diff_context` | type_reference | [sync_cmd](../modules/sync_cmd.md) |
| `documentation_policy` | import | [documentation_policy](../modules/documentation_policy.md) |
| `dependencies` | import | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) |
| `_build_extract_source_snapshot` | type_reference | [extraction_service](../modules/extraction_service.md) |
| `_diff_block_is_selected` | type_reference | [extraction_service](../modules/extraction_service.md) |
| `filter_source_diff` | type_reference | [extraction_service](../modules/extraction_service.md) |
| `_source_selection_pin` | type_reference | [mcp_server](../modules/mcp_server.md) |
| `_policy_from_content` | call | [source_selection](../modules/source_selection.md) |
| `_policy_from_content` | type_reference | [source_selection](../modules/source_selection.md) |
| `_validate_policy_filesystem` | type_reference | [source_selection](../modules/source_selection.md) |
| `canonical_selection_payload` | type_reference | [source_selection](../modules/source_selection.md) |
