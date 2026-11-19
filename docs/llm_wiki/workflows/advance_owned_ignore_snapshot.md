# advance_owned_ignore_snapshot

**Entry point:** `migrate_runtime._advance_owned_ignore_snapshot`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [migrate_runtime](../modules/migrate_runtime.md), [source_snapshot](../modules/source_snapshot.md)

> Admit one exact owned control write without absorbing source changes.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.build_source_snapshot`
2. `source_snapshot.SourceSnapshotMutationError`
3. `source_snapshot.SourceSnapshotMutationError`
4. `canonical_json.sha256_digest`
5. `knowledge_storage_io.read_guarded`
6. `source_snapshot.SourceSnapshotMutationError`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [migrate_runtime](../modules/migrate_runtime.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `migrate_runtime._advance_owned_ignore_snapshot`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
