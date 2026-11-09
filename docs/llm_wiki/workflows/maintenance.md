# maintenance

**Entry point:** `publication_maintenance._maintenance`
**Modules involved:** [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [publication](../modules/publication.md), [publication_candidate](../modules/publication_candidate.md), [publication_maintenance](../modules/publication_maintenance.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage_io._absolute_path`
2. `knowledge_storage_io._absolute_path`
3. `publication_candidate.check_publication_candidate`
4. `knowledge_storage_io.StorageReadSession`
5. `knowledge_storage_io.StorageReadSession.read`
6. `knowledge_evidence.sha256_bytes`
7. `knowledge_storage_io.StorageReadSession.recheck`
8. `publication.bind_publication_workspace`
9. `publication.collect_reviewed_publication_edits`
10. `publication_candidate._hashes`
11. `knowledge_evidence.sha256_bytes`
12. `knowledge_evidence.sha256_bytes`
13. `publication_candidate._candidate_path`
14. `knowledge_storage_io.StorageReadSession.recheck`
15. `publication_candidate.check_publication_candidate`
16. `publication.collect_reviewed_publication_edits`
17. `knowledge_evidence.sha256_bytes`
18. `knowledge_evidence.hash_json`

## Touches

- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [publication](../modules/publication.md)
- [publication_candidate](../modules/publication_candidate.md)
- [publication_maintenance](../modules/publication_maintenance.md)

## Behavior

This workflow starts at `publication_maintenance._maintenance`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
