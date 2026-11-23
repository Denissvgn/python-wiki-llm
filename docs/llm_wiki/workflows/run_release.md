# run_release

**Entry point:** `historical_release.run_release`
**Modules involved:** [historical_release](../modules/historical_release.md), [io](../modules/io.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [source_retirement](../modules/source_retirement.md), [sync_manifest](../modules/sync_manifest.md), [wiki_surface](../modules/wiki_surface.md)

> Plan and publish one manifest-last release. Source changes are deliberately deferred.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.load`
2. `knowledge_orchestration.capture_committed_knowledge`
3. `source_retirement.SourceRetirementError`
4. `source_retirement.SourceRetirementError`
5. `wiki_surface.collect_wiki_pages`
6. `source_retirement.SourceRetirementError`
7. `io.decode_markdown_bytes`
8. `knowledge_envelope.hash_markdown_snapshot`
9. `source_retirement.SourceRetirementError`
10. `source_retirement.SourceRetirementError`
11. `knowledge_artifacts.validated_artifact_bytes`
12. `knowledge_artifacts.build_knowledge_commit_plan`
13. `maintenance_protocol.guard_maintenance_owner`
14. `source_retirement.SourceRetirementError`
15. `io.write_bytes_atomic`
16. `knowledge_artifacts.commit_knowledge_artifacts`
17. `knowledge_storage_io.read_guarded`
18. `knowledge_storage_io.read_guarded`
19. `io.write_bytes_atomic`
20. `knowledge_storage_io.read_guarded`
21. `io.write_bytes_atomic`
22. `knowledge_artifacts.commit_knowledge_artifacts`

## Touches

- [historical_release](../modules/historical_release.md)
- [io](../modules/io.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [source_retirement](../modules/source_retirement.md)
- [sync_manifest](../modules/sync_manifest.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `historical_release.run_release`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
