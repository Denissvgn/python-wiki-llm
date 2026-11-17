# save_migration_progress

**Entry point:** `migrate_runtime._save_migration_progress`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [migrate_runtime](../modules/migrate_runtime.md)

> Atomically persist exact evidence receipts before a chunk can return.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_evidence.is_valid_sha256`
2. `io.read_md`
3. `canonical_json.sha256_digest`
4. `io.write_json_atomic`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [migrate_runtime](../modules/migrate_runtime.md)

## Behavior

This workflow starts at `migrate_runtime._save_migration_progress`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
