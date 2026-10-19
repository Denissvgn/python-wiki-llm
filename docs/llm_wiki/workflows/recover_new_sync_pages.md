# recover_new_sync_pages

**Entry point:** `sync_recovery.recover_new_sync_pages`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_protocol](../modules/maintenance_protocol.md), [sync_manifest](../modules/sync_manifest.md), [sync_recovery](../modules/sync_recovery.md)

> Remove only unchanged transaction-created pages, preserving postimages.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io._absolute_path`
3. `knowledge_storage_io.read_guarded`
4. `knowledge_storage.digest`
5. `maintenance_protocol.governance_writer_lock`
6. `maintenance_protocol.storage_writer_lock`
7. `knowledge_storage_io.read_guarded`
8. `knowledge_storage.digest`
9. `knowledge_storage.digest`
10. `sync_manifest.SyncManifest.load`
11. `knowledge_storage_io.read_guarded`
12. `knowledge_storage.digest`
13. `knowledge_storage.digest`
14. `knowledge_storage_io.read_guarded`
15. `knowledge_storage_io._identity`
16. `filesystem_guard.fresh_no_follow_stat`
17. `filesystem_guard.fresh_no_follow_stat`
18. `knowledge_storage_io._identity`
19. `filesystem_guard.unlink_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_recovery](../modules/sync_recovery.md)

## Behavior

Requires the exact hash emitted by a rejected sync and the same physical wiki
root. Under governance and storage locks, validates the journal, source-selection
commitments and unchanged authority, then preflights every candidate against
committed owners, selected sources, captured identities and byte backups.
Preview returns that bounded list without deleting pages. Apply rechecks authority
and each candidate before a guarded content-matched unlink. A changed candidate
refuses recovery; an I/O failure reports partial progress and retains postimages.
Existing pages and authority are not restored. Rerun owning sync afterward.
