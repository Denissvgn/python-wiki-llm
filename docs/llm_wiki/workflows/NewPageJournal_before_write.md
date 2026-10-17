# NewPageJournal_before_write

**Entry point:** `sync_recovery.NewPageJournal.before_write`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [sync_recovery](../modules/sync_recovery.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io.read_guarded`
3. `knowledge_storage.digest`
4. `knowledge_storage.digest`
5. `knowledge_storage_io.read_guarded`
6. `filesystem_guard.atomic_write_guarded_bytes`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [sync_recovery](../modules/sync_recovery.md)

## Behavior

Ignores writes outside the wiki and preexisting or previously owned pages.
For a genuinely new Markdown target, checks source ownership and resource bounds,
persists the intended postimage commitment and saves exact bytes before allowing
the underlying write. A repeated write must match this operation's previously
completed file identity; unrelated occupied pages are refused.
