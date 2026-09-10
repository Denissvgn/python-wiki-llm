# run_status

**Entry point:** `knowledge_cmd._run_status`
**Modules involved:** [knowledge_cmd](../modules/knowledge_cmd.md), [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_loader](../modules/knowledge_loader.md), [knowledge_observability](../modules/knowledge_observability.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_governance.GovernanceError`
2. `knowledge_loader.load_knowledge_state`
3. `knowledge_consumption.build_knowledge_read_view`
4. `knowledge_observability.knowledge_freshness_disclosure`
5. `knowledge_governance.GovernanceError`
6. `knowledge_governance.load_governance`

## Touches

- [knowledge_cmd](../modules/knowledge_cmd.md)
- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [knowledge_observability](../modules/knowledge_observability.md)

## Behavior

This workflow starts at `knowledge_cmd._run_status`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
