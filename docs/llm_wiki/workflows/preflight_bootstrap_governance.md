# preflight_bootstrap_governance

**Entry point:** `bootstrap_runtime._preflight_bootstrap_governance`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [infrastructure_sync](../modules/infrastructure_sync.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_orchestration](../modules/knowledge_orchestration.md)

> Reject corrupt or missing committed governance before creating pages.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `infrastructure_sync.validate_infrastructure_generation_input`
2. `knowledge_governance.load_governance`
3. `knowledge_orchestration.committed_governance_bundle_id`
4. `knowledge_governance.GovernanceError`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_orchestration](../modules/knowledge_orchestration.md)

## Behavior

This workflow starts at `bootstrap_runtime._preflight_bootstrap_governance`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
