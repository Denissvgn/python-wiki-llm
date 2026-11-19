# Engine_operation

**Entry point:** `__init__.Engine.operation`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [domain_pack](../modules/domain_pack.md), [engine___init__](../modules/engine___init__.md), [helper_runtime](../modules/helper_runtime.md), [host](../modules/host.md), [knowledge_kinds](../modules/knowledge_kinds.md), [knowledge_validators](../modules/knowledge_validators.md), [publication_targets](../modules/publication_targets.md)

> Apply this engine's grants to all work inside the block.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.using_host`
2. `analysis_compatibility.comparison_scope`
3. `helper_runtime.helper_policy`
4. `helper_runtime.helper_operation`
5. `knowledge_validators.using_validators`
6. `knowledge_kinds.using_kinds`
7. `domain_pack.using_pack`
8. `publication_targets.using_publication_targets`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [domain_pack](../modules/domain_pack.md)
- [engine___init__](../modules/engine___init__.md)
- [helper_runtime](../modules/helper_runtime.md)
- [host](../modules/host.md)
- [knowledge_kinds](../modules/knowledge_kinds.md)
- [knowledge_validators](../modules/knowledge_validators.md)
- [publication_targets](../modules/publication_targets.md)

## Behavior

This workflow starts at `__init__.Engine.operation`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
