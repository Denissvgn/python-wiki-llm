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
9. `maintenance_state.new_identity`
10. `maintenance_evidence.reconcile_pending_maintenance`
11. `maintenance_projection.project_maintenance_knowledge`
12. `knowledge_artifacts.validated_artifact_bytes`
13. `knowledge_artifacts.build_knowledge_commit_plan`
14. `maintenance_protocol.save_recovery_snapshot`
15. `maintenance_protocol.save_recovery_snapshot`
16. `filesystem_guard.ensure_guarded_directory`
17. `filesystem_guard.atomic_write_guarded_bytes`
18. `knowledge_storage.canonical_bytes`
19. `source_snapshot.source_snapshot_matches_current_files`
20. `maintenance_protocol.MaintenanceProtocolError`
21. `knowledge_artifacts.commit_knowledge_artifacts`
22. `maintenance_protocol.save_recovery_snapshot`
23. `maintenance_protocol.snapshot_wiki`
24. `knowledge_storage.digest`
25. `knowledge_storage.canonical_bytes`

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
