# finalize_prepared_sync

**Entry point:** `sync_runtime._finalize_prepared_sync`
**Modules involved:** [host](../modules/host.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [sync_analysis_cache](../modules/sync_analysis_cache.md), [sync_runtime](../modules/sync_runtime.md), [wiki_surface_index](../modules/wiki_surface_index.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `wiki_surface_index.evaluate_surface_index`
2. `sync_analysis_cache.build_payload`
3. `sync_analysis_cache.report_capture`
4. `knowledge_orchestration.finalize_runtime_knowledge`
5. `knowledge_orchestration.RuntimeKnowledgeInputs`
6. `sync_analysis_cache.commitment`
7. `knowledge_orchestration.runtime_generation_options`
8. `host.emit`
9. `sync_analysis_cache.report_capture`
10. `sync_analysis_cache.save`
11. `host.emit`
12. `host.emit`
13. `host.emit`
14. `host.emit`
15. `host.emit`
16. `host.emit`
17. `host.emit`
18. `host.emit`
19. `host.emit`
20. `host.emit`
21. `host.emit`

## Touches

- [host](../modules/host.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)
- [sync_runtime](../modules/sync_runtime.md)
- [wiki_surface_index](../modules/wiki_surface_index.md)

## Behavior

This workflow starts at `sync_runtime._finalize_prepared_sync`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
