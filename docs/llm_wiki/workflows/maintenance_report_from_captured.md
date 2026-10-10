# maintenance_report_from_captured

**Entry point:** `maintenance_service.maintenance_report_from_captured`
**Modules involved:** [knowledge_orchestration](../modules/knowledge_orchestration.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_service](../modules/maintenance_service.md), [maintenance_status](../modules/maintenance_status.md), [python_implementation](../modules/python_implementation.md), [sync_manifest](../modules/sync_manifest.md)

> Reuse one captured inventory; never extract again to decorate a read.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.load`
2. `maintenance_protocol.guard_maintenance_owner`
3. `knowledge_orchestration.capture_committed_knowledge`
4. `maintenance_protocol.guard_maintenance_owner`
5. `maintenance_protocol.snapshot_wiki`
6. `maintenance_status.build_maintenance_status`
7. `python_implementation.analysis_identity`

## Touches

- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_status](../modules/maintenance_status.md)
- [python_implementation](../modules/python_implementation.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `maintenance_service.maintenance_report_from_captured`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
