# try_sync_knowledge_reuse

**Entry point:** `sync_cmd._try_sync_knowledge_reuse`
**Modules involved:** [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [progress](../modules/progress.md), [source_snapshot](../modules/source_snapshot.md), [sync_cmd](../modules/sync_cmd.md), [validation](../modules/validation.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_envelope.build_repository_record`
2. `knowledge_reuse.bind_reuse_commitment`
3. `source_snapshot.source_snapshot_matches_current_files`
4. `validation.resolve_portable_workspace_path`
5. `knowledge_evidence.hash_file`
6. `knowledge_reuse.wiki_input_hashes`
7. `knowledge_orchestration.collect_runtime_repository_evidence`
8. `knowledge_reuse.repository_input_hash`
9. `knowledge_envelope.build_repository_record`
10. `knowledge_reuse.implementation_hash`
11. `progress.record_counts`
12. `knowledge_reuse.unchanged_commit_result`

## Touches

- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [progress](../modules/progress.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_cmd](../modules/sync_cmd.md)
- [validation](../modules/validation.md)

## Behavior

This workflow starts at `sync_cmd._try_sync_knowledge_reuse`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
