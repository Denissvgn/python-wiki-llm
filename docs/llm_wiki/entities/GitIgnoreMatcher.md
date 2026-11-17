# GitIgnoreMatcher

**Location:** `src/llm_wiki_cli/services/gitignore.py:23`
**Kind:** Class
**Bases:** —
**Module:** [gitignore](../modules/gitignore.md)

## Description

Ordered gitignore matcher for repository scans.

This supports the semantics the extractors need without reparsing the same
.gitignore file for every source file: negation, root-anchored patterns,
nested .gitignore files, directory-only rules, and common ``**`` patterns.

## Attributes

*No annotated attributes found.*

## Methods

| Method | Signature | Decorators | Description |
|--------|-----------|------------|-------------|
| `__init__` | `(rules: list[_GitignoreRule])` | — | — |
| `last_matching_rule` | `(rel_path: str) -> _GitignoreRule \| None` | — | Return the final gitignore rule that matches *rel_path*, if any. |
| `is_ignored` | `(rel_path: str) -> bool` | — | — |

## Relationships

<!-- Auto-generated relationship summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["GitIgnoreMatcher (src/llm_wiki_cli/services/gitignore.py)"]
    n1["src/llm_wiki_cli/config.py"]
    n2["discover_source_files (src/llm_wiki_cli/extractors/common.py)"]
    n3["should_skip_source_path (src/llm_wiki_cli/extractors/common.py)"]
    n4["build_gitignore_matcher (src/llm_wiki_cli/services/gitignore.py)"]
    n5["is_ignored_by_gitignore (src/llm_wiki_cli/services/gitignore.py)"]
    n6["assert_bootstrap_output_excluded (src/llm_wiki_cli/services/publication_snapshot.py)"]
    n7["source_path_diagnostics (src/llm_wiki_cli/services/source_path_diagnostics.py)"]
    n8["_collect_source_selection_controls (src/llm_wiki_cli/services/source_snapshot.py)"]
    n9["_collect_source_tree (src/llm_wiki_cli/services/source_snapshot.py)"]
    n10["_directory_ignored (src/llm_wiki_cli/services/source_snapshot.py)"]
    n11["_is_rescuable_typescript_src_lib_directory (src/llm_wiki_cli/services/source_snapshot.py)"]
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
    click n0 "../modules/gitignore.md"
    click n1 "../modules/config.md"
    click n2 "../modules/common.md"
    click n3 "../modules/common.md"
    click n4 "../modules/gitignore.md"
    click n5 "../modules/gitignore.md"
    click n6 "../modules/publication_snapshot.md"
    click n7 "../modules/source_path_diagnostics.md"
    click n8 "../modules/source_snapshot.md"
    click n9 "../modules/source_snapshot.md"
    click n10 "../modules/source_snapshot.md"
    click n11 "../modules/source_snapshot.md"
```

### Summary

| Module | Methods | Attributes |
|---|---:|---|
| [gitignore](../modules/gitignore.md) | 3 | — |

### References

| Reference | Kind | Source | Call sites |
|---|---|---|---:|
| `config` | import | [config](../modules/config.md) | — |
| `discover_source_files` | type_reference | [common](../modules/common.md) | — |
| `should_skip_source_path` | type_reference | [common](../modules/common.md) | — |
| `build_gitignore_matcher` | call | [gitignore](../modules/gitignore.md) | 2 |
| `build_gitignore_matcher` | type_reference | [gitignore](../modules/gitignore.md) | — |
| `is_ignored_by_gitignore` | call | [gitignore](../modules/gitignore.md) | 1 |
| `assert_bootstrap_output_excluded` | call | [publication_snapshot](../modules/publication_snapshot.md) | 1 |
| `source_path_diagnostics` | call | [source_path_diagnostics](../modules/source_path_diagnostics.md) | 1 |
| `_collect_source_selection_controls` | call | [source_snapshot](../modules/source_snapshot.md) | 1 |
| `_collect_source_tree` | call | [source_snapshot](../modules/source_snapshot.md) | 1 |
| `_directory_ignored` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |
| `_is_rescuable_typescript_src_lib_directory` | type_reference | [source_snapshot](../modules/source_snapshot.md) | — |

> References: showing 12 of 19 logical references; 7 omitted by the 12-row generated summary limit.
