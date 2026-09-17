# SyncManifest_save

**Entry point:** `sync_manifest.SyncManifest.save`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [manifest_storage](../modules/manifest_storage.md), [sync_manifest](../modules/sync_manifest.md)

> Atomically write the manifest through the shared JSON boundary.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `manifest_storage.current_manifest_format`
2. `manifest_storage.build_manifest_store`
3. `knowledge_governance.governance_lock`
4. `filesystem_guard.ensure_guarded_directory`
5. `knowledge_storage_io.read_guarded`
6. `knowledge_storage.KnowledgeStorageError`
7. `filesystem_guard.atomic_write_guarded_bytes`
8. `knowledge_storage_io.read_guarded`
9. `filesystem_guard.atomic_write_guarded_bytes`
10. `io.write_json_atomic`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [manifest_storage](../modules/manifest_storage.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `sync_manifest.SyncManifest.save`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
