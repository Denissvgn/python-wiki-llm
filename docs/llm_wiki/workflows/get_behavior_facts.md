# get_behavior_facts

**Entry point:** `behavior_reference.get_behavior_facts`
**Modules involved:** [behavior_reference](../modules/behavior_reference.md), [cli](../modules/cli.md), [cli_reference](../modules/cli_reference.md), [current_contracts](../modules/current_contracts.md), [helper_runtime](../modules/helper_runtime.md), [knowledge_evidence](../modules/knowledge_evidence.md), [skills](../modules/skills.md)

> Return detached declarations for the loaded provider without inspecting a consumer wiki.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `cli_reference.build_cli_contract`
2. `cli.build_cli_parser`
3. `current_contracts.current_contract_defaults`
4. `helper_runtime.resolve_helper_policy`
5. `helper_runtime.resolve_helper_policy`
6. `helper_runtime.resolve_helper_policy`
7. `helper_runtime.resolve_helper_policy`
8. `skills.list_bundled_skills`
9. `knowledge_evidence.hash_json`

## Touches

- [behavior_reference](../modules/behavior_reference.md)
- [cli](../modules/cli.md)
- [cli_reference](../modules/cli_reference.md)
- [current_contracts](../modules/current_contracts.md)
- [helper_runtime](../modules/helper_runtime.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [skills](../modules/skills.md)

## Behavior

This workflow starts at `behavior_reference.get_behavior_facts`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
