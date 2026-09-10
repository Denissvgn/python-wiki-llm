# load_machine_verification_read_view

**Entry point:** `knowledge_verification.load_machine_verification_read_view`
**Modules involved:** [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_verification](../modules/knowledge_verification.md), [verification_contracts](../modules/verification_contracts.md)

> Load and evaluate one fixed receipt without executing a checker.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_consumption.MachineVerificationReadView`
2. `verification_contracts.load_verification_receipt`
3. `knowledge_consumption.MachineVerificationReadView`
4. `knowledge_consumption.MachineVerificationReadView`
5. `knowledge_evidence.hash_json`
6. `verification_contracts.evaluate_verification_receipt`
7. `knowledge_consumption.MachineVerificationReadView`

## Touches

- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_verification](../modules/knowledge_verification.md)
- [verification_contracts](../modules/verification_contracts.md)

## Behavior

This workflow starts at `knowledge_verification.load_machine_verification_read_view`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
