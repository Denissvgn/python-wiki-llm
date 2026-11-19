# expected_records

**Entry point:** `knowledge_audit.expected_records`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_audit](../modules/knowledge_audit.md), [knowledge_storage](../modules/knowledge_storage.md), [storage_sort](../modules/storage_sort.md)

> Derive record identities, owners and aliases from logical facts.

Partitioning, tree construction, pack writing and supplied lookup rows are
deliberately absent. Only the shared reversible value codec is reused.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage._Encoder`
2. `storage_sort.SortedRuns`
3. `knowledge_storage._owner`
4. `knowledge_storage._owner`
5. `knowledge_storage._owner`
6. `knowledge_storage._concept_aliases`
7. `knowledge_storage._Encoder.encode`
8. `canonical_json.sha256_digest`
9. `knowledge_storage.canonical_bytes`
10. `knowledge_storage._text`
11. `knowledge_storage._node_aliases`
12. `knowledge_storage._node_aliases`
13. `knowledge_storage._text`
14. `knowledge_storage._node_aliases`
15. `knowledge_storage.KnowledgeStorageError`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_audit](../modules/knowledge_audit.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [storage_sort](../modules/storage_sort.md)

## Behavior

This workflow starts at `knowledge_audit.expected_records`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
