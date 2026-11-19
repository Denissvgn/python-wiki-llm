# validator_identity

**Entry point:** `knowledge_index._validator_identity`
**Modules involved:** [knowledge_index](../modules/knowledge_index.md), [knowledge_kinds](../modules/knowledge_kinds.md), [knowledge_validators](../modules/knowledge_validators.md), [maintenance_state](../modules/maintenance_state.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_state.maintenance_core`
2. `knowledge_validators.current_validators`
3. `knowledge_kinds.current_kinds`

## Touches

- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_kinds](../modules/knowledge_kinds.md)
- [knowledge_validators](../modules/knowledge_validators.md)
- [maintenance_state](../modules/maintenance_state.md)

## Behavior

This workflow starts at `knowledge_index._validator_identity`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
