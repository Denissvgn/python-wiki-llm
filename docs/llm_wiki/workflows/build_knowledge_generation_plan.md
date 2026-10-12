# build_knowledge_generation_plan

**Entry point:** `knowledge_generation._build_knowledge_generation_plan`
**Modules involved:** [implementation_evidence](../modules/implementation_evidence.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_generation](../modules/knowledge_generation.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_links](../modules/knowledge_links.md), [knowledge_reuse](../modules/knowledge_reuse.md), [maintenance_evidence](../modules/maintenance_evidence.md), [maintenance_projection](../modules/maintenance_projection.md), [source_retirement](../modules/source_retirement.md), [sync_manifest](../modules/sync_manifest.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.ManifestEvidenceBaseline.unknown`
2. `knowledge_envelope.build_repository_record`
3. `knowledge_envelope.build_evaluated_envelope`
4. `knowledge_envelope.EnvelopeInputs`
5. `sync_manifest.SyncManifest.build_from_inventory`
6. `knowledge_links.collect_link_observations`
7. `knowledge_reuse.bind_reuse_commitment`
8. `infrastructure_sync.infrastructure_evidence_by_page`
9. `implementation_evidence.project_concept_implementations`
10. `source_retirement.retired_entity_mappings`
11. `knowledge_index.build_knowledge_index`
12. `knowledge_index.KnowledgeIndexInputs`
13. `knowledge_governance.apply_governance_projection`
14. `maintenance_evidence.captured_observations_from_knowledge`
15. `implementation_evidence.analysis_hash_from_producer`
16. `maintenance_evidence.maintenance_transfers_from_page_plan`
17. `maintenance_evidence.reconcile_pending_maintenance`
18. `maintenance_projection.project_maintenance_knowledge`
19. `knowledge_artifacts.build_knowledge_commit_plan`

## Touches

- [implementation_evidence](../modules/implementation_evidence.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [source_retirement](../modules/source_retirement.md)
- [sync_manifest](../modules/sync_manifest.md)

## Behavior

This workflow starts at `knowledge_generation._build_knowledge_generation_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
