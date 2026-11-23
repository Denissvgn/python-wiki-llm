# prepare_sync_run

**Entry point:** `sync_runtime._prepare_sync_run`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [extraction_service](../modules/extraction_service.md), [historical_retirement](../modules/historical_retirement.md), [host](../modules/host.md), [inventory_cache](../modules/inventory_cache.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [source_retirement](../modules/source_retirement.md), [source_snapshot](../modules/source_snapshot.md), [sync_analysis_cache](../modules/sync_analysis_cache.md), [sync_generated_sections](../modules/sync_generated_sections.md), [sync_manifest](../modules/sync_manifest.md), [sync_runtime](../modules/sync_runtime.md), [sync_transition_execution](../modules/sync_transition_execution.md), [sync_transitions](../modules/sync_transitions.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_transition_execution.assert_no_pending_page_moves`
2. `source_retirement.SourceRetirementError`
3. `sync_manifest.SyncManifest`
4. `inventory_cache.prepare_cache_options`
5. `knowledge_orchestration.capture_committed_knowledge`
6. `knowledge_orchestration.committed_runtime_provenance`
7. `host.emit`
8. `host.emit`
9. `source_snapshot.build_source_snapshot`
10. `sync_manifest.prune_manifest_for_source_selection`
11. `extraction_service.prepare_inventory_helpers`
12. `extraction_service.InventoryRequest`
13. `sync_analysis_cache.load`
14. `knowledge_reuse.wiki_input_hashes`
15. `sync_analysis_cache.inventory_result`
16. `source_retirement.SourceRetirementError`
17. `sync_manifest.retained_concept_page_paths`
18. `api_contracts.build_api_contracts`
19. `api_contracts.attach_routes_to_entry_points`
20. `host.emit`
21. `source_retirement.discover_retired_entities`
22. `validation.portable_path_key`
23. `wiki_surface.canonical_path`
24. `validation.portable_path_key`
25. `source_retirement.historical_entity_semantics`
26. `source_retirement.with_entity_retirement_state`
27. `historical_retirement.released_inputs`
28. `sync_transitions.find_missing_source_pages`
29. `sync_generated_sections.plan_generated_source_repairs`
30. `historical_retirement.plan_retirement`
31. `knowledge_orchestration.runtime_generation_options`
32. `knowledge_orchestration.runtime_source_snapshot_hash`
33. `knowledge_orchestration.runtime_generation_options_hash`
34. `knowledge_reuse.observation_inputs_hash`
35. `knowledge_orchestration.collect_runtime_repository_evidence`
36. `knowledge_reuse.wiki_input_hashes`
37. `sync_analysis_cache.SyncAnalysisMutationError`
38. `sync_analysis_cache.input_key`
39. `sync_analysis_cache.SyncAnalysisMutationError`
40. `knowledge_reuse.observation_inputs_hash`
41. `wiki_surface.canonical_path`
42. `extraction_service.get_call_graph`
43. `knowledge_reuse.wiki_input_hashes`
44. `sync_analysis_cache.SyncAnalysisMutationError`
45. `wiki_surface.canonical_path`

## Touches

- [api_contracts](../modules/api_contracts.md)
- [extraction_service](../modules/extraction_service.md)
- [historical_retirement](../modules/historical_retirement.md)
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
