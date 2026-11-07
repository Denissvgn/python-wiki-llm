# write

**Entry point:** `publication_cmd._write`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_cmd](../modules/publication_cmd.md), [publication_config](../modules/publication_config.md), [publication_impact](../modules/publication_impact.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `publication_config.load_publication_config`
3. `knowledge_storage_io.StorageReadSession`
4. `publication_impact.read_publication_document`
5. `filesystem_guard.ensure_guarded_directory`
6. `filesystem_guard.atomic_write_private_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_cmd](../modules/publication_cmd.md)
- [publication_config](../modules/publication_config.md)
- [publication_impact](../modules/publication_impact.md)

## Behavior

This workflow starts at `publication_cmd._write`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
