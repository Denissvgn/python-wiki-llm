# init_cmd Module

**Path:** `src/llm_wiki_cli/commands/init_cmd.py`

## Description

Creates or refreshes the wiki scaffold, managed agent instructions, and local
agent configuration after validating existing paths, configuration, source
selection, and agent ownership. Existing compatible preferences survive a
refresh; ambiguous or unsafe state requires recovery before writes proceed.

`--prepare-extractors` adds a setup step before provisioning. It prepares the
selected helper languages, reuses valid cached artifacts, and stops on failed
preparation before changing the scaffold or agent configuration. The flag is
specific to that invocation. `--helper-cache-dir` selects its cache and requires
the preparation flag; it does not become a saved analysis preference.

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `AgentConfigState`, `CLI_AGENTS`, `DEFAULT_WIKI_DIR`, `config_requires_manual_recovery`, `get_agent_config_path`, `inspect_config`, `require_committed_config`, `require_config_inspection_unchanged`, `require_safe_config_path`, `validate_path`, `write_config` |
| `..services.extractor_helpers` | `helper_preparation_failure_hint` |
| `..services.filesystem_guard` | `atomic_write_guarded_bytes`, `ensure_guarded_directory`, `unlink_guarded_bytes` |
| `..services.helper_preparation` | `ensure_source_helpers` |
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
    n3["src/llm_wiki_cli/services/extractor_helpers.py"]
    n4["src/llm_wiki_cli/services/filesystem_guard.py"]
    n5["src/llm_wiki_cli/services/helper_preparation.py"]
    n6["src/llm_wiki_cli/services/rendering_lifecycle.py"]
    n7["src/llm_wiki_cli/services/schema.py"]
    n8["src/llm_wiki_cli/services/skills.py"]
    n9["src/llm_wiki_cli/services/source_selection.py"]
    n10["src/llm_wiki_cli/services/wiki_lifecycle.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n1 --> n7
    n1 --> n8
    n1 --> n9
    n1 --> n10
    n2 --> n4
    n5 --> n3
    n6 --> n7
    n6 --> n8
    n7 --> n8
    n9 --> n2
    n10 --> n2
    n10 --> n4
    n10 --> n6
    n10 --> n7
    click n0 "../modules/cli.md"
    click n1 "../modules/init_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/extractor_helpers.md"
    click n4 "../modules/filesystem_guard.md"
    click n5 "../modules/helper_preparation.md"
    click n6 "../modules/rendering_lifecycle.md"
    click n7 "../modules/services_schema.md"
    click n8 "../modules/skills.md"
    click n9 "../modules/source_selection.md"
    click n10 "../modules/wiki_lifecycle.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [extractor_helpers](../modules/extractor_helpers.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [helper_preparation](../modules/helper_preparation.md) |
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
