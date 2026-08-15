# export Module

**Path:** `src/llm_wiki_cli/services/documentation_run/export.py`

## Description

Documentation-run export services.

## Imports

| Source | Symbols |
|--------|---------|
| `..site_export` | `SiteExportError`, `check_site_mirror`, `export_site_mirror` |
| `.contracts` | `*` |
| `.dependencies` | `*` |
| `.integrity` | `*` |
| `.record` | `*` |
| `.refresh` | `*` |
| `.schema` | `*` |
| `.verify` | `*` |
| `.workspace` | `*` |
| `__future__` | `annotations` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/services/documentation_run/__init__.py"]
    n1["src/llm_wiki_cli/services/documentation_run/contracts.py"]
    n2["src/llm_wiki_cli/services/documentation_run/dependencies.py"]
    n3["src/llm_wiki_cli/services/documentation_run/export.py"]
    n4["src/llm_wiki_cli/services/documentation_run/integrity.py"]
    n5["src/llm_wiki_cli/services/documentation_run/record.py"]
    n6["src/llm_wiki_cli/services/documentation_run/refresh.py"]
    n7["src/llm_wiki_cli/services/documentation_run/schema.py"]
    n8["src/llm_wiki_cli/services/documentation_run/verify.py"]
    n9["src/llm_wiki_cli/services/documentation_run/workspace.py"]
    n10["src/llm_wiki_cli/services/site_export.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n0 --> n4
    n0 --> n5
    n0 --> n6
    n0 --> n7
    n0 --> n8
    n0 --> n9
    n1 --> n2
    n1 --> n7
    n3 --> n1
    n3 --> n2
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n3 --> n9
    n3 --> n10
    n4 --> n1
    n4 --> n2
    n4 --> n7
    n4 --> n9
    n5 --> n1
    n5 --> n2
    n5 --> n4
    n5 --> n6
    n5 --> n7
    n5 --> n9
    n6 --> n1
    n6 --> n2
    n6 --> n4
    n6 --> n7
    n6 --> n9
    n7 --> n1
    n7 --> n2
    n8 --> n1
    n8 --> n2
    n8 --> n4
    n8 --> n5
    n8 --> n6
    n8 --> n7
    n8 --> n9
    n9 --> n1
    n9 --> n2
    n9 --> n7
    click n0 "../modules/documentation_run___init__.md"
    click n1 "../modules/documentation_run_contracts.md"
    click n2 "../modules/documentation_run_dependencies.md"
    click n3 "../modules/export.md"
    click n4 "../modules/integrity.md"
    click n5 "../modules/record.md"
    click n6 "../modules/refresh.md"
    click n7 "../modules/documentation_run_schema.md"
    click n8 "../modules/verify.md"
    click n9 "../modules/workspace.md"
    click n10 "../modules/site_export.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [documentation_run___init__](../modules/documentation_run___init__.md) |
| Outbound | [documentation_run_contracts](../modules/documentation_run_contracts.md) |
| Outbound | [documentation_run_dependencies](../modules/documentation_run_dependencies.md) |
| Outbound | [integrity](../modules/integrity.md) |
| Outbound | [record](../modules/record.md) |
| Outbound | [refresh](../modules/refresh.md) |
| Outbound | [documentation_run_schema](../modules/documentation_run_schema.md) |
| Outbound | [verify](../modules/verify.md) |
| Outbound | [workspace](../modules/workspace.md) |
| Outbound | [site_export](../modules/site_export.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_run_authorized_builder` | `(workspace_root: Path, run: DocumentationRun, *, build: bool, builder_command: Iterable[str] \| None) -> dict[str, Any]` | — | — |
| `_read_builder_output_tail` | `(stream) -> tuple[str, int, bool]` | — | — |
| `_remove_built_site_before_builder` | `(workspace_root: Path, built_root: Path) -> None` | — | Remove only the derived built-site root through qualified path guards. |
| `_build_final_report` | `(run: DocumentationRun, *, export_report: Mapping[str, Any], builder_evidence: Mapping[str, Any], site_check: Mapping[str, Any], verification: Mapping[str, Any]) -> dict[str, Any]` | — | — |
| `_render_final_report` | `(report: Mapping[str, Any]) -> str` | — | — |
| `export_documentation_run` | `(workspace: str \| Path, *, build: bool = False, builder_command: Iterable[str] \| None = None, knowledge_mode: str \| None = None, knowledge_public_repository_identity: str \| None = None) -> dict[str, Any]` | — | Export/check the user profile and write a reproducible local handoff. |
