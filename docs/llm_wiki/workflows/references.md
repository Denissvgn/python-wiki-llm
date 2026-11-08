# references

**Entry point:** `publication_contracts._references`
**Modules involved:** [behavior_reference](../modules/behavior_reference.md), [cli_reference](../modules/cli_reference.md), [knowledge_evidence](../modules/knowledge_evidence.md), [publication_contracts](../modules/publication_contracts.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_evidence.hash_json`
2. `behavior_reference.validate_behavior_facts`
3. `cli_reference.validate_cli_contract`
4. `knowledge_evidence.hash_json`

## Touches

- [behavior_reference](../modules/behavior_reference.md)
- [cli_reference](../modules/cli_reference.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [publication_contracts](../modules/publication_contracts.md)

## Behavior

This workflow starts at `publication_contracts._references`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
