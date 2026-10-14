# adopt_maintenance_authority

**Entry point:** `maintenance_service.adopt_maintenance_authority`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_evidence](../modules/maintenance_evidence.md), [maintenance_projection](../modules/maintenance_projection.md), [maintenance_protocol](../modules/maintenance_protocol.md), [maintenance_service](../modules/maintenance_service.md), [maintenance_state](../modules/maintenance_state.md), [source_snapshot](../modules/source_snapshot.md)

> Explicitly adopt durable unreviewed authority without editing Markdown.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io._absolute_path`
3. `maintenance_protocol.governance_writer_lock`
4. `maintenance_protocol.storage_writer_lock`
5. `maintenance_protocol.load_adoption_marker`
6. `maintenance_protocol.guard_maintenance_owner`
7. `maintenance_protocol.guard_maintenance_owner`
8. `maintenance_protocol.snapshot_wiki`
9. `maintenance_protocol.MaintenanceProtocolError`
10. `maintenance_protocol.MaintenanceProtocolError`
11. `source_snapshot.source_snapshot_matches_current_files`
12. `maintenance_protocol.MaintenanceProtocolError`
13. `maintenance_state.new_identity`
14. `maintenance_evidence.reconcile_pending_maintenance`
15. `maintenance_projection.project_maintenance_knowledge`
16. `knowledge_artifacts.validated_artifact_bytes`
17. `knowledge_artifacts.build_knowledge_commit_plan`
18. `maintenance_protocol.save_recovery_snapshot`
19. `maintenance_protocol.save_recovery_snapshot`
20. `filesystem_guard.ensure_guarded_directory`
21. `filesystem_guard.atomic_write_guarded_bytes`
22. `knowledge_storage.canonical_bytes`
23. `source_snapshot.source_snapshot_matches_current_files`
24. `maintenance_protocol.MaintenanceProtocolError`
25. `knowledge_artifacts.commit_knowledge_artifacts`
26. `maintenance_protocol.save_recovery_snapshot`
27. `maintenance_protocol.snapshot_wiki`
28. `knowledge_storage.digest`
29. `knowledge_storage.canonical_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [maintenance_service](../modules/maintenance_service.md)
- [maintenance_state](../modules/maintenance_state.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `maintenance_service.adopt_maintenance_authority`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
