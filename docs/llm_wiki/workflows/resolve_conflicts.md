# resolve_conflicts

**Entry point:** `team.resolve_conflicts`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md), [team](../modules/team.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.resolve_source_selection`
2. `sync_manifest.SyncManifest.load`
3. `io.read_md`
4. `source_selection.SourceSelectionError`
5. `source_selection.validate_persisted_source_selection_identity`
6. `source_snapshot.capture_source_selection_inputs`
7. `source_selection.validate_persisted_source_selection_identity`
8. `source_snapshot.build_source_snapshot`
9. `source_selection.validate_persisted_source_selection_identity`
10. `knowledge_storage_lifecycle.is_storage_path`
11. `io.decode_markdown_bytes`
12. `extraction_service.get_inventory_result`
13. `extraction_service.ExtractorFailureError`
14. `io.decode_markdown_bytes`
15. `filesystem_guard.atomic_write_guarded_bytes`
16. `knowledge_storage_io._absolute_path`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)
- [team](../modules/team.md)

## Behavior

This workflow starts at `team.resolve_conflicts`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
