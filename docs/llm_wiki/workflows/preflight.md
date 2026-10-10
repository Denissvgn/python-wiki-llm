# preflight

**Entry point:** `knowledge_maintenance.preflight`
**Modules involved:** [analysis_capture](../modules/analysis_capture.md), [analysis_compatibility](../modules/analysis_compatibility.md), [common](../modules/common.md), [config](../modules/config.md), [extractor_helpers](../modules/extractor_helpers.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_maintenance](../modules/knowledge_maintenance.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_orchestration](../modules/knowledge_orchestration.md), [knowledge_packs](../modules/knowledge_packs.md), [knowledge_storage](../modules/knowledge_storage.md), [knowledge_storage_io](../modules/knowledge_storage_io.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_path`
2. `config.validate_source_root`
3. `knowledge_storage_io.read_guarded`
4. `source_snapshot.build_source_snapshot`
5. `knowledge_storage_io.StorageReadSession`
6. `knowledge_storage_io.StorageReadSession.read`
7. `knowledge_packs.parse_packed_root`
8. `knowledge_model._parse_bundle`
9. `knowledge_storage.parse_store_root`
10. `knowledge_model._parse_bundle`
11. `knowledge_model.parse_knowledge_index`
12. `sync_manifest.SyncManifest.load`
13. `knowledge_storage_io.StorageReadSession.read`
14. `source_selection.validate_persisted_source_selection_identity`
15. `common.inventory_language_for_path`
16. `analysis_compatibility.has_contract`
17. `analysis_compatibility.selected_policy`
18. `analysis_compatibility.selected_policy`
19. `analysis_capture.capture_analysis`
20. `knowledge_orchestration._producer_evidence`
21. `knowledge_orchestration._infrastructure_extractor_component`
22. `knowledge_envelope.build_producer_record`
23. `analysis_capture.attach`
24. `knowledge_envelope.ProducerComponentInput`
25. `analysis_compatibility.compare_components`
26. `analysis_compatibility.selected_policy`
27. `analysis_compatibility.compare_components`
28. `analysis_compatibility.selected_policy`
29. `knowledge_orchestration.runtime_generation_options`
30. `knowledge_orchestration.runtime_generation_options_hash`
31. `extractor_helpers.get_prepared_typescript_root`
32. `extractor_helpers.get_prepared_binary`
33. `knowledge_storage_io.StorageReadSession.recheck`
34. `knowledge_evidence.hash_json`
35. `knowledge_envelope.hash_source_snapshot`
36. `analysis_compatibility.producer_contracts`
37. `analysis_compatibility.producer_contracts`

## Touches

- [analysis_capture](../modules/analysis_capture.md)
- [analysis_compatibility](../modules/analysis_compatibility.md)
- [common](../modules/common.md)
- [config](../modules/config.md)
- [extractor_helpers](../modules/extractor_helpers.md)
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
