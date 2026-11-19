# validated_source

**Entry point:** `knowledge_projection._validated_source`
**Modules involved:** [canonical_json](../modules/canonical_json.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_projection](../modules/knowledge_projection.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_artifacts.require_validated_artifacts`
2. `knowledge_model.serialize_knowledge_index`
3. `knowledge_artifacts.validate_knowledge_artifacts`
4. `canonical_json.sha256_digest`

## Touches

- [canonical_json](../modules/canonical_json.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_projection](../modules/knowledge_projection.md)

## Behavior

This workflow starts at `knowledge_projection._validated_source`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
