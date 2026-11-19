# validate_artifact_parity

**Entry point:** `knowledge_artifacts._validate_artifact_parity`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_graph](../modules/knowledge_graph.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_reuse_format](../modules/knowledge_reuse_format.md), [section_ownership](../modules/section_ownership.md)

> Check the new cross-artifact state after its logical model is validated.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_index._validator_identity`
2. `canonical_json.sha256_digest`
3. `knowledge_graph._validate_typed_graph_concept_bindings`
4. `section_ownership.validate_section_ownership`
5. `knowledge_reuse_format.validate_reuse_artifact_parity`
6. `knowledge_governance.governance_hash_from_knowledge`
7. `knowledge_index._require_validation_receipt`
8. `knowledge_index._require_validation_receipt`
9. `knowledge_index._validator_identity`
10. `immutable.freeze`
11. `canonical_json.sha256_digest`
12. `knowledge_envelope.EvaluatedEnvelope`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_reuse_format](../modules/knowledge_reuse_format.md)
- [section_ownership](../modules/section_ownership.md)

## Behavior

This workflow starts at `knowledge_artifacts._validate_artifact_parity`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
