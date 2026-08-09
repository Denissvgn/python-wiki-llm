# uninstall_cmd Module

**Path:** `src/llm_wiki_cli/commands/uninstall_cmd.py`

## Description

_Auto-generated from `src/llm_wiki_cli/commands/uninstall_cmd.py`._

## Imports

| Source | Symbols |
|--------|---------|
| `..config` | `DEFAULT_WIKI_DIR`, `validate_path` |
| `..services.ci_installer` | `MANAGED_WORKFLOW_PATH`, `is_unmodified_managed_workflow` |
| `..services.io` | `first_unsafe_path_component`, `read_md`, `write_md` |
| `..services.schema` | `ALL_SCHEMA_FILES`, `CONSTRAINT_END`, `CONSTRAINT_START`, `strip_wiki_block` |
| `..services.skills` | `KNOWN_INSTALL_TARGETS`, `REFERENCE_SKILL_ID`, `reference_skill_state` |
| `pathlib` | `Path` |
| `shutil` | `shutil` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/cli.py"]
    n1["src/llm_wiki_cli/commands/uninstall_cmd.py"]
    n2["src/llm_wiki_cli/config.py"]
    n3["src/llm_wiki_cli/services/ci_installer.py"]
    n4["src/llm_wiki_cli/services/io.py"]
    n5["src/llm_wiki_cli/services/schema.py"]
    n6["src/llm_wiki_cli/services/skills.py"]
    n0 --> n1
    n0 --> n2
    n1 --> n2
    n1 --> n3
    n1 --> n4
    n1 --> n5
    n1 --> n6
    n2 --> n4
    n3 --> n4
    n5 --> n4
    n5 --> n6
    n6 --> n4
    click n0 "../modules/cli.md"
    click n1 "../modules/uninstall_cmd.md"
    click n2 "../modules/config.md"
    click n3 "../modules/ci_installer.md"
    click n4 "../modules/io.md"
    click n5 "../modules/services_schema.md"
    click n6 "../modules/skills.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [cli](../modules/cli.md) |
| Outbound | [config](../modules/config.md) |
| Outbound | [ci_installer](../modules/ci_installer.md) |
| Outbound | [io](../modules/io.md) |
| Outbound | [services_schema](../modules/services_schema.md) |
| Outbound | [skills](../modules/skills.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `_confirm` | `(prompt: str) -> bool` | — | Ask for y/n confirmation. |
| `_remove_hooks` | `(dry_run: bool = False) -> int` | — | Remove llm-wiki hooks, but only if they contain our signature. |
| `_clean_agent_schemas` | `(dry_run: bool = False) -> int` | — | Remove the LLM Wiki constraint block from agent schema files. |
| `_remove_wiki_dir` | `(wiki_dir: Path, dry_run: bool = False) -> bool` | — | Remove the wiki directory tree. |
| `_remove_reference_skill` | `(dry_run: bool = False) -> int` | — | Remove installed wiki-reference skill copies, but only unmodified ones. |
| `_remove_runtime_artifacts` | `(dry_run: bool = False) -> int` | — | Remove local runtime artifacts created by llm-wiki. |
| `_remove_ci_workflow` | `(dry_run: bool = False) -> int` | — | Remove the dedicated CI workflow only when its checksum proves ownership. |
| `run` | `(args)` | — | — |
