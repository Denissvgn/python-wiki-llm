# config Module

**Path:** `src/llm_wiki_cli/config.py`

## Description

Shared constants and utilities for agent-wiki-cli.

## Imports

| Source | Symbols |
|--------|---------|
| `.services.extractor_registry` | `DOCKERFILE_PATTERNS`, `COMPOSE_PATTERNS`, `EXTRACTOR_REGISTRY` |
| `.services.filesystem_guard` | `atomic_write_private_bytes`, `ensure_guarded_directory` |
| `.services.gitignore` | `_GitignoreRule`, `GitIgnoreMatcher`, `_normalize_gitignore_trailing_spaces`, `_parse_gitignore_text`, `_parse_gitignore_file`, `_match_gitignore_pattern`, `_rule_matches`, `build_gitignore_matcher`, `is_ignored_by_gitignore` |
| `.services.io` | `first_unsafe_path_component` |
| `.services.knowledge_evidence` | `formatted_json_bytes` |
| `.services.path_policy` | `DEFAULT_WIKI_DIR`, `EXCLUDED_DIRS`, `AGENT_WORKTREE_DIR_PATTERNS`, `_normalized_rel_parts`, `is_agent_worktree_path`, `PathValidationError`, `validate_path`, `validate_source_root`, `validate_source_paths` |
| `__future__` | `annotations` |
| `dataclasses` | `dataclass` |
| `enum` | `Enum` |
| `json` | `json` |
| `os` | `os` |
| `pathlib` | `Path` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/config.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/config.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (41) |
| Outbound | `src` (6) |

> All 47 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Classes

| Class | Kind | Line | Bases / Target | Description |
|-------|------|------|----------------|-------------|
| [AgentConfigState](../entities/AgentConfigState.md) | Enum | 84 | `str`, `Enum` | Compatibility classification for the local agent configuration. |
| [AgentConfigInspection](../entities/AgentConfigInspection.md) | Class | 94 | — | One safe configuration read with provenance for status reporting. |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `get_agent_config_path` | `(wiki_dir: 'str \| Path') -> Path` | — | Return the local-only agent config file path. |
| `inspect_config_path` | `(config_path: 'str \| Path') -> AgentConfigInspection` | — | Inspect one exact local-agent config path without hiding its state. |
| `inspect_config` | `(wiki_dir: 'str \| Path') -> AgentConfigInspection` | — | Inspect the canonical config, adopting one safe legacy home if needed. |
| `config_requires_manual_recovery` | `(inspection: AgentConfigInspection) -> bool` | — | Return whether config bytes must be inspected before lifecycle mutation. |
| `read_config` | `(wiki_dir: 'str \| Path') -> dict` | — | Return the backward-compatible config mapping used by older callers. |
| `require_safe_config_path` | `(wiki_dir: 'str \| Path') -> Path` | — | Return an absent or regular config path with no redirected component. |
| `write_config` | `(wiki_dir: 'str \| Path', data: dict, *, expected_existing: bytes \| None \| object = _CONFIG_EXPECTATION_UNSET) -> None` | — | Atomically persist config, optionally bound to an inspected snapshot. |
| `require_committed_config` | `(wiki_dir: 'str \| Path', data: dict) -> None` | — | Require one canonical config home containing exactly the committed bytes. |
| `require_config_inspection_unchanged` | `(wiki_dir: 'str \| Path', expected: AgentConfigInspection) -> None` | — | Require the exact config/home snapshot inspected before mutation. |
