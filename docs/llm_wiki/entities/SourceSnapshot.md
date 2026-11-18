# SourceSnapshot

**Location:** `src/llm_wiki_cli/services/source_snapshot.py:135`
**Kind:** Class
**Bases:** —
**Module:** [source_snapshot](../modules/source_snapshot.md)

**Decorators:** `@dataclass(frozen=True)`

## Description

Filtered source-tree discovery results shared by lint/extract paths.

## Attributes

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `root` | `Path` | *required* | — |
| `files_by_language` | `dict[str, tuple[SourceFile, ...]]` | *required* | — |
| `dockerfile_candidates` | `tuple[SourceFile, ...]` | *required* | — |
| `compose_candidates` | `tuple[SourceFile, ...]` | *required* | — |
| `yaml_candidates` | `tuple[SourceFile, ...]` | *required* | — |
| `package_markers` | `tuple[SourceFile, ...]` | *required* | — |
| `unsupported_files_by_language` | `dict[str, tuple[SourceFile, ...]]` | *required* | — |
| `all_source_paths` | `tuple[str, ...]` | *required* | — |
| `gitignore_fingerprint` | `str` | *required* | — |
| `captured_content_hashes` | `dict[str, str]` | *required* | — |
| `captured_input_kinds` | `dict[str, tuple[str, ...]]` | *required* | — |
| `source_selection_policy` | `SourceSelectionPolicy \| None` | `None` | — |
| `selected_regular_paths` | `frozenset[str]` | `frozenset()` | — |
| `gitignore_rules` | `tuple[_GitignoreRule, ...]` | `()` | — |
| `include_tests` | `frozenset[str]` | `frozenset()` | — |
| `only_files` | `frozenset[str] \| None` | `None` | — |
| `captured_file_integrity` | `dict[str, SourceFileIntegrity]` | `field(default_factory=dict)` | — |
| `captured_gitignore_paths` | `frozenset[str]` | `frozenset()` | — |
| `respect_ignores` | `bool` | `False` | — |
| `respect_discovery` | `bool` | `False` | — |
| `capture_byte_limit` | `int \| None` | `None` | — |
| `capture_scan_limit` | `int \| None` | `None` | — |
| `coherent` | `bool` | `False` | — |
| `directory_integrity` | `dict[str, tuple[int, ...]]` | `field(default_factory=dict)` | — |

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `source_selection_path` | `() -> str \| None` | `@property` | Return the repository-relative policy path, when configured. |
| `source_selection_origin` | `() -> str \| None` | `@property` | Return whether selection was discovered by default or explicitly. |
| `source_selection_fingerprint` | `() -> str \| None` | `@property` | Return the semantic policy fingerprint, when configured. |
| `source_selection_identity` | `() -> dict[str, str] \| None` | `@property` | Return the canonical persisted policy identity, when configured. |
| `source_selection_inputs` | `() -> dict[str, object] \| None` | `@property` | Return exact configured profile/gitignore content commitments. |
| `path_is_effectively_selected` | `(path: str) -> bool` | — | Evaluate configured selection rules for an existing or missing path. |
| `path_may_contain_effective_selection` | `(path: str) -> bool` | — | Return whether a directory remains reachable by the live rules. |
| `language_paths` | `(language: str) -> list[str]` | — | Return deterministic relative paths for a language. |
| `unsupported_language_paths` | `(language: str) -> list[str]` | — | Return deterministic unsupported relative paths for a language. |
| `hashes_for` | `(paths: Iterable[str] \| None = None) -> dict[str, str]` | — | Return a validated copy of captured exact hashes without file I/O. |
| `to_consumed_inputs` | `(paths: Iterable[str] \| None = None) -> tuple[ConsumedInput, ...]` | — | Return canonical consumed inputs from already captured hashes. |
| `with_captured_inventory_paths` | `(paths: Iterable[str]) -> SourceSnapshot` | — | Commit extractor-returned paths absent from built-in discovery. |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["SourceSnapshot (src/llm_wiki_cli/services/source_snapshot.py)"]
    n1["_build_prompt (src/llm_wiki_cli/commands/generate_prompt_cmd.py)"]
    n2["_resolved_prompt_selection_and_diff (src/llm_wiki_cli/commands/generate_prompt_cmd.py)"]
    n3["_selected_prompt_diff (src/llm_wiki_cli/commands/generate_prompt_cmd.py)"]
    n4["_validated_prompt_selection_and_diff (src/llm_wiki_cli/commands/generate_prompt_cmd.py)"]
    n5["_validated_prompt_snapshot (src/llm_wiki_cli/commands/generate_prompt_cmd.py)"]
    n6["_preflight_team_source_selection (src/llm_wiki_cli/commands/team_cmd.py)"]
    n7["_build_sync_prompt (src/llm_wiki_cli/commands/trigger_cmd.py)"]
    n8["_filter_trigger_diff (src/llm_wiki_cli/commands/trigger_cmd.py)"]
    n9["_preflight_trigger_source_selection (src/llm_wiki_cli/commands/trigger_cmd.py)"]
    n10["_trigger_source_snapshot (src/llm_wiki_cli/commands/trigger_cmd.py)"]
    n11["_resolve_openapi_path (src/llm_wiki_cli/services/api_contracts.py)"]
    n12["build_api_contracts (src/llm_wiki_cli/services/api_contracts.py)"]
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
    click n0 "../modules/source_snapshot.md"
    click n1 "../modules/generate_prompt_cmd.md"
    click n2 "../modules/generate_prompt_cmd.md"
    click n3 "../modules/generate_prompt_cmd.md"
    click n4 "../modules/generate_prompt_cmd.md"
    click n5 "../modules/generate_prompt_cmd.md"
    click n6 "../modules/team_cmd.md"
    click n7 "../modules/trigger_cmd.md"
    click n8 "../modules/trigger_cmd.md"
    click n9 "../modules/trigger_cmd.md"
    click n10 "../modules/trigger_cmd.md"
    click n11 "../modules/api_contracts.md"
    click n12 "../modules/api_contracts.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_snapshot](../modules/source_snapshot.md) | 12 | `all_source_paths`, `capture_byte_limit`, `capture_scan_limit`, `captured_content_hashes`, `captured_file_integrity`, `captured_gitignore_paths`, `captured_input_kinds`, `coherent`, `compose_candidates`, `directory_integrity`, `dockerfile_candidates`, `files_by_language` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_build_prompt` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `_resolved_prompt_selection_and_diff` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `_selected_prompt_diff` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `_validated_prompt_selection_and_diff` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `_validated_prompt_snapshot` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `_preflight_team_source_selection` | type_reference | [team_cmd](../modules/team_cmd.md) | — |
| `_build_sync_prompt` | type_reference | [trigger_cmd](../modules/trigger_cmd.md) | — |
| `_filter_trigger_diff` | type_reference | [trigger_cmd](../modules/trigger_cmd.md) | — |
| `_preflight_trigger_source_selection` | type_reference | [trigger_cmd](../modules/trigger_cmd.md) | — |
| `_trigger_source_snapshot` | type_reference | [trigger_cmd](../modules/trigger_cmd.md) | — |
| `_resolve_openapi_path` | type_reference | [api_contracts](../modules/api_contracts.md) | — |
| `build_api_contracts` | type_reference | [api_contracts](../modules/api_contracts.md) | — |

> References: showing 12 of 159 logical references; 147 omitted by the 12-row generated summary limit.
