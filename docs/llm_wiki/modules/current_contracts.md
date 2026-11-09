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
    n0["src"]
    n1["src/llm_wiki_cli/services/current_contracts.py"]
    n0 --> n1
    n1 --> n0
    click n1 "../modules/current_contracts.md"
```

> Module-level dependencies exceed the generated-diagram limits, so the diagram and table below group them by top-level package. Counts report the number of module neighbors in each package.

### Internal neighbors

| Direction | Module |
|---|---|
| Inbound | `src` (5) |
| Outbound | `src` (8) |

> All 12 module neighbor(s) are summarized by package because the module-level view exceeds the 12-node limit.

## Functions

| Function | Signature | Decorators | Description |
|----------|-----------|------------|-------------|
| `current_contract_defaults` | `() -> dict` | — | Return detached installation policy; callers do not elect wire versions. |
| `upgrade_current_knowledge` | `(src_dir, wiki_dir, *, helper_cache_dir = None, source_selection = None, allow_external_src = False, _captured = None, _seed_legacy = None) -> dict` | — | Use existing guarded writers and recovery copies; never repair bad authority. |