# capture_committed_knowledge

**Entry point:** `knowledge_orchestration.capture_committed_knowledge`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.from_payload`
2. `knowledge_artifacts._decode_json_object`
3. `knowledge_artifacts.KnowledgeArtifactError`
4. `knowledge_artifacts.validate_knowledge_artifacts`
5. `knowledge_artifacts.KnowledgeArtifactError`
6. `immutable.freeze`

## Touches

- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `knowledge_orchestration.capture_committed_knowledge`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
