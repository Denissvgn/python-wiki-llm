# sync_reuse_input_basis

**Entry point:** `sync_cmd._sync_reuse_input_basis`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [knowledge_envelope](../modules/knowledge_envelope.md), [source_snapshot](../modules/source_snapshot.md), [sync_cmd](../modules/sync_cmd.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_envelope.RepositoryEvidence`
2. `source_snapshot.SourceSnapshot`
3. `sync_manifest.SyncManifest`
4. `extraction_service.InventoryResult`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `sync_cmd._sync_reuse_input_basis`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
