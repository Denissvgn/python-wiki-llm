# advance_owned_ignore_snapshot

**Entry point:** `migrate_cmd._advance_owned_ignore_snapshot`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [migrate_cmd](../modules/migrate_cmd.md), [source_snapshot](../modules/source_snapshot.md)

> Admit one exact owned control write without absorbing source changes.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.build_source_snapshot`
2. `source_snapshot.SourceSnapshotMutationError`
3. `source_snapshot.SourceSnapshotMutationError`
4. `knowledge_evidence.sha256_bytes`
5. `knowledge_storage_io.read_guarded`
6. `source_snapshot.SourceSnapshotMutationError`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [migrate_cmd](../modules/migrate_cmd.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `migrate_cmd._advance_owned_ignore_snapshot`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
