# validate_knowledge_artifacts

**Entry point:** `knowledge_artifacts.validate_knowledge_artifacts`
**Modules involved:** [immutable](../modules/immutable.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_graph](../modules/knowledge_graph.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_reuse](../modules/knowledge_reuse.md), [section_ownership](../modules/section_ownership.md)

> Validate canonical projections, cross-artifact parity, and manifest basis.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_index._validated_index_serialization`
2. `knowledge_evidence.sha256_bytes`
3. `knowledge_graph.typed_graph_from_knowledge_extensions`
4. `section_ownership.validate_section_ownership`
5. `knowledge_reuse.validate_reuse_artifact_parity`
6. `knowledge_governance.governance_hash_from_knowledge`
7. `immutable.freeze`
8. `knowledge_evidence.sha256_bytes`
9. `knowledge_envelope.EvaluatedEnvelope`

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

This workflow starts at `knowledge_artifacts.validate_knowledge_artifacts`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
