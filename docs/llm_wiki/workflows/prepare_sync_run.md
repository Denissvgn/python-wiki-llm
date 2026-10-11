# prepare_sync_run

**Entry point:** `sync_cmd._prepare_sync_run`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [extraction_service](../modules/extraction_service.md), [inventory_cache](../modules/inventory_cache.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [source_snapshot](../modules/source_snapshot.md), [sync_analysis_cache](../modules/sync_analysis_cache.md), [sync_cmd](../modules/sync_cmd.md), [sync_manifest](../modules/sync_manifest.md), [sync_transition_execution](../modules/sync_transition_execution.md), [sync_transitions](../modules/sync_transitions.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_transition_execution.assert_no_pending_page_moves`
2. `sync_manifest.SyncManifest`
3. `inventory_cache.prepare_cache_options`
4. `knowledge_orchestration.capture_committed_knowledge`
5. `knowledge_orchestration.committed_runtime_provenance`
6. `source_snapshot.build_source_snapshot`
7. `sync_manifest.prune_manifest_for_source_selection`
8. `sync_analysis_cache.load`
9. `knowledge_reuse.wiki_input_hashes`
10. `sync_analysis_cache.inventory_result`
11. `sync_manifest.retained_concept_page_paths`
12. `api_contracts.build_api_contracts`
13. `api_contracts.attach_routes_to_entry_points`
14. `sync_transitions.find_missing_source_pages`
15. `knowledge_orchestration.runtime_generation_options`
16. `knowledge_orchestration.runtime_source_snapshot_hash`
17. `knowledge_orchestration.runtime_generation_options_hash`
18. `knowledge_reuse.observation_inputs_hash`
19. `knowledge_orchestration.collect_runtime_repository_evidence`
20. `knowledge_reuse.wiki_input_hashes`
21. `sync_analysis_cache.SyncAnalysisMutationError`
22. `sync_analysis_cache.input_key`
23. `sync_analysis_cache.SyncAnalysisMutationError`
24. `knowledge_reuse.observation_inputs_hash`
25. `wiki_surface.canonical_path`
26. `extraction_service.get_call_graph`
27. `knowledge_reuse.wiki_input_hashes`
28. `sync_analysis_cache.SyncAnalysisMutationError`
29. `wiki_surface.canonical_path`

## Touches

- [api_contracts](../modules/api_contracts.md)
- [extraction_service](../modules/extraction_service.md)
- [inventory_cache](../modules/inventory_cache.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)
- [sync_cmd](../modules/sync_cmd.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_transition_execution](../modules/sync_transition_execution.md)
- [sync_transitions](../modules/sync_transitions.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `sync_cmd._prepare_sync_run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
