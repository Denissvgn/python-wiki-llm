# projected_commit_plan

**Entry point:** `knowledge_cmd._projected_commit_plan`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_cmd](../modules/knowledge_cmd.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_index](../modules/knowledge_index.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_governance.strip_governance_projection`
2. `knowledge_governance.apply_governance_projection`
3. `knowledge_artifacts.build_knowledge_commit_plan`
4. `knowledge_index.serialize_knowledge_index`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_cmd](../modules/knowledge_cmd.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_index](../modules/knowledge_index.md)

## Behavior

This workflow starts at `knowledge_cmd._projected_commit_plan`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
