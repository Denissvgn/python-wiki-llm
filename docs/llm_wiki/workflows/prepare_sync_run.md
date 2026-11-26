# prepare_sync_run

**Entry point:** `sync_runtime._prepare_sync_run`
**Modules involved:** [api_contracts](../modules/api_contracts.md), [extraction_service](../modules/extraction_service.md), [historical_retirement](../modules/historical_retirement.md), [host](../modules/host.md), [inventory_cache](../modules/inventory_cache.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_reuse](../modules/knowledge_reuse.md), [source_retirement](../modules/source_retirement.md), [source_snapshot](../modules/source_snapshot.md), [sync_analysis_cache](../modules/sync_analysis_cache.md), [sync_generated_sections](../modules/sync_generated_sections.md), [sync_manifest](../modules/sync_manifest.md), [sync_ownership](../modules/sync_ownership.md), [sync_runtime](../modules/sync_runtime.md), [sync_transition_execution](../modules/sync_transition_execution.md), [sync_transitions](../modules/sync_transitions.md), [validation](../modules/validation.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_transition_execution.assert_no_pending_page_moves`
2. `source_retirement.SourceRetirementError`
3. `sync_manifest.unrecognised_generation_input_records`
4. `sync_ownership.SyncOwnershipError`
5. `sync_manifest.SyncManifest`
6. `inventory_cache.prepare_cache_options`
7. `knowledge_orchestration.capture_committed_knowledge`
8. `knowledge_orchestration.committed_runtime_provenance`
9. `host.emit`
10. `host.emit`
11. `source_snapshot.build_source_snapshot`
12. `sync_manifest.prune_manifest_for_source_selection`
13. `extraction_service.prepare_inventory_helpers`
14. `extraction_service.InventoryRequest`
15. `sync_analysis_cache.load`
16. `knowledge_reuse.wiki_input_hashes`
17. `sync_analysis_cache.inventory_result`
18. `source_retirement.SourceRetirementError`
19. `sync_manifest.retained_concept_page_paths`
20. `api_contracts.build_api_contracts`
21. `api_contracts.attach_routes_to_entry_points`
22. `host.emit`
23. `source_retirement.discover_retired_entities`
24. `validation.portable_path_key`
25. `wiki_surface.canonical_path`
26. `validation.portable_path_key`
27. `source_retirement.historical_entity_semantics`
28. `source_retirement.with_entity_retirement_state`
29. `historical_retirement.released_inputs`
30. `sync_transitions.find_missing_source_pages`
31. `sync_generated_sections.plan_generated_source_repairs`
32. `historical_retirement.plan_retirement`
33. `knowledge_orchestration.runtime_generation_options`
34. `knowledge_orchestration.runtime_source_snapshot_hash`
35. `knowledge_orchestration.runtime_generation_options_hash`
36. `knowledge_reuse.observation_inputs_hash`
37. `knowledge_orchestration.collect_runtime_repository_evidence`
38. `knowledge_reuse.wiki_input_hashes`
39. `sync_analysis_cache.SyncAnalysisMutationError`
40. `sync_analysis_cache.input_key`
41. `sync_analysis_cache.SyncAnalysisMutationError`
42. `knowledge_reuse.observation_inputs_hash`
43. `wiki_surface.canonical_path`
44. `extraction_service.get_call_graph`
45. `knowledge_reuse.wiki_input_hashes`
46. `sync_analysis_cache.SyncAnalysisMutationError`
47. `wiki_surface.canonical_path`

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
- [sync_ownership](../modules/sync_ownership.md)
- [sync_runtime](../modules/sync_runtime.md)
- [sync_transition_execution](../modules/sync_transition_execution.md)
- [sync_transitions](../modules/sync_transitions.md)
- [validation](../modules/validation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `sync_runtime._prepare_sync_run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
