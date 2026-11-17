# validated_migration_progress_pages

**Entry point:** `migrate_runtime._validated_migration_progress_pages`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [io](../modules/io.md), [knowledge_evidence](../modules/knowledge_evidence.md), [migrate_runtime](../modules/migrate_runtime.md)

> Load durable receipts for pages written by an earlier migration chunk.

Receipts are only accepted when the exact current page bytes still match
the recorded write and the page also equals the current deterministic
migration output. This prevents a stale or edited receipt from promoting
retained Markdown to known evidence.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_evidence.is_valid_sha256`
2. `knowledge_evidence.is_valid_sha256`
3. `canonical_json.sha256_digest`
4. `io.read_md`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [io](../modules/io.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [migrate_runtime](../modules/migrate_runtime.md)

## Behavior

This workflow starts at `migrate_runtime._validated_migration_progress_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
