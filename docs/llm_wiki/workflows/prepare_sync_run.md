# prepare_sync_run

**Entry point:** `sync_runtime._prepare_sync_run`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [extraction_service](../modules/extraction_service.md), [host](../modules/host.md), [inventory_cache](../modules/inventory_cache.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [source_retirement](../modules/source_retirement.md), [source_snapshot](../modules/source_snapshot.md), [sync_analysis_cache](../modules/sync_analysis_cache.md), [sync_generated_sections](../modules/sync_generated_sections.md), [sync_manifest](../modules/sync_manifest.md), [sync_runtime](../modules/sync_runtime.md), [sync_transition_execution](../modules/sync_transition_execution.md), [sync_transitions](../modules/sync_transitions.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_transition_execution.assert_no_pending_page_moves`
2. `sync_manifest.SyncManifest`
3. `inventory_cache.prepare_cache_options`
4. `knowledge_orchestration.capture_committed_knowledge`
5. `knowledge_orchestration.committed_runtime_provenance`
6. `host.emit`
7. `host.emit`
8. `source_snapshot.build_source_snapshot`
9. `sync_manifest.prune_manifest_for_source_selection`
10. `extraction_service.prepare_inventory_helpers`
11. `extraction_service.InventoryRequest`
12. `sync_analysis_cache.load`
13. `knowledge_reuse.wiki_input_hashes`
14. `sync_analysis_cache.inventory_result`
15. `source_retirement.SourceRetirementError`
16. `sync_manifest.retained_concept_page_paths`
17. `api_contracts.build_api_contracts`
18. `api_contracts.attach_routes_to_entry_points`
19. `host.emit`
20. `source_retirement.discover_retired_entities`
21. `validation.portable_path_key`
22. `wiki_surface.canonical_path`
23. `validation.portable_path_key`
24. `source_retirement.historical_entity_semantics`
25. `source_retirement.with_entity_retirement_state`
26. `sync_transitions.find_missing_source_pages`
27. `sync_generated_sections.plan_generated_source_repairs`
28. `knowledge_orchestration.runtime_generation_options`
29. `knowledge_orchestration.runtime_source_snapshot_hash`
30. `knowledge_orchestration.runtime_generation_options_hash`
31. `knowledge_reuse.observation_inputs_hash`
32. `knowledge_orchestration.collect_runtime_repository_evidence`
33. `knowledge_reuse.wiki_input_hashes`
34. `sync_analysis_cache.SyncAnalysisMutationError`
35. `sync_analysis_cache.input_key`
36. `sync_analysis_cache.SyncAnalysisMutationError`
37. `knowledge_reuse.observation_inputs_hash`
38. `wiki_surface.canonical_path`
39. `extraction_service.get_call_graph`
40. `knowledge_reuse.wiki_input_hashes`
41. `sync_analysis_cache.SyncAnalysisMutationError`
42. `wiki_surface.canonical_path`

## Touches

- [api_contracts](../modules/api_contracts.md)
- [extraction_service](../modules/extraction_service.md)
- [host](../modules/host.md)
- [inventory_cache](../modules/inventory_cache.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [source_retirement](../modules/source_retirement.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_analysis_cache](../modules/sync_analysis_cache.md)
- [sync_generated_sections](../modules/sync_generated_sections.md)
- [sync_manifest](../modules/sync_manifest.md)
- [sync_runtime](../modules/sync_runtime.md)
- [sync_transition_execution](../modules/sync_transition_execution.md)
- [sync_transitions](../modules/sync_transitions.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `sync_runtime._prepare_sync_run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
