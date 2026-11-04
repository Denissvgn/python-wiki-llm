# load_recovery_snapshot

**Entry point:** `maintenance_service._load_recovery_snapshot`
**Modules involved:** [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_projection](../modules/maintenance_projection.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_recovery](../modules/maintenance_recovery.md), [maintenance_service](../modules/maintenance_service.md), [maintenance_state](../modules/maintenance_state.md), [sync_manifest](../modules/sync_manifest.md), [validation](../modules/validation.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io.read_guarded`
3. `maintenance_protocol.MaintenanceProtocolError`
4. `maintenance_protocol.MaintenanceProtocolError`
5. `maintenance_protocol.MaintenanceProtocolError`
6. `maintenance_recovery.load_recovery_catalog`
7. `validation.is_portable_relative_path`
8. `maintenance_protocol.MaintenanceProtocolError`
9. `knowledge_storage_io.read_guarded`
10. `knowledge_storage.digest`
11. `maintenance_protocol.MaintenanceProtocolError`
12. `maintenance_protocol.MaintenanceProtocolError`
13. `maintenance_state.validate_maintenance_adoption`
14. `knowledge_storage.canonical_bytes`
15. `maintenance_protocol.MaintenanceProtocolError`
16. `maintenance_protocol.MaintenanceProtocolError`
17. `sync_manifest.SyncManifest.from_payload`
18. `knowledge_artifacts.validate_knowledge_artifacts`
19. `maintenance_projection.validate_maintenance_projection`
20. `knowledge_storage.digest`
21. `maintenance_protocol.MaintenanceProtocolError`
22. `maintenance_protocol.MaintenanceProtocolError`
23. `knowledge_storage.digest`
24. `maintenance_protocol.MaintenanceProtocolError`
25. `knowledge_governance.validate_governance_projection`
26. `knowledge_governance.parse_governance_ledger`
27. `knowledge_storage.digest`
28. `io.decode_markdown_bytes`
29. `maintenance_protocol.MaintenanceProtocolError`

## Touches

- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_recovery](../modules/maintenance_recovery.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_state](../modules/maintenance_state.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `maintenance_service._load_recovery_snapshot`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
