# preflight

**Entry point:** `knowledge_maintenance.preflight`
**Modules involved:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [common](../modules/common.md), [config](../modules/config.md), [extractor_helpers](../modules/extractor_helpers.md), [health_policy](../modules/health_policy.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_maintenance](../modules/knowledge_maintenance.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_path`
2. `config.validate_source_root`
3. `health_policy.MaintenanceError`
4. `health_policy.MaintenanceError`
5. `health_policy.MaintenanceError`
6. `health_policy.strict_json`
7. `knowledge_storage_io.read_guarded`
8. `health_policy.MaintenanceError`
9. `health_policy.MaintenanceError`
10. `source_snapshot.build_source_snapshot`
11. `knowledge_storage_io.StorageReadSession`
12. `knowledge_storage_io.StorageReadSession.read`
13. `health_policy.strict_json`
14. `knowledge_packs.parse_packed_root`
15. `knowledge_model._parse_bundle`
16. `knowledge_storage.parse_store_root`
17. `knowledge_model._parse_bundle`
18. `knowledge_model.parse_knowledge_index`
19. `sync_manifest.SyncManifest.load`
20. `health_policy.digest`
21. `health_policy.MaintenanceError`
22. `knowledge_storage_io.StorageReadSession.read`
23. `health_policy.digest`
24. `health_policy.MaintenanceError`
25. `source_selection.validate_persisted_source_selection_identity`
26. `common.inventory_language_for_path`
27. `analysis_compatibility.has_contract`
28. `analysis_compatibility.selected_policy`
29. `analysis_compatibility.selected_policy`
30. `analysis_capture.capture_analysis`
31. `knowledge_orchestration._producer_evidence`
32. `knowledge_orchestration._infrastructure_extractor_component`
33. `knowledge_envelope.build_producer_record`
34. `analysis_capture.attach`
35. `knowledge_envelope.ProducerComponentInput`
36. `analysis_compatibility.compare_components`
37. `analysis_compatibility.selected_policy`
38. `analysis_compatibility.compare_components`
39. `analysis_compatibility.selected_policy`
40. `knowledge_orchestration.runtime_generation_options`
41. `knowledge_orchestration.runtime_generation_options_hash`
42. `extractor_helpers.get_prepared_typescript_root`
43. `extractor_helpers.get_prepared_binary`
44. `knowledge_storage_io.StorageReadSession.recheck`
45. `knowledge_evidence.hash_json`
46. `knowledge_envelope.hash_source_snapshot`
47. `health_policy.digest`
48. `health_policy.digest`
49. `health_policy._binding`
50. `analysis_compatibility.producer_contracts`
51. `analysis_compatibility.producer_contracts`

## Touches

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [health_policy](../modules/health_policy.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_maintenance](../modules/knowledge_maintenance.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)
- [knowledge_packs](../modules/knowledge_packs.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [knowledge_storage_io](../modules/knowledge_storage_io.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `knowledge_maintenance.preflight`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
