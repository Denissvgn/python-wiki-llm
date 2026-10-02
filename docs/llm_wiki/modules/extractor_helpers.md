# extractor_helpers Module

**Path:** `src/llm_wiki_cli/services/extractor_helpers.py`

## Description

Preparation and lookup for external extractor helper tools.
Resolves tool overrides and validates prepared helper manifests against their
source, platform, and artifact identities. Unreadable or invalid manifests leave
the helper unprepared so diagnostics can provide a corrective preparation command.

Recovery commands preserve the failing language, resolved source root, and
helper cache base. They request external-source access only when the root is
outside the caller's workspace. POSIX and PowerShell rendering preserves
literal path arguments. Without a Git or configured cache, the remedy proposes
an explicit cache base and explains how subsequent reads should select it.
Preparation remains a separate authorized operation; diagnostics do not invoke
toolchains or change the source and wiki.

## Imports

| Source | Symbols |
|--------|---------|
| `.inventory_cache` | `ENV_CACHE_DIR` |
| `.paths` | `render_shell_command` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `os` | `os` |
| `pathlib` | `Path` |
| `platform` | `platform` |
| `re` | `re` |
| `shutil` | `shutil` |
| `subprocess` | `subprocess` |
| `sys` | `sys` |
| `typing` | `Any` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/extractor_helpers.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/extractor_helpers.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (10) |
| Outbound | `src` (2) |

> All 12 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Line | Bases | Description |
|-------|------|-------|-------------|
| [HelperPrepareResult](../entities/HelperPrepareResult.md) | 50 | — | — |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `extractor_timeout_seconds` | `() -> int` | — | Return the configured extractor runtime timeout, with a one-second floor. |
| `_binary_name` | `(base: str) -> str` | — | — |
| `_resolve_gitdir_file` | `(git_file: Path) -> Path \| None` | — | — |
| `_nearest_git_dir` | `(start: Path) -> Path \| None` | — | — |
| `resolve_helper_cache_root` | `(src_dir: str \| Path, cache_dir: str \| None = None, *, env: dict[str, str] \| None = None) -> Path \| None` | — | Resolve the helper cache root using CLI/env/git precedence. |
| `platform_id` | `() -> str` | — | — |
| `_hash_labeled_files` | `(paths: list[tuple[str, Path]]) -> str` | — | — |
| `helper_source_files` | `(language: str) -> list[tuple[str, Path]]` | — | — |
| `helper_source_fingerprint` | `(language: str) -> str` | — | — |
| `helper_artifact_fingerprint` | `(path: Path) -> str` | — | — |
| `command_output` | `(cmd: list[str], *, cwd: Path \| None = None, timeout: int = 15) -> str \| None` | — | — |
| `_resolve_go_executable` | `(env: dict[str, str] \| None = None) -> str \| None` | — | — |
| `_resolve_ghc_executable` | `(env: dict[str, str] \| None = None) -> str \| None` | — | — |
| `_go_version` | `(go_executable: str, *, timeout: int = 15) -> tuple[str \| None, str]` | — | — |
| `_ghc_version` | `(ghc_executable: str, *, timeout: int = 15) -> tuple[str \| None, str]` | — | — |
| `_parse_ghc_version` | `(toolchain: str) -> tuple[int, int, int] \| None` | — | — |
| `_ghc_support_error` | `(toolchain: str) -> str \| None` | — | — |
| `_env_has_value` | `(env: dict[str, str], name: str) -> bool` | — | Return True when *env* contains a non-empty variable named *name*. |
| `helper_cache_key` | `(language: str, *, toolchain_version: str \| None = None, platform_value: str \| None = None) -> str` | — | — |
| `_manifest_path` | `(cache_root: Path, language: str) -> Path` | — | — |
| `_load_manifest` | `(cache_root: Path, language: str) -> dict[str, Any] \| None` | — | — |
| `_write_manifest` | `(cache_root: Path, language: str, data: dict[str, Any]) -> None` | — | — |
| `_manifest_current` | `(cache_root: Path, language: str) -> dict[str, Any] \| None` | — | — |
| `helper_preparation_argv` | `(language: str, src_dir: str \| Path = '.', cache_dir: str \| None = None) -> list[str]` | — | Describe cache-only recovery for one helper without executing or writing. |
| `helper_preparation_failure_hint` | `(language: str) -> str` | — | — |
| `get_prepared_binary` | `(language: str, src_dir: str \| Path = '.', cache_dir: str \| None = None) -> Path \| None` | — | — |
| `get_prepared_typescript_root` | `(src_dir: str \| Path = '.', cache_dir: str \| None = None) -> Path \| None` | — | — |
| `missing_helper_message` | `(language: str, src_dir: str \| Path = '.', cache_dir: str \| None = None) -> str` | — | — |
| `typescript_dependencies_ready` | `(src_dir: str \| Path = '.', cache_dir: str \| None = None) -> bool` | — | — |
| `prepare_typescript` | `(cache_root: Path) -> HelperPrepareResult` | — | — |
| `prepare_go` | `(cache_root: Path) -> HelperPrepareResult` | — | — |
| `prepare_rust` | `(cache_root: Path) -> HelperPrepareResult` | — | — |
| `prepare_haskell` | `(cache_root: Path) -> HelperPrepareResult` | — | — |
| `prepare_helper` | `(language: str, cache_root: Path) -> HelperPrepareResult` | — | — |
