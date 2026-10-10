# get_maintenance_status_authority

**Entry point:** `maintenance_service.get_maintenance_status_authority`
**Modules involved:** [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_service](../modules/maintenance_service.md), [maintenance_status](../modules/maintenance_status.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md)

> Read current ordinary-review needs without publishing observations/history.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `maintenance_protocol.snapshot_wiki`
3. `maintenance_protocol.guard_maintenance_owner`
4. `sync_manifest.SyncManifest.load`
5. `knowledge_orchestration.capture_committed_knowledge`
6. `maintenance_status.build_maintenance_status`
7. `maintenance_protocol.MaintenanceProtocolError`
8. `maintenance_status.build_maintenance_status`
9. `source_snapshot.source_snapshot_matches_current_files`
10. `maintenance_protocol.MaintenanceProtocolError`
11. `maintenance_protocol.snapshot_wiki`
12. `maintenance_protocol.MaintenanceProtocolError`
13. `maintenance_protocol.MaintenanceProtocolError`

## Touches

- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_status](../modules/maintenance_status.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `maintenance_service.get_maintenance_status_authority`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
