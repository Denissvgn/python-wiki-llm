# review_storage

**Entry point:** `knowledge_storage_diagnostics.review_storage`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_access](../modules/knowledge_storage_access.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md), [knowledge_storage_io](../modules/knowledge_storage_io.md)

> Page logical snapshots or recover an exact row under the same output bounds.

Each call repeats its original validation/materialization scope. Continuations
bind snapshot commitments, native locations, operation and canonical ordering;
they are consistency checks, not authorization or live-source freshness proof.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage.KnowledgeStorageError`
2. `knowledge_storage.KnowledgeStorageError`
3. `knowledge_storage.KnowledgeStorageError`
4. `knowledge_storage_access.capture_knowledge_slice`
5. `knowledge_storage_io._absolute_path`
6. `knowledge_storage.canonical_bytes`
7. `knowledge_storage.canonical_bytes`
8. `knowledge_storage.digest`
9. `knowledge_storage.canonical_bytes`
10. `knowledge_storage.KnowledgeStorageError`
11. `knowledge_storage.KnowledgeStorageError`
12. `knowledge_storage.canonical_bytes`
13. `knowledge_storage.digest`
14. `knowledge_storage.canonical_bytes`
15. `knowledge_storage.canonical_bytes`
16. `knowledge_storage.KnowledgeStorageError`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_access](../modules/knowledge_storage_access.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)

## Behavior

Validates the requested bounds before reading logical snapshots. Full inspection and comparison use the committed loader; explicit selected inspection captures only its declared selected-record/policy scope and finishes its authoritative recheck before returning. Comparison preserves canonical JSON type distinctions and orders changed keys, including duplicate relationship occurrences.

The review identity binds the snapshots, native root locations, operation, selection and validation policy. Continuation rejects a changed binding. Each page reports its ordinal offset, global total, records outside the page and records still ahead; enumeration completion does not approve earlier pages or omitted values. Exact-record requests require the review identity and ordinal, and deliver base64 chunks of the canonical complete row with byte offsets, size and SHA-256. A caller reconstructs and verifies those bytes before treating an oversized value or identity as reviewed. Readers repeat validation/materialization, never migrate or write snapshots, and establish no live-source freshness.
