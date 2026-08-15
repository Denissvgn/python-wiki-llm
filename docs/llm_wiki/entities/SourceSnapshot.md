# SourceSnapshot

**Location:** `src/llm_wiki_cli/services/source_snapshot.py:126`
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
    n6["src/llm_wiki_cli/commands/migrate_cmd.py"]
    n7["_build_surface_index_pages (src/llm_wiki_cli/commands/review_cmd.py)"]
    n8["_flow_pages_by_source (src/llm_wiki_cli/commands/review_cmd.py)"]
    n9["_preflight_review_source_selection (src/llm_wiki_cli/commands/review_cmd.py)"]
    n10["_surface_index_pages (src/llm_wiki_cli/commands/review_cmd.py)"]
    n11["_append_log (src/llm_wiki_cli/commands/sync_cmd.py)"]
    n12["_apply_current_infrastructure_plan (src/llm_wiki_cli/commands/sync_cmd.py)"]
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
    click n6 "../modules/migrate_cmd.md"
    click n7 "../modules/review_cmd.md"
    click n8 "../modules/review_cmd.md"
    click n9 "../modules/review_cmd.md"
    click n10 "../modules/review_cmd.md"
    click n11 "../modules/sync_cmd.md"
    click n12 "../modules/sync_cmd.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [source_snapshot](../modules/source_snapshot.md) | 12 | `all_source_paths`, `captured_content_hashes`, `captured_file_integrity`, `captured_gitignore_paths`, `captured_input_kinds`, `compose_candidates`, `dockerfile_candidates`, `files_by_language`, `gitignore_fingerprint`, `gitignore_rules`, `include_tests`, `only_files` |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `_build_prompt` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `_resolved_prompt_selection_and_diff` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `_selected_prompt_diff` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `_validated_prompt_selection_and_diff` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `_validated_prompt_snapshot` | type_reference | [generate_prompt_cmd](../modules/generate_prompt_cmd.md) | — |
| `migrate_cmd` | import | [migrate_cmd](../modules/migrate_cmd.md) | — |
| `_build_surface_index_pages` | type_reference | [review_cmd](../modules/review_cmd.md) | — |
| `_flow_pages_by_source` | type_reference | [review_cmd](../modules/review_cmd.md) | — |
| `_preflight_review_source_selection` | type_reference | [review_cmd](../modules/review_cmd.md) | — |
| `_surface_index_pages` | type_reference | [review_cmd](../modules/review_cmd.md) | — |
| `_append_log` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |
| `_apply_current_infrastructure_plan` | type_reference | [sync_cmd](../modules/sync_cmd.md) | — |

> References: showing 12 of 146 logical references; 134 omitted by the 12-row generated summary limit.
