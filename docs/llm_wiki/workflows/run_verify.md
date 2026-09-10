# run_verify

**Entry point:** `knowledge_cmd._run_verify`
**Modules involved:** [knowledge_cmd](../modules/knowledge_cmd.md), [knowledge_governance](../modules/knowledge_governance.md), [knowledge_loader](../modules/knowledge_loader.md), [verification_contracts](../modules/verification_contracts.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_loader.load_knowledge_state`
2. `knowledge_governance.GovernanceError`
3. `verification_contracts.build_artifact_verification_context`
4. `verification_contracts.verify`
5. `verification_contracts.verify_and_write_receipt`

## Touches

- [knowledge_cmd](../modules/knowledge_cmd.md)
- [knowledge_governance](../modules/knowledge_governance.md)
- [knowledge_loader](../modules/knowledge_loader.md)
- [verification_contracts](../modules/verification_contracts.md)

## Behavior

This workflow starts at `knowledge_cmd._run_verify`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
