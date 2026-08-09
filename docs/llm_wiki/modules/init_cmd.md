# init_cmd Module

**Path:** `src/llm_wiki_cli/commands/init_cmd.py`

## Description

_Auto-generated from `src/llm_wiki_cli/commands/init_cmd.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `CLI_AGENTS`, `DEFAULT_WIKI_DIR`, `read_config`, `validate_path`, `write_config` |
| `..services.io` | `read_md`, `write_md` |
| `..services.schema` | `CONSTRAINT_START`, `SCHEMA_FILENAMES`, `build_schema_content`, `replace_schema_block` |
| `..services.skills` | `REFERENCE_SKILL_ID`, `SkillsError`, `install_reference_skill`, `list_bundled_skills` |
| `..services.source_selection` | `SourceSelectionError`, `resolve_source_selection` |
| `..services.wiki_scaffold` | `INITIAL_WIKI_INDEX_MARKDOWN`, `INITIAL_WIKI_LOG_MARKDOWN` |
| `..services.wiki_surface` | `iter_directory_kinds` |
| `__future__` | `annotations` |
| `pathlib` | `Path` |
| `shutil` | `shutil` |
| `sys` | `sys` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/init_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/io.py"]
    n4["src/llm_wiki_cli/services/schema.py"]
    n5["src/llm_wiki_cli/services/skills.py"]
    n6["src/llm_wiki_cli/services/source_selection.py"]
    n7["src/llm_wiki_cli/services/wiki_scaffold.py"]
    n8["src/llm_wiki_cli/services/wiki_surface.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n1 --> n7
    n1 --> n8
    n2 --> n3
    n4 --> n3
    n4 --> n5
    n5 --> n3
    n6 --> n2
    click n0 "../modules/cli.md"
    click n1 "../modules/init_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/io.md"
    click n4 "../modules/services_schema.md"
    click n5 "../modules/skills.md"
    click n6 "../modules/source_selection.md"
    click n7 "../modules/wiki_scaffold.md"
    click n8 "../modules/wiki_surface.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [services_schema](../modules/services_schema.md) |
| Outbound | [skills](../modules/skills.md) |
| Outbound | [source_selection](../modules/source_selection.md) |
| Outbound | [wiki_scaffold](../modules/wiki_scaffold.md) |
| Outbound | [wiki_surface](../modules/wiki_surface.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `run` | `(args)` | — | — |
