# team_cmd Module

**Path:** `src/llm_wiki_cli/commands/team_cmd.py`

## Description

_Auto-generated from `src/llm_wiki_cli/commands/team_cmd.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `DEFAULT_WIKI_DIR`, `validate_path`, `validate_source_root` |
| `..services` | `team` |
| `..services.extraction_service` | `get_docker_inventory`, `get_inventory_result` |
| `..services.source_selection` | `resolve_source_selection`, `validate_persisted_source_selection_identity` |
| `..services.source_snapshot` | `SourceSnapshot`, `build_source_snapshot`, `capture_source_selection_inputs` |
| `..services.sync_manifest` | `SyncManifest` |
| `__future__` | `annotations` |
| `json` | `json` |
| `pathlib` | `Path` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/team_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/extraction_service.py"]
    n4["src/llm_wiki_cli/services/source_selection.py"]
    n5["src/llm_wiki_cli/services/source_snapshot.py"]
    n6["src/llm_wiki_cli/services/sync_manifest.py"]
    n7["src/llm_wiki_cli/services/team.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n1 --> n7
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n4 --> n2
    n5 --> n2
    n5 --> n4
    n6 --> n4
    n6 --> n5
    n7 --> n2
    n7 --> n3
    n7 --> n4
    n7 --> n5
    n7 --> n6
    click n0 "../modules/cli.md"
    click n1 "../modules/team_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/extraction_service.md"
    click n4 "../modules/source_selection.md"
    click n5 "../modules/source_snapshot.md"
    click n6 "../modules/sync_manifest.md"
    click n7 "../modules/team.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [extraction_service](../modules/extraction_service.md) |
| Outbound | [source_selection](../modules/source_selection.md) |
| Outbound | [source_snapshot](../modules/source_snapshot.md) |
| Outbound | [sync_manifest](../modules/sync_manifest.md) |
| Outbound | [team](../modules/team.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_render_issues_text` | `(title: str, issues: list[dict]) -> str` | — | — |
| `_render_conflicts_text` | `(result: dict) -> str` | — | — |
| `_print_payload` | `(payload: dict, output_format: str, *, conflict: bool = False) -> None` | — | — |
| `_run_init` | `(args) -> None` | — | — |
| `_preflight_team_source_selection` | `(src_dir: str, wiki_dir: str \| Path, source_selection: str \| Path \| None) -> SourceSnapshot` | — | — |
| `_run_check` | `(args) -> None` | — | — |
| `_run_resolve_conflicts` | `(args) -> None` | — | — |
| `run` | `(args) -> None` | — | — |
