# upgrade_current_knowledge

**Entry point:** `current_contracts.upgrade_current_knowledge`
**Modules involved:** [current_contracts](../modules/current_contracts.md), [filesystem_guard](../modules/filesystem_guard.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_service](../modules/maintenance_service.md), [manifest_storage](../modules/manifest_storage.md), [wiki_lifecycle](../modules/wiki_lifecycle.md)

> Use existing guarded writers and recovery copies; never repair bad authority.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `maintenance_protocol.load_adoption_marker`
3. `maintenance_protocol.guard_maintenance_owner`
4. `wiki_lifecycle.is_pristine_wiki_target`
5. `knowledge_artifacts.current_knowledge_format`
6. `manifest_storage.current_manifest_format`
7. `knowledge_storage_lifecycle._committed_inputs`
8. `filesystem_guard.ensure_guarded_directory`
9. `knowledge_storage_io._absolute_path`
10. `knowledge_consumption.load_knowledge_read_view`
11. `maintenance_protocol.save_recovery_snapshot`
12. `maintenance_protocol.snapshot_wiki`
13. `knowledge_storage_lifecycle._committed_inputs`
14. `maintenance_service.adopt_maintenance_authority`
15. `knowledge_artifacts.current_knowledge_format`
16. `knowledge_storage_lifecycle.migrate_knowledge_storage`
17. `manifest_storage.current_manifest_format`
18. `knowledge_storage_lifecycle.migrate_knowledge_storage`
19. `knowledge_storage_lifecycle._committed_inputs`

## Touches

- [current_contracts](../modules/current_contracts.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_service](../modules/maintenance_service.md)
- [manifest_storage](../modules/manifest_storage.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Behavior

This workflow starts at `current_contracts.upgrade_current_knowledge`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
