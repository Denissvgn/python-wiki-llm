# gitignore Module

**Path:** `src/llm_wiki_engine/gitignore.py`

## Description

Gitignore matching for source discovery.

``llm_wiki_cli.config`` re-exports every name for existing callers.

## Imports

| Source | Symbols |
|--------|---------|
| `.path_policy` | `EXCLUDED_DIRS`, `is_agent_worktree_path` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `fnmatch` | `fnmatch` |
| `pathlib` | `Path` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/config.py"]
    n1["src/llm_wiki_cli/extractors/common.py"]
    n2["src/llm_wiki_cli/extractors/python_extractor.py"]
    n3["src/llm_wiki_cli/services/source_path_diagnostics.py"]
    n4["src/llm_wiki_cli/services/source_snapshot.py"]
    n5["src/llm_wiki_engine/gitignore.py"]
    n6["src/llm_wiki_engine/path_policy.py"]
    n7["src/llm_wiki_engine/wiki_operations.py"]
    n0 --> n5
    n0 --> n6
    n1 --> n5
    n1 --> n6
    n2 --> n1
    n2 --> n5
    n3 --> n1
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n4 --> n1
    n4 --> n5
    n4 --> n6
    n5 --> n6
    n7 --> n5
    n7 --> n6
    click n0 "../modules/config.md"
    click n1 "../modules/common.md"
    click n2 "../modules/python_extractor.md"
    click n3 "../modules/source_path_diagnostics.md"
    click n4 "../modules/source_snapshot.md"
    click n5 "../modules/gitignore.md"
    click n6 "../modules/path_policy.md"
    click n7 "../modules/wiki_operations.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [config](../modules/config.md) |
| Inbound | [common](../modules/common.md) |
| Inbound | [python_extractor](../modules/python_extractor.md) |
| Inbound | [source_path_diagnostics](../modules/source_path_diagnostics.md) |
| Inbound | [source_snapshot](../modules/source_snapshot.md) |
| Inbound | [wiki_operations](../modules/wiki_operations.md) |
| Outbound | [path_policy](../modules/path_policy.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [_GitignoreRule](../entities/GitignoreRule.md) | 16 | — | — |
| [GitIgnoreMatcher](../entities/GitIgnoreMatcher.md) | 23 | — | Ordered gitignore matcher for repository scans. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_normalize_gitignore_trailing_spaces` | `(line: str) -> str` | — | Remove Git-insignificant trailing spaces from one ignore pattern. |
| `_parse_gitignore_text` | `(raw_text: str, base: str = '') -> list[_GitignoreRule]` | — | Parse already captured gitignore text without performing file I/O. |
| `_parse_gitignore_file` | `(gitignore_path: Path, base: str = '') -> list[_GitignoreRule]` | — | — |
| `_match_gitignore_pattern` | `(rel_path: str, pattern: str, *, directory_only: bool = False) -> bool` | — | Check if a relative path matches a gitignore pattern. |
| `_rule_matches` | `(rel_path: str, rule: _GitignoreRule) -> bool` | — | — |
| `build_gitignore_matcher` | `(root: 'str \| Path') -> GitIgnoreMatcher` | — | Parse root and nested .gitignore files once for a source scan. |
| `is_ignored_by_gitignore` | `(rel_path: str, gitignore_path: Path = Path('.gitignore')) -> bool` | — | Check if a relative path is ignored according to one .gitignore file. |
