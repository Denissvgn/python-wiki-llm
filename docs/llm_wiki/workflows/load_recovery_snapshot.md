# load_recovery_snapshot

**Entry point:** `maintenance_service._load_recovery_snapshot`
**Modules involved:** [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_projection](../modules/maintenance_projection.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_service](../modules/maintenance_service.md), [maintenance_state](../modules/maintenance_state.md), [sync_manifest](../modules/sync_manifest.md), [validation](../modules/validation.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io.read_guarded`
3. `maintenance_protocol.MaintenanceProtocolError`
4. `maintenance_protocol.MaintenanceProtocolError`
5. `maintenance_protocol.MaintenanceProtocolError`
6. `validation.is_portable_relative_path`
7. `maintenance_protocol.MaintenanceProtocolError`
8. `knowledge_storage_io.read_guarded`
9. `knowledge_storage.digest`
10. `maintenance_protocol.MaintenanceProtocolError`
11. `maintenance_protocol.MaintenanceProtocolError`
12. `maintenance_state.validate_maintenance_adoption`
13. `knowledge_storage.canonical_bytes`
14. `maintenance_protocol.MaintenanceProtocolError`
15. `maintenance_protocol.MaintenanceProtocolError`
16. `sync_manifest.SyncManifest.from_payload`
17. `knowledge_artifacts.validate_knowledge_artifacts`
18. `maintenance_projection.validate_maintenance_projection`
19. `knowledge_storage.digest`
20. `maintenance_protocol.MaintenanceProtocolError`
21. `maintenance_protocol.MaintenanceProtocolError`
22. `knowledge_storage.digest`
23. `maintenance_protocol.MaintenanceProtocolError`
24. `knowledge_governance.validate_governance_projection`
25. `knowledge_governance.parse_governance_ledger`
26. `knowledge_storage.digest`
27. `io.decode_markdown_bytes`
28. `maintenance_protocol.MaintenanceProtocolError`

## Touches

- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_state](../modules/maintenance_state.md)
- [sync_manifest](../modules/sync_manifest.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `maintenance_service._load_recovery_snapshot`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
