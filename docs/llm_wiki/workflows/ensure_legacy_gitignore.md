# ensure_legacy_gitignore

**Entry point:** `migrate_cmd._ensure_legacy_gitignore`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [migrate_cmd](../modules/migrate_cmd.md), [source_snapshot](../modules/source_snapshot.md)

> Ensure migration archives are ignored by git.

Returns True when a write was needed, including dry-run previews.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.source_snapshot_matches_current_files`
2. `source_snapshot.SourceSnapshotMutationError`
3. `knowledge_storage_io.read_guarded`
4. `source_snapshot.SourceSnapshotMutationError`
5. `knowledge_evidence.sha256_bytes`
6. `source_snapshot.SourceSnapshotMutationError`
7. `source_snapshot.SourceFileIntegrity`
8. `source_snapshot.SourceSnapshotMutationError`
9. `filesystem_guard.atomic_write_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [migrate_cmd](../modules/migrate_cmd.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `migrate_cmd._ensure_legacy_gitignore`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
