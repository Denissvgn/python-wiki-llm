# change_selection Module

**Path:** `src/llm_wiki_cli/services/change_selection.py`

## Description

Resolves supplied paths, Git ranges, staged changes, and patch file headers into
portable source-relative selections. Patch parsing handles quoted paths and
binary, mode, copy, and rename headers while respecting hunk boundaries.

Shared page mapping uses exact generated module Path and entity Location
provenance to resolve naming collisions and conflicting retained mappings.
Callers can supply already captured page contents to preserve their read basis.

## Imports

| Source | Symbols |
|--------|---------|
| `.bootstrap_runtime` | `build_entity_occurrence_page_map`, `build_entity_page_map`, `build_module_page_map` |
| `.extraction_service` | `_git_name_status_paths`, `_partition_snapshot_git_changes` |
| `__future__` | `annotations` |
| `ast` | `ast` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `llm_wiki_engine.context_request_format` | `portable_path`, `validate_changes` |
| `llm_wiki_engine.host` | `current_host` |
| `re` | `re` |
| `subprocess` | `subprocess` |
| `typing` | `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src"]
    n1["src/llm_wiki_cli/services/change_selection.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/change_selection.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (8) |
| Outbound | `src` (4) |

> All 12 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `changes_from_args` | `(args) -> dict \| None` | — | — |
| `_git` | `(root, *arguments) -> str` | — | — |
| `source_relative_paths` | `(paths, root, *, prefix = None) -> list[str]` | — | Map repo-relative Git/patch paths through an exact source-root prefix. |
| `select_changes` | `(root, request, *, snapshot = None) -> dict` | — | — |
| `_patch_path` | `(value: str, *, git_prefix: bool = False) -> str \| None` | — | — |
| `_git_patch_header_paths` | `(line: str) -> set[str]` | — | — |
| `patch_paths` | `(text: str) -> list[str]` | — | Read file headers, including binary/mode changes, without reading hunks. |
| `affected_page_map` | `(paths, inventory: Mapping, surface_pages = (), *, page_contents: Mapping[str, str] \| None = None) -> dict[str, list[str]]` | — | Map exact sources to canonical pages; never match ambiguous suffixes. |
