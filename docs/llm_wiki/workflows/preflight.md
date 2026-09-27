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
12. `health_policy.strict_json`
13. `knowledge_packs.parse_packed_root`
14. `knowledge_model._parse_bundle`
15. `knowledge_storage.parse_store_root`
16. `knowledge_model._parse_bundle`
17. `knowledge_model.parse_knowledge_index`
18. `sync_manifest.SyncManifest.load`
19. `health_policy.digest`
20. `health_policy.MaintenanceError`
21. `health_policy.digest`
22. `health_policy.MaintenanceError`
23. `source_selection.validate_persisted_source_selection_identity`
24. `common.inventory_language_for_path`
25. `analysis_compatibility.has_contract`
26. `analysis_compatibility.selected_policy`
27. `analysis_compatibility.selected_policy`
28. `analysis_capture.capture_analysis`
29. `knowledge_orchestration._producer_evidence`
30. `knowledge_orchestration._infrastructure_extractor_component`
31. `knowledge_envelope.build_producer_record`
32. `analysis_capture.attach`
33. `knowledge_envelope.ProducerComponentInput`
34. `analysis_compatibility.compare_components`
35. `analysis_compatibility.selected_policy`
36. `analysis_compatibility.compare_components`
37. `analysis_compatibility.selected_policy`
38. `knowledge_orchestration.runtime_generation_options`
39. `knowledge_orchestration.runtime_generation_options_hash`
40. `extractor_helpers.get_prepared_typescript_root`
41. `extractor_helpers.get_prepared_binary`
42. `knowledge_evidence.hash_json`
43. `knowledge_envelope.hash_source_snapshot`
44. `health_policy.digest`
45. `health_policy.digest`
46. `health_policy._binding`
47. `analysis_compatibility.producer_contracts`
48. `analysis_compatibility.producer_contracts`

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
