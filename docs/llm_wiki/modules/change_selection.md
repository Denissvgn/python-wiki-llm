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
| `re` | `re` |
| `subprocess` | `subprocess` |
| `typing` | `Mapping` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/review_cmd.py"]
    n1["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n2["src/llm_wiki_cli/services/change_selection.py"]
    n3["src/llm_wiki_cli/services/context_budget.py"]
    n4["src/llm_wiki_cli/services/context_packet.py"]
    n5["src/llm_wiki_cli/services/context_service.py"]
    n6["src/llm_wiki_cli/services/extraction_service.py"]
    n7["src/llm_wiki_cli/services/impact.py"]
    n8["src/llm_wiki_cli/services/review_service.py"]
    n9["src/llm_wiki_cli/services/task_context.py"]
    n10["src/llm_wiki_cli/services/task_context_v2.py"]
    n11["src/llm_wiki_cli/services/task_contract.py"]
    n0 --> n2
    n0 --> n7
    n0 --> n8
    n1 --> n6
    n2 --> n1
    n2 --> n6
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n4 --> n2
    n4 --> n5
    n4 --> n6
    n5 --> n2
    n5 --> n3
    n5 --> n4
    n5 --> n6
    n7 --> n2
    n7 --> n8
    n8 --> n1
    n8 --> n2
    n8 --> n6
    n9 --> n2
    n9 --> n3
    n9 --> n4
    n9 --> n5
    n9 --> n10
    n9 --> n11
    n10 --> n2
    n10 --> n3
    n10 --> n4
    n10 --> n5
    n10 --> n6
    n10 --> n9
    n10 --> n11
    n11 --> n2
    click n0 "../modules/review_cmd.md"
    click n1 "../modules/bootstrap_runtime.md"
    click n2 "../modules/change_selection.md"
    click n3 "../modules/context_budget.md"
    click n4 "../modules/context_packet.md"
    click n5 "../modules/context_service.md"
    click n6 "../modules/extraction_service.md"
    click n7 "../modules/impact.md"
    click n8 "../modules/review_service.md"
    click n9 "../modules/task_context.md"
    click n10 "../modules/task_context_v2.md"
    click n11 "../modules/task_contract.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [review_cmd](../modules/review_cmd.md) |
| Inbound | [context_budget](../modules/context_budget.md) |
| Inbound | [context_packet](../modules/context_packet.md) |
| Inbound | [context_service](../modules/context_service.md) |
| Inbound | [impact](../modules/impact.md) |
| Inbound | [review_service](../modules/review_service.md) |
| Inbound | [task_context](../modules/task_context.md) |
| Inbound | [task_context_v2](../modules/task_context_v2.md) |
| Inbound | [task_contract](../modules/task_contract.md) |
| Outbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Outbound | [extraction_service](../modules/extraction_service.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `portable_path` | `(value: str) -> str` | — | — |
| `validate_changes` | `(value: object) -> dict` | — | — |
| `changes_from_args` | `(args) -> dict \| None` | — | — |
| `_git` | `(root, *arguments) -> str` | — | — |
| `source_relative_paths` | `(paths, root, *, prefix = None) -> list[str]` | — | Map repo-relative Git/patch paths through an exact source-root prefix. |
| `select_changes` | `(root, request, *, snapshot = None) -> dict` | — | — |
| `_patch_path` | `(value: str, *, git_prefix: bool = False) -> str \| None` | — | — |
| `_git_patch_header_paths` | `(line: str) -> set[str]` | — | — |
| `patch_paths` | `(text: str) -> list[str]` | — | Read file headers, including binary/mode changes, without reading hunks. |
| `affected_page_map` | `(paths, inventory: Mapping, surface_pages = (), *, page_contents: Mapping[str, str] \| None = None) -> dict[str, list[str]]` | — | Map exact sources to canonical pages; never match ambiguous suffixes. |