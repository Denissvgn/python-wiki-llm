# impact Module

**Path:** `src/llm_wiki_cli/services/impact.py`

## Description

Builds deterministic advisory impact from selected paths and captured candidate
source/wiki coverage. Reports direct page mappings, static dependency edges,
API operation hints, and explicit unknown coverage for deleted sources without
retained provenance. Equivalent change inputs share the same coverage analysis.

GitHub output is limited to fifty annotations and the Markdown summary to
64 KiB, with omissions recorded. Integrity and API compatibility verdicts remain
separate checks.

## Imports

| Source | Symbols |
|--------|---------|
| `.api_contracts` | `build_static_api_contracts` |
| `.change_selection` | `_git`, `patch_paths`, `source_relative_paths` |
| `.dependencies` | `build_dependency_graph` |
| `.review_service` | `build_analysis`, `_is_dependency_path` |
| `.source_snapshot` | `source_snapshot_matches_current_files` |
| `__future__` | `annotations` |
| `dataclasses` | `asdict` |
| `hashlib` | `hashlib` |
| `html` | `html` |
| `json` | `json` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/review_cmd.py"]
    n1["src/llm_wiki_cli/services/api_contracts.py"]
    n2["src/llm_wiki_cli/services/change_selection.py"]
    n3["src/llm_wiki_cli/services/dependencies.py"]
    n4["src/llm_wiki_cli/services/impact.py"]
    n5["src/llm_wiki_cli/services/review_service.py"]
    n6["src/llm_wiki_cli/services/source_snapshot.py"]
    n0 --> n2
    n0 --> n4
    n0 --> n5
    n1 --> n6
    n3 --> n6
    n4 --> n1
    n4 --> n2
    n4 --> n3
    n4 --> n5
    n4 --> n6
    n5 --> n2
    n5 --> n6
    click n0 "../modules/review_cmd.md"
    click n1 "../modules/api_contracts.md"
    click n2 "../modules/change_selection.md"
    click n3 "../modules/services_dependencies.md"
    click n4 "../modules/impact.md"
    click n5 "../modules/review_service.md"
    click n6 "../modules/source_snapshot.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [review_cmd](../modules/review_cmd.md) |
| Outbound | [api_contracts](../modules/api_contracts.md) |
| Outbound | [change_selection](../modules/change_selection.md) |
| Outbound | [services_dependencies](../modules/services_dependencies.md) |
| Outbound | [review_service](../modules/review_service.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `build_impact` | `(diff_text: str = '', *, src_dir = '.', wiki_dir = 'docs/llm_wiki', changes = None, source_selection = None, helper_cache_dir = None) -> dict` | — | — |
| `_cell` | `(value, limit = 512)` | — | — |
| `render_summary` | `(impact: dict) -> str` | — | — |
| `_escape_command` | `(value: str, *, property = False) -> str` | — | — |
| `render_github` | `(impact: dict) -> str` | — | — |
