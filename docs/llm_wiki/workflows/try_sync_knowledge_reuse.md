# try_sync_knowledge_reuse

**Entry point:** `sync_cmd._try_sync_knowledge_reuse`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [progress](../modules/progress.md), [source_snapshot](../modules/source_snapshot.md), [sync_cmd](../modules/sync_cmd.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `progress.observed_phase`
2. `knowledge_envelope.RepositoryEvidence`
3. `knowledge_orchestration.CommittedKnowledgeState`
4. `source_snapshot.SourceSnapshot`
5. `sync_manifest.SyncManifest`
6. `extraction_service.InventoryResult`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [progress](../modules/progress.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `sync_cmd._try_sync_knowledge_reuse`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
