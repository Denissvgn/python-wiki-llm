# add_supersession_edges

**Entry point:** `knowledge_governance._add_supersession_edges`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_graph](../modules/knowledge_graph.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_graph.materialize_typed_graph`
2. `knowledge_graph.KnowledgeGraphInputs`
3. `knowledge_graph.GraphConcept`
4. `knowledge_evidence.is_valid_sha256`
5. `canonical_json.sha256_digest`
6. `canonical_json.compact_text`
7. `knowledge_graph.validate_typed_graph`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_graph](../modules/knowledge_graph.md)

## Behavior

This workflow starts at `knowledge_governance._add_supersession_edges`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
