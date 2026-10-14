# current_contracts Module

**Path:** `src/llm_wiki_cli/services/current_contracts.py`

## Description

The library selects current task and view contracts and native storage during authorized setup. New data uses compressed packed knowledge and indexed ordinary maintenance ownership. Upgrade preserves validated recovery preimages and source/wiki content, rejects damaged authority, and keeps human review separate from ordinary pending maintenance. Read-only consumption never upgrades files.


Setup distinguishes untouched scaffolds from established canonical wikis and incomplete authority. Missing adopted or governed data requires complete recovery; a current format label does not establish source freshness or prose approval. Older canonical layouts are seeded by the owning command with complete preimages, while selected-source scaffolds remain first-use targets.

## Imports

| Source | Symbols |
|--------|---------|
| `.filesystem_guard` | `ensure_guarded_directory` |
| `.knowledge_artifacts` | `current_knowledge_format` |
| `.knowledge_consumption` | `load_knowledge_read_view` |
| `.knowledge_storage_lifecycle` | `_committed_inputs`, `migrate_knowledge_storage`, `_absolute_path` |
| `.maintenance_protocol` | `load_adoption_marker`, `guard_maintenance_owner`, `snapshot_wiki`, `save_recovery_snapshot` |
| `.maintenance_service` | `adopt_maintenance_authority` |
| `.manifest_storage` | `current_manifest_format` |
| `.wiki_lifecycle` | `is_pristine_wiki_target` |
| `__future__` | `annotations` |
| `hashlib` | `hashlib` |
| `json` | `json` |
| `pathlib` | `Path` |
| `tempfile` | `tempfile` |

## Local dependency map

<!-- Auto-generated local dependency summary. Do not edit by hand. -->
```mermaid
flowchart LR
    n0["src/llm_wiki_cli/commands/init_cmd.py"]
    n1["src/llm_wiki_cli/commands/upgrade_cmd.py"]
    n2["src/llm_wiki_cli/services/bootstrap_runtime.py"]
    n3["src/llm_wiki_cli/services/current_contracts.py"]
    n4["src/llm_wiki_cli/services/filesystem_guard.py"]
    n5["src/llm_wiki_cli/services/knowledge_artifacts.py"]
    n6["src/llm_wiki_cli/services/knowledge_consumption.py"]
    n7["src/llm_wiki_cli/services/knowledge_storage_lifecycle.py"]
    n8["src/llm_wiki_cli/services/maintenance_protocol.py"]
    n9["src/llm_wiki_cli/services/maintenance_service.py"]
    n10["src/llm_wiki_cli/services/manifest_storage.py"]
    n11["src/llm_wiki_cli/services/wiki_lifecycle.py"]
    n0 --> n1
    n0 --> n3
    n0 --> n4
    n0 --> n11
    n1 --> n3
    n1 --> n4
    n1 --> n11
    n2 --> n3
    n2 --> n5
    n2 --> n6
    n2 --> n8
    n2 --> n11
    n3 --> n4
    n3 --> n5
    n3 --> n6
    n3 --> n7
    n3 --> n8
    n3 --> n9
    n3 --> n10
    n3 --> n11
    n5 --> n4
    n5 --> n8
    n5 --> n10
    n6 --> n5
    n7 --> n4
    n7 --> n5
    n7 --> n8
    n7 --> n10
    n8 --> n4
    n9 --> n4
    n9 --> n5
    n9 --> n8
    n10 --> n5
    n11 --> n3
    n11 --> n4
    click n0 "../modules/init_cmd.md"
    click n1 "../modules/upgrade_cmd.md"
    click n2 "../modules/bootstrap_runtime.md"
    click n3 "../modules/current_contracts.md"
    click n4 "../modules/filesystem_guard.md"
    click n5 "../modules/knowledge_artifacts.md"
    click n6 "../modules/knowledge_consumption.md"
    click n7 "../modules/knowledge_storage_lifecycle.md"
    click n8 "../modules/maintenance_protocol.md"
    click n9 "../modules/maintenance_service.md"
    click n10 "../modules/manifest_storage.md"
    click n11 "../modules/wiki_lifecycle.md"
```

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | [init_cmd](../modules/init_cmd.md) |
| Inbound | [upgrade_cmd](../modules/upgrade_cmd.md) |
| Inbound | [bootstrap_runtime](../modules/bootstrap_runtime.md) |
| Inbound | [wiki_lifecycle](../modules/wiki_lifecycle.md) |
| Outbound | [filesystem_guard](../modules/filesystem_guard.md) |
| Outbound | [knowledge_artifacts](../modules/knowledge_artifacts.md) |
| Outbound | [knowledge_consumption](../modules/knowledge_consumption.md) |
| Outbound | [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md) |
| Outbound | [maintenance_protocol](../modules/maintenance_protocol.md) |
| Outbound | [maintenance_service](../modules/maintenance_service.md) |
| Outbound | [manifest_storage](../modules/manifest_storage.md) |
| Outbound | [wiki_lifecycle](../modules/wiki_lifecycle.md) |

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `current_contract_defaults` | `() -> dict` | — | Return detached installation policy; callers do not elect wire versions. |
| `upgrade_current_knowledge` | `(src_dir, wiki_dir, *, helper_cache_dir = None, source_selection = None, allow_external_src = False, _captured = None, _seed_legacy = None) -> dict` | — | Use existing guarded writers and recovery copies; never repair bad authority. |