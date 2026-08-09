# imports Module

**Path:** `src/llm_wiki_cli/services/imports.py`

## Description

_Auto-generated from `src/llm_wiki_cli/services/imports.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `is_agent_worktree_path` |
| `.source_snapshot` | `SourceSnapshot` |
| `.validation` | `path_is_under`, `path_is_under_scope` |
| `__future__` | `annotations` |
| `collections` | `defaultdict` |
| `dataclasses` | `dataclass` |
| `json` | `json` |
| `os` | `os` |
| `pathlib` | `Path`, `PurePosixPath` |
| `posixpath` | `posixpath` |
| `typing` | `TYPE_CHECKING` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/config.py"]
    n1["src/llm_wiki_cli/extractors/python_extractor.py"]
    n2["src/llm_wiki_cli/services/api_contracts.py"]
    n3["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n4["src/llm_wiki_cli/services/dependencies.py"]
    n5["src/llm_wiki_cli/services/entrypoints.py"]
    n6["src/llm_wiki_cli/services/extraction_service.py"]
    n7["src/llm_wiki_cli/services/imports.py"]
    n8["src/llm_wiki_cli/services/relationships.py"]
    n9["src/llm_wiki_cli/services/source_snapshot.py"]
    n10["src/llm_wiki_cli/services/validation.py"]
    n1 --> n0
    n1 --> n7
    n2 --> n7
    n2 --> n9
    n3 --> n0
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n3 --> n9
    n3 --> n10
    n4 --> n0
    n4 --> n7
    n4 --> n9
    n4 --> n10
    n5 --> n7
    n5 --> n9
    n5 --> n10
    n6 --> n0
    n6 --> n1
    n6 --> n2
    n6 --> n4
    n6 --> n5
    n6 --> n7
    n6 --> n9
    n7 --> n0
    n7 --> n9
    n7 --> n10
    n8 --> n7
    n8 --> n10
    n9 --> n0
    n9 --> n10
    click n0 "../modules/config.md"
    click n1 "../modules/python_extractor.md"
    click n2 "../modules/api_contracts.md"
    click n3 "../modules/bootstrap_runtime.md"
    click n4 "../modules/services_dependencies.md"
    click n5 "../modules/entrypoints.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/imports.md"
    click n8 "../modules/relationships.md"
    click n9 "../modules/source_snapshot.md"
    click n10 "../modules/validation.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [python_extractor](../modules/python_extractor.md) |
| Inbound | [api_contracts](../modules/api_contracts.md) |
| Inbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Inbound | [services_dependencies](../modules/services_dependencies.md) |
| Inbound | [entrypoints](../modules/entrypoints.md) |
| Inbound | [extraction_service](../modules/extraction_service.md) |
| Inbound | [relationships](../modules/relationships.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |
| Outbound | [validation](../modules/validation.md) |

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [_TsPathAliasRule](../entities/TsPathAliasRule.md) | 22 | — | One ``compilerOptions.paths`` mapping scoped to its tsconfig directory. |
| [_GoModuleScope](../entities/GoModuleScope.md) | 33 | — | One ``go.mod`` module declaration scoped to its directory. |
| [ModulePathResolver](../entities/ModulePathResolver.md) | 41 | — | Indexed module import resolver for a fixed inventory. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_suffix_candidates` | `(path_no_suffix: str) -> set[str]` | — | — |
| `_normalize_module` | `(module: str) -> str` | — | — |
| `_is_python_from_import` | `(module: str, name: str, import_type: str \| None) -> bool` | — | Return whether an import record can name a Python child module. |
| `_python_from_import_child` | `(module: str, name: str) -> str` | — | Join the two parts of ``from <module> import <name>`` as a module. |
| `_candidate_stems` | `(module: str, importer_filepath: str) -> set[str]` | — | — |
| `_is_go_file` | `(filepath: str, data: object) -> bool` | — | — |
| `_language_family` | `(data: object) -> str` | — | — |
| `_is_haskell_entry` | `(data: object) -> bool` | — | — |
| `_is_typescript_entry` | `(data: object) -> bool` | — | — |
| `_is_typescript_index` | `(filepath: str, data: object) -> bool` | — | — |
| `_normalize_haskell_module` | `(module: object) -> str` | — | — |
| `_package_dir` | `(filepath: str) -> str` | — | — |
| `_relative_package_dir` | `(module: str, importer_filepath: str) -> str` | — | — |
| `_read_go_module_scopes` | `(project_root: str \| Path \| None, source_snapshot: SourceSnapshot \| None = None) -> tuple[_GoModuleScope, ...]` | — | — |
| `_go_module_dir_is_agent_worktree` | `(project_root: Path, root_path: Path, dirname: str) -> bool` | — | — |
| `_read_go_module_path` | `(path: Path) -> str` | — | — |
| `_go_package_dir_for_module` | `(module: str, scope: _GoModuleScope) -> str` | — | — |
| `_path_under` | `(path: str, prefix: str) -> bool` | — | — |
| `_path_under_scope` | `(path: str, scope_root: str) -> bool` | — | — |
| `_read_ts_path_aliases` | `(project_root: str \| Path \| None, source_snapshot: SourceSnapshot \| None = None) -> tuple[_TsPathAliasRule, ...]` | — | — |
| `_snapshot_marker_paths` | `(project_root: Path, source_snapshot: SourceSnapshot, filename: str) -> list[Path]` | — | — |
| `_parse_tsconfig_aliases` | `(project_root: Path, tsconfig: Path) -> list[_TsPathAliasRule]` | — | — |
| `_project_relative_dir` | `(project_root: Path, directory: Path) -> str` | — | — |
| `_join_posix` | `(*parts: str) -> str` | — | — |
| `_nearest_ts_alias_root` | `(rules: tuple[_TsPathAliasRule, ...], importer_filepath: str) -> str \| None` | — | — |
| `_match_ts_alias_rule` | `(rule: _TsPathAliasRule, spec: str) -> str \| None` | — | — |
| `_ts_alias_target_stems` | `(target: str, star: str) -> set[str]` | — | — |
| `_strip_ts_source_suffix` | `(path: str) -> str` | — | — |
| `build_module_path_resolver` | `(inventory: dict, project_root: str \| Path \| None = None, *, source_snapshot: SourceSnapshot \| None = None) -> ModulePathResolver` | — | Build an indexed import resolver for repeated lookups. |
