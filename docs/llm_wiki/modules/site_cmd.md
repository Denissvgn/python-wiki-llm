# site_cmd Module

**Path:** `src/llm_wiki_cli/commands/site_cmd.py`

## Description

Commands for exporting LLM Wiki into a static-site-friendly mirror.

## Imports

| Source | Symbols |
|--------|---------|
| `..cli_declarations` | `KNOWLEDGE_METADATA_CHOICES` |
| `..config` | `DEFAULT_WIKI_DIR`, `validate_path` |
| `..services.knowledge_consumption` | `load_knowledge_read_view` |
| `..services.knowledge_model` | `KnowledgeProjectionProfile` |
| `..services.knowledge_projection` | `KnowledgeProjection`, `project_knowledge` |
| `..services.site_export` | `SUPPORTED_KNOWLEDGE_METADATA`, `SiteExportError`, `check_site_hub`, `check_site_mirror`, `export_site_hub`, `export_site_mirror`, `render_report_json`, `render_report_text`, `resolve_site_hub_sources` |
| `__future__` | `annotations` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/cli_declarations.py"]
    n2["src/llm_wiki_cli/commands/site_cmd.py"]
    n3["src/llm_wiki_cli/config.py"]
    n4["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n5["src/llm_wiki_cli/services/knowledge_model.py"]
    n6["src/llm_wiki_cli/services/knowledge_projection.py"]
    n7["src/llm_wiki_cli/services/site_export.py"]
    n0 --> n1
    n0 --> n2
    n0 --> n3
    n1 --> n3
    n1 --> n5
    n1 --> n7
    n2 --> n1
    n2 --> n3
    n2 --> n4
    n2 --> n5
    n2 --> n6
    n2 --> n7
    n4 --> n5
    n6 --> n4
    n6 --> n5
    n7 --> n6
    click n0 "../modules/cli.md"
    click n1 "../modules/cli_declarations.md"
    click n2 "../modules/site_cmd.md"
    click n3 "../modules/config.md"
    click n4 "../modules/knowledge_consumption.md"
    click n5 "../modules/knowledge_model.md"
    click n6 "../modules/knowledge_projection.md"
    click n7 "../modules/site_export.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [cli_declarations](../modules/cli_declarations.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [knowledge_consumption](../modules/knowledge_consumption.md) |
| Outbound | [knowledge_model](../modules/knowledge_model.md) |
| Outbound | [knowledge_projection](../modules/knowledge_projection.md) |
| Outbound | [site_export](../modules/site_export.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_print_report` | `(report, output_format: str, *, action: str) -> None` | — | — |
| `_hub_requested` | `(args) -> bool` | — | — |
| `_validate_hub_args` | `(args) -> tuple[str \| None, list[str]]` | — | — |
| `_knowledge_metadata` | `(args) -> str \| None` | — | — |
| `_load_knowledge_projection` | `(wiki_dir: str, args) -> KnowledgeProjection \| None` | — | — |
| `_load_hub_knowledge_projections` | `(*, wiki_root: str \| None, wikis: list[str], args) -> dict[str, KnowledgeProjection] \| None` | — | — |
| `run` | `(args) -> None` | — | — |
