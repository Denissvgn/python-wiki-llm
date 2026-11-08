# write

**Entry point:** `publication_cmd._write`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication_cmd](../modules/publication_cmd.md), [publication_config](../modules/publication_config.md), [publication_impact](../modules/publication_impact.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot._is_package_marker`
2. `knowledge_storage_io._absolute_path`
3. `publication_config.load_publication_config`
4. `publication_config.publication_input_controls`
5. `publication_config.publication_control_overlap`
6. `publication_config.publication_control_overlap`
7. `publication_config.publication_control_overlap`
8. `publication_config.publication_control_overlap`
9. `knowledge_storage_io.StorageReadSession`
10. `publication_impact.read_publication_document`
11. `filesystem_guard.ensure_guarded_directory`
12. `filesystem_guard.atomic_write_private_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication_cmd](../modules/publication_cmd.md)
- [publication_config](../modules/publication_config.md)
- [publication_impact](../modules/publication_impact.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `publication_cmd._write`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
