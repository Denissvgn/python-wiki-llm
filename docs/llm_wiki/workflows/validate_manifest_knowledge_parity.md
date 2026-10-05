# validate_manifest_knowledge_parity

**Entry point:** `knowledge_artifacts._validate_manifest_knowledge_parity`
**Modules involved:** [implementation_evidence](../modules/implementation_evidence.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [maintenance_projection](../modules/maintenance_projection.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_projection.validate_maintenance_projection`
2. `implementation_evidence.validate_concept_implementation`
3. `knowledge_evidence.is_valid_sha256`
4. `infrastructure_sync.infrastructure_evidence_by_page`

## Touches

- [implementation_evidence](../modules/implementation_evidence.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)

## Behavior

This workflow starts at `knowledge_artifacts._validate_manifest_knowledge_parity`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
