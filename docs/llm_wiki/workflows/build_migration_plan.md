# build_migration_plan

**Entry point:** `migrate_cmd._build_migration_plan`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [extraction_service](../modules/extraction_service.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [migrate_cmd](../modules/migrate_cmd.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.load`
2. `source_selection.resolve_source_selection`
3. `source_selection.validate_persisted_source_selection_identity`
4. `source_snapshot.capture_source_selection_inputs`
5. `source_selection.validate_persisted_source_selection_identity`
6. `source_snapshot.build_source_snapshot`
7. `source_selection.validate_persisted_source_selection_identity`
8. `extraction_service.get_inventory_result`
9. `extraction_service.print_inventory_failures`
10. `extraction_service.get_docker_inventory`
11. `bootstrap_runtime.build_module_page_map`
12. `bootstrap_runtime.build_entity_occurrence_page_map`
13. `knowledge_orchestration.collect_runtime_repository_evidence`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [extraction_service](../modules/extraction_service.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [migrate_cmd](../modules/migrate_cmd.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `migrate_cmd._build_migration_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
