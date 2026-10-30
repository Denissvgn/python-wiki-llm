# build_artifact_verification_context

**Entry point:** `verification_contracts.build_artifact_verification_context`
**Modules involved:** [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_evidence](../modules/knowledge_evidence.md), [knowledge_model](../modules/knowledge_model.md), [verification_contracts](../modules/verification_contracts.md)

> Build the canonical receipt context for one committed artifact set.

The context is intentionally assembled only from already evaluated,
application-owned inputs.  Bundle checks bind to the complete knowledge
artifact.  A concept-scoped check additionally binds to the canonical
concept record and uses its durable projected UID when governance exists.
Locator-only projects receive an explicitly disposable locator digest
rather than a misleading stable identifier.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_model.knowledge_index_to_payload`
2. `knowledge_artifacts.require_validated_artifacts`
3. `knowledge_evidence.hash_json`
4. `knowledge_evidence.hash_json`

## Touches

- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [knowledge_model](../modules/knowledge_model.md)
- [verification_contracts](../modules/verification_contracts.md)

## Behavior

This workflow starts at `verification_contracts.build_artifact_verification_context`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
