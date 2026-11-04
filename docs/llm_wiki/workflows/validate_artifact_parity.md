# validate_artifact_parity

**Entry point:** `knowledge_artifacts._validate_artifact_parity`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_graph](../modules/knowledge_graph.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_reuse](../modules/knowledge_reuse.md), [section_ownership](../modules/section_ownership.md)

> Check the new cross-artifact state after its logical model is validated.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_index._validator_identity`
2. `knowledge_evidence.sha256_bytes`
3. `knowledge_graph._validate_typed_graph_concept_bindings`
4. `section_ownership.validate_section_ownership`
5. `knowledge_reuse.validate_reuse_artifact_parity`
6. `knowledge_governance.governance_hash_from_knowledge`
7. `knowledge_index._require_validation_receipt`
8. `knowledge_index._require_validation_receipt`
9. `knowledge_index._validator_identity`
10. `immutable.freeze`
11. `knowledge_evidence.sha256_bytes`
12. `knowledge_envelope.EvaluatedEnvelope`

## Touches

- [immutable](../modules/immutable.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_reuse](../modules/knowledge_reuse.md)
- [section_ownership](../modules/section_ownership.md)

## Behavior

This workflow starts at `knowledge_artifacts._validate_artifact_parity`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
