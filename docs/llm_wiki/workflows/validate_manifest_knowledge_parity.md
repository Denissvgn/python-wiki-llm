# validate_manifest_knowledge_parity

**Entry point:** `knowledge_artifacts._validate_manifest_knowledge_parity`
**Modules involved:** [infrastructure_state](../modules/infrastructure_state.md), [integrations](../modules/integrations.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [maintenance_projection](../modules/maintenance_projection.md), [source_retirement](../modules/source_retirement.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_projection.validate_maintenance_projection`
2. `source_retirement.retired_entity_mappings`
3. `source_retirement.source_retirement_projection`
4. `integrations.attributes`
5. `knowledge_evidence.is_valid_sha256`
6. `infrastructure_state.infrastructure_evidence_by_page`

## Touches

- [infrastructure_state](../modules/infrastructure_state.md)
- [integrations](../modules/integrations.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [maintenance_projection](../modules/maintenance_projection.md)
- [source_retirement](../modules/source_retirement.md)

## Behavior

This workflow starts at `knowledge_artifacts._validate_manifest_knowledge_parity`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
