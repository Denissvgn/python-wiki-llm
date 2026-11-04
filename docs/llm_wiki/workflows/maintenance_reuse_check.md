# maintenance_reuse_check

**Entry point:** `knowledge_reuse.maintenance_reuse_check`
**Modules involved:** [io](../modules/io.md), [knowledge_reuse](../modules/knowledge_reuse.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [maintenance_evidence](../modules/maintenance_evidence.md), [maintenance_protocol](../modules/maintenance_protocol.md), [python_implementation](../modules/python_implementation.md), [source_retirement](../modules/source_retirement.md), [source_snapshot](../modules/source_snapshot.md), [wiki_surface](../modules/wiki_surface.md)

> Reconcile exact live maintenance inputs before reusing a committed graph.

Success retains a guarded raw-page recheck for the caller's final boundary.
It never allocates an identity, changes review history or publishes evidence.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_protocol.guard_maintenance_owner`
2. `python_implementation.analysis_identity`
3. `knowledge_storage_io.StorageReadSession`
4. `wiki_surface.collect_wiki_pages`
5. `knowledge_storage.KnowledgeStorageError`
6. `knowledge_storage_io.StorageReadSession.read`
7. `knowledge_storage_io.StorageReadSession.recheck_work`
8. `knowledge_storage.KnowledgeStorageError`
9. `io.decode_markdown_bytes`
10. `source_snapshot.confirmed_missing_source_paths`
11. `maintenance_evidence.captured_observations_from_knowledge`
12. `source_retirement.retired_entity_mappings`
13. `maintenance_evidence.owner_key`
14. `maintenance_evidence.reconcile_pending_maintenance`

## Touches

- [io](../modules/io.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_protocol](../modules/maintenance_protocol.md)
- [python_implementation](../modules/python_implementation.md)
- [source_retirement](../modules/source_retirement.md)
- [source_snapshot](../modules/source_snapshot.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `knowledge_reuse.maintenance_reuse_check`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
