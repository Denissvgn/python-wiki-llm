# application_knowledge_extensions

**Entry point:** `knowledge_generation._application_knowledge_extensions`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_generation](../modules/knowledge_generation.md), [knowledge_graph](../modules/knowledge_graph.md), [progress](../modules/progress.md), [section_ownership](../modules/section_ownership.md)

> Build reserved extensions from the exact final evaluated snapshot.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_artifacts.require_validated_artifacts`
2. `knowledge_evidence.hash_json`
3. `knowledge_envelope.hash_inventory`
4. `progress.record_counts`
5. `knowledge_graph.materialize_typed_graph`
6. `knowledge_graph.KnowledgeGraphInputs`
7. `section_ownership.observe_page_sections`
8. `section_ownership.section_ownership_extension`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_generation](../modules/knowledge_generation.md)
- [knowledge_graph](../modules/knowledge_graph.md)
- [progress](../modules/progress.md)
- [section_ownership](../modules/section_ownership.md)

## Behavior

This workflow starts at `knowledge_generation._application_knowledge_extensions`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
