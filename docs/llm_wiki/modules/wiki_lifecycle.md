# wiki_lifecycle Module

**Path:** `src/llm_wiki_cli/services/wiki_lifecycle.py`

## Description

Read-only classification for wiki bootstrap, sync, and migration routing.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `AGENT_CHOICES` |
| `.filesystem_guard` | `atomic_write_guarded_bytes`, `ensure_guarded_directory` |
| `.io` | `first_unsafe_path_component`, `formatted_json_bytes` |
| `.rendering_lifecycle` | `RenderReason` |
| `.schema` | `SCHEMA_BLOCK_VERSION`, `SchemaRenderProfile` |
| `.sync_manifest` | `MANIFEST_FILENAME` |
| `.wiki_scaffold` | `INITIAL_WIKI_INDEX_MARKDOWN`, `INITIAL_WIKI_LOG_MARKDOWN` |
| `.wiki_surface` | `iter_directory_kinds`, `iter_page_kinds` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `enum` | `Enum` |
| `json` | `json` |
| `os` | `os` |
| `pathlib` | `Path` |
| `shlex` | `shlex` |
| `subprocess` | `subprocess` |
| `typing` | `Union` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/wiki_lifecycle.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/wiki_lifecycle.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (7) |
| Outbound | `src` (8) |

> All 15 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [WikiScaffoldPathError](../entities/WikiScaffoldPathError.md) | Class | 27 | `ValueError` | Raised when a managed scaffold path is redirected or non-regular. |
| [WikiScaffoldProvision](../entities/WikiScaffoldProvision.md) | Class | 32 | — | Additive scaffold entries created by one guarded provisioning pass. |
| [WikiLifecycleState](../entities/WikiLifecycleState.md) | Enum | 130 | `str`, `Enum` | One unambiguous lifecycle route for a wiki target. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `require_safe_wiki_scaffold` | `(wiki_dir: Union[str, Path]) -> None` | — | Preflight every managed scaffold path before any lifecycle mutation. |
| `provision_wiki_scaffold` | `(wiki_dir: Union[str, Path]) -> WikiScaffoldProvision` | — | Create missing scaffold entries with no-follow, descriptor-pinned writes. |
| `_uses_windows_command_line` | `() -> bool` | — | Return whether lifecycle guidance should use Windows CLI quoting. |
| `_render_recovery_command` | `(arguments: list[str]) -> str` | — | Render a copy-pasteable recovery command for the current platform. |
| `is_pristine_wiki_target` | `(wiki_dir: Union[str, Path]) -> bool` | — | Return whether a target is absent, empty, or the exact init scaffold. |
| `classify_wiki_lifecycle` | `(wiki_dir: Union[str, Path]) -> WikiLifecycleState` | — | Classify a target without reading source code or mutating the wiki. |
| `bootstrap_guidance` | `(*, src_dir: str, wiki_dir: Union[str, Path]) -> str` | — | Return a path-safe first-use bootstrap command. |
| `migration_guidance` | `(*, src_dir: str, wiki_dir: Union[str, Path]) -> str` | — | Return a path-safe migration preview command. |
| `sync_guidance` | `(*, src_dir: str, wiki_dir: Union[str, Path]) -> str` | — | Return a path-safe manifest-seeding sync command. |
