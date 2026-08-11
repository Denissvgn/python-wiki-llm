# init_cmd Module

**Path:** `src/llm_wiki_cli/commands/init_cmd.py`

## Description

_Auto-generated from `src/llm_wiki_cli/commands/init_cmd.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `AgentConfigState`, `CLI_AGENTS`, `DEFAULT_WIKI_DIR`, `config_requires_manual_recovery`, `get_agent_config_path`, `inspect_config`, `require_committed_config`, `require_config_inspection_unchanged`, `require_safe_config_path`, `validate_path`, `write_config` |
| `..services.filesystem_guard` | `atomic_write_guarded_bytes`, `ensure_guarded_directory`, `unlink_guarded_bytes` |
| `..services.rendering_lifecycle` | `reference_recovery_command`, `select_render_profile` |
| `..services.schema` | `CONSTRAINT_START`, `SCHEMA_FILENAMES`, `ManagedSchemaBlockError`, `ManagedSchemaBlockState`, `ManagedSchemaPathError`, `SchemaRenderProfile`, `build_schema_content`, `classify_managed_schema_block`, `decode_managed_document_bytes`, `encode_managed_document_text`, `replace_schema_block_content`, `require_managed_schema_profile`, `require_replaceable_managed_schema`, `require_safe_schema_path` |
| `..services.skills` | `REFERENCE_SKILL_ID`, `ReferenceSkillState`, `_provision_reference_skill_guarded`, `list_bundled_skills`, `skills_install_dir`, `verify_reference_skill` |
| `..services.source_selection` | `SourceSelectionError`, `resolve_source_selection` |
| `..services.wiki_lifecycle` | `WikiScaffoldPathError`, `provision_wiki_scaffold`, `require_safe_wiki_scaffold` |
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
    n3["src/llm_wiki_cli/services/filesystem_guard.py"]
    n4["src/llm_wiki_cli/services/rendering_lifecycle.py"]
    n5["src/llm_wiki_cli/services/schema.py"]
    n6["src/llm_wiki_cli/services/skills.py"]
    n7["src/llm_wiki_cli/services/source_selection.py"]
    n8["src/llm_wiki_cli/services/wiki_lifecycle.py"]
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
    n4 --> n5
    n4 --> n6
    n5 --> n6
    n7 --> n2
    n8 --> n2
    n8 --> n3
    n8 --> n4
    n8 --> n5
    click n0 "../modules/cli.md"
    click n1 "../modules/init_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/filesystem_guard.md"
    click n4 "../modules/rendering_lifecycle.md"
    click n5 "../modules/services_schema.md"
    click n6 "../modules/skills.md"
    click n7 "../modules/source_selection.md"
    click n8 "../modules/wiki_lifecycle.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [rendering_lifecycle](../modules/rendering_lifecycle.md) |
| Outbound | [services_schema](../modules/services_schema.md) |
| Outbound | [skills](../modules/skills.md) |
| Outbound | [source_selection](../modules/source_selection.md) |
| Outbound | [wiki_lifecycle](../modules/wiki_lifecycle.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_managed_schema_agents` | `() -> tuple[str, ...]` | — | Return agents with one safely readable managed schema in the checkout. |
| `run` | `(args)` | — | — |
