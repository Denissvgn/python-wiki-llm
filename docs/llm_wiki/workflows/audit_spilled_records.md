# audit_spilled_records

**Entry point:** `knowledge_audit.audit_spilled_records`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_audit](../modules/knowledge_audit.md), [knowledge_storage](../modules/knowledge_storage.md), [storage_sort](../modules/storage_sort.md)

> Complete exact membership comparison with bounded private merge runs.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `storage_sort.SortedRuns`
2. `storage_sort.SortedRuns`
3. `canonical_json.sha256_digest`
4. `knowledge_storage.canonical_bytes`
5. `canonical_json.sha256_digest`
6. `knowledge_storage.canonical_bytes`
7. `knowledge_storage.KnowledgeStorageError`
8. `knowledge_storage.KnowledgeStorageError`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_audit](../modules/knowledge_audit.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [storage_sort](../modules/storage_sort.md)

## Behavior

This workflow starts at `knowledge_audit.audit_spilled_records`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
