# reference_cmd_flow

**Entry point:** `reference_cmd.run`
**Modules involved:** [cli_reference](../modules/cli_reference.md), [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [reference_cmd](../modules/reference_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `cli_reference.load_cli_contract`
2. `cli_reference.get_cli_contract`
3. `cli_reference.render_cli_reference`
4. `knowledge_storage_io._absolute_path`
5. `knowledge_storage_io._absolute_path`
6. `knowledge_storage_io.StorageReadSession`
7. `filesystem_guard.ensure_guarded_directory`
8. `filesystem_guard.atomic_write_private_bytes`

## Touches

- [cli_reference](../modules/cli_reference.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [reference_cmd](../modules/reference_cmd.md)

## Behavior

This workflow starts at `reference_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
