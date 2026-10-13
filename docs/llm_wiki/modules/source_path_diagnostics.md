# source_path_diagnostics Module

**Path:** `src/llm_wiki_cli/services/source_path_diagnostics.py`

## Description

Separates supplied-path filesystem observations from captured discovery
eligibility. Source-selection exclusions prevent a metadata read; other
exclusions preserve the permitted no-follow filesystem observation. Recognized
Go test files excluded by the default language policy report
`go-tests-excluded` and `not-attempted`, rather than an unsupported extension.
Included source files without an attributable extraction outcome remain
unavailable until the query builder merges an extractor-owned result. Inventory
absence cannot establish a missing file, parser failure or completed extraction.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `EXCLUDED_DIRS`, `GitIgnoreMatcher`, `PathValidationError`, `is_agent_worktree_path` |
| `..extractors.common` | `is_bundled_helper_implementation_path`, `is_generated_javascript_bundle_path` |
| `.source_selection` | `path_is_selected` |
| `.source_snapshot` | `SourceSnapshot`, `_language_selection_for_path`, `_is_rescuable_typescript_src_lib_file` |
| `__future__` | `annotations` |
| `pathlib` | `Path` |
| `stat` | `stat` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/config.py"]
    n1["src/llm_wiki_cli/extractors/common.py"]
    n2["src/llm_wiki_cli/services/documentation_query_builder.py"]
    n3["src/llm_wiki_cli/services/source_path_diagnostics.py"]
    n4["src/llm_wiki_cli/services/source_selection.py"]
    n5["src/llm_wiki_cli/services/source_snapshot.py"]
    n1 --> n0
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n3 --> n0
    n3 --> n1
    n3 --> n4
    n3 --> n5
    n4 --> n0
    n5 --> n0
    n5 --> n1
    n5 --> n4
    click n0 "../modules/config.md"
    click n1 "../modules/common.md"
    click n2 "../modules/documentation_query_builder.md"
    click n3 "../modules/source_path_diagnostics.md"
    click n4 "../modules/source_selection.md"
    click n5 "../modules/source_snapshot.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_query_builder](../modules/documentation_query_builder.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [common](../modules/common.md) |
| Outbound | [source_selection](../modules/source_selection.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `source_path_diagnostics` | `(snapshot: SourceSnapshot, paths: tuple[str, ...]) -> dict[str, dict]` | — | Observe selected path metadata without following links or reading content. |