# wiki_lifecycle Module

**Path:** `src/llm_wiki_cli/services/wiki_lifecycle.py`

## Description

Read-only classification for wiki bootstrap, sync, and migration routing.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `AGENT_CHOICES` |
| `.sync_manifest` | `MANIFEST_FILENAME` |
| `.wiki_scaffold` | `INITIAL_WIKI_INDEX_MARKDOWN`, `INITIAL_WIKI_LOG_MARKDOWN` |
| `.wiki_surface` | `iter_page_kinds` |
| `__future__` | `annotations` |
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
    n0["src/llm_wiki_cli/commands/sync_cmd.py"]
    n1["src/llm_wiki_cli/config.py"]
    n2["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n3["src/llm_wiki_cli/services/lint_service.py"]
    n4["src/llm_wiki_cli/services/sync_manifest.py"]
    n5["src/llm_wiki_cli/services/wiki_lifecycle.py"]
    n6["src/llm_wiki_cli/services/wiki_scaffold.py"]
    n7["src/llm_wiki_cli/services/wiki_surface.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n4
    n0 --> n5
    n0 --> n7
    n2 --> n1
    n2 --> n4
    n2 --> n5
    n2 --> n7
    n3 --> n1
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n7
    n5 --> n1
    n5 --> n4
    n5 --> n6
    n5 --> n7
    click n0 "../modules/sync_cmd.md"
    click n1 "../modules/config.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/lint_service.md"
    click n4 "../modules/sync_manifest.md"
    click n5 "../modules/wiki_lifecycle.md"
    click n6 "../modules/wiki_scaffold.md"
    click n7 "../modules/wiki_surface.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [sync_cmd](../modules/sync_cmd.md) |
| Inbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Inbound | [lint_service](../modules/lint_service.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |
| Outbound | [wiki_scaffold](../modules/wiki_scaffold.md) |
| Outbound | [wiki_surface](../modules/wiki_surface.md) |

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [WikiLifecycleState](../entities/WikiLifecycleState.md) | Enum | 22 | `str`, `Enum` | One unambiguous lifecycle route for a wiki target. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_uses_windows_command_line` | `() -> bool` | — | Return whether lifecycle guidance should use Windows CLI quoting. |
| `_render_recovery_command` | `(arguments: list[str]) -> str` | — | Render a copy-pasteable recovery command for the current platform. |
| `is_pristine_wiki_target` | `(wiki_dir: Union[str, Path]) -> bool` | — | Return whether a target is absent, empty, or the exact init scaffold. |
| `classify_wiki_lifecycle` | `(wiki_dir: Union[str, Path]) -> WikiLifecycleState` | — | Classify a target without reading source code or mutating the wiki. |
| `bootstrap_guidance` | `(*, src_dir: str, wiki_dir: Union[str, Path]) -> str` | — | Return a path-safe first-use bootstrap command. |
| `migration_guidance` | `(*, src_dir: str, wiki_dir: Union[str, Path]) -> str` | — | Return a path-safe migration preview command. |
| `sync_guidance` | `(*, src_dir: str, wiki_dir: Union[str, Path]) -> str` | — | Return a path-safe manifest-seeding sync command. |
