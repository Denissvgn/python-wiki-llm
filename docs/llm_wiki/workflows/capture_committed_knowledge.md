# capture_committed_knowledge

**Entry point:** `knowledge_orchestration.capture_committed_knowledge`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [maintenance_protocol](../modules/maintenance_protocol.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_protocol.guard_maintenance_owner`
2. `sync_manifest.SyncManifest.from_payload`
3. `knowledge_artifacts._decode_json_object`
4. `knowledge_artifacts.KnowledgeArtifactError`
5. `knowledge_artifacts.validate_knowledge_artifacts`
6. `knowledge_artifacts.KnowledgeArtifactError`
7. `knowledge_artifacts.KnowledgeArtifactError`
8. `knowledge_artifacts.KnowledgeArtifactError`
9. `immutable.freeze`

## Touches

- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `knowledge_orchestration.capture_committed_knowledge`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
