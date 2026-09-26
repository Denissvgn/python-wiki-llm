# capture_health_details

**Entry point:** `health_details.capture_health_details`
**Modules involved:** [health_contract](../modules/health_contract.md), [health_details](../modules/health_details.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_freshness](../modules/knowledge_freshness.md)

> Capture inventory, exact comparison basis and bounded primary examples.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_evidence.hash_json`
2. `knowledge_envelope.hash_source_snapshot`
3. `knowledge_artifacts.require_validated_artifacts`
4. `knowledge_freshness.structural_freshness_modeled`
5. `health_contract.HealthDetailsError`
6. `health_contract.HealthDetailsError`
7. `knowledge_freshness.structural_freshness_modeled`
8. `knowledge_evidence.canonical_json_text`

## Touches

- [health_contract](../modules/health_contract.md)
- [health_details](../modules/health_details.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_freshness](../modules/knowledge_freshness.md)

## Behavior

This workflow starts at `health_details.capture_health_details`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
