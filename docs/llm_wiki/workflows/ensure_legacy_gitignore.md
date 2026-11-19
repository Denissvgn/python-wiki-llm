# ensure_legacy_gitignore

**Entry point:** `migrate_runtime._ensure_legacy_gitignore`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [filesystem_guard](../modules/filesystem_guard.md), [host](../modules/host.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [migrate_runtime](../modules/migrate_runtime.md), [source_snapshot](../modules/source_snapshot.md)

> Ensure migration archives are ignored by git.

Returns True when a write was needed, including dry-run previews.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.source_snapshot_matches_current_files`
2. `source_snapshot.SourceSnapshotMutationError`
3. `knowledge_storage_io.read_guarded`
4. `host.emit`
5. `source_snapshot.SourceSnapshotMutationError`
6. `canonical_json.sha256_digest`
7. `source_snapshot.SourceSnapshotMutationError`
8. `source_snapshot.SourceFileIntegrity`
9. `source_snapshot.SourceSnapshotMutationError`
10. `filesystem_guard.atomic_write_guarded_bytes`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [host](../modules/host.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [migrate_runtime](../modules/migrate_runtime.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `migrate_runtime._ensure_legacy_gitignore`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
