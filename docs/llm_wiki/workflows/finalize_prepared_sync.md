# finalize_prepared_sync

**Entry point:** `sync_cmd._finalize_prepared_sync`
**Modules involved:** [knowledge_orchestration](../modules/knowledge_orchestration.md), [sync_analysis_cache](../modules/sync_analysis_cache.md), [sync_cmd](../modules/sync_cmd.md), [wiki_surface_index](../modules/wiki_surface_index.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface_index.evaluate_surface_index`
2. `sync_analysis_cache.build_payload`
3. `sync_analysis_cache.report_capture`
4. `knowledge_orchestration.finalize_runtime_knowledge`
5. `knowledge_orchestration.RuntimeKnowledgeInputs`
6. `sync_analysis_cache.commitment`
7. `knowledge_orchestration.runtime_generation_options`
8. `sync_analysis_cache.report_capture`
9. `sync_analysis_cache.save`

## Touches

- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)
- [sync_cmd](../modules/sync_cmd.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

This workflow starts at `sync_cmd._finalize_prepared_sync`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
