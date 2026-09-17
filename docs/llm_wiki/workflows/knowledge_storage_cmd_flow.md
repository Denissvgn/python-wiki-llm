# knowledge_storage_cmd_flow

**Entry point:** `knowledge_storage_cmd.run`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [knowledge_cmd](../modules/knowledge_cmd.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_cmd](../modules/knowledge_storage_cmd.md), [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md), [knowledge_stream_audit](../modules/knowledge_stream_audit.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_cmd._wiki_root`
2. `knowledge_storage_lifecycle.migrate_knowledge_storage`
3. `knowledge_storage_lifecycle.recover_knowledge_storage`
4. `knowledge_storage_lifecycle.export_knowledge_v1`
5. `knowledge_storage.decode_bytes`
6. `knowledge_storage_io.read_guarded`
7. `knowledge_storage_lifecycle.prune_knowledge_storage`
8. `knowledge_storage_lifecycle._outside_tree`
9. `filesystem_guard.ensure_guarded_directory`
10. `filesystem_guard.atomic_write_guarded_bytes`
11. `knowledge_storage.canonical_bytes`
12. `knowledge_storage_lifecycle.restore_pruned_storage`
13. `knowledge_storage_diagnostics.review_storage`
14. `knowledge_stream_audit.audit_knowledge_stream`
15. `knowledge_storage_diagnostics.storage_report`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_cmd](../modules/knowledge_cmd.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_cmd](../modules/knowledge_storage_cmd.md)
- [knowledge_storage_diagnostics](../modules/knowledge_storage_diagnostics.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [knowledge_storage_lifecycle](../modules/knowledge_storage_lifecycle.md)
- [knowledge_stream_audit](../modules/knowledge_stream_audit.md)

## Behavior

Resolves the managed wiki and delegates the requested explicit storage operation. Migration receives the selected storage profile; inspection and comparison receive output bounds. Structured errors produce failure exits, and storage operations do not stage, rewrite history or publish to a remote.
