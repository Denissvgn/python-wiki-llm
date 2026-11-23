# Engine_operation

**Entry point:** `engine.Engine.operation`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [engine](../modules/engine.md), [host](../modules/host.md), [integrations](../modules/integrations.md), [knowledge_kinds](../modules/knowledge_kinds.md), [knowledge_validators](../modules/knowledge_validators.md), [pack_interfaces](../modules/pack_interfaces.md)

> Apply this engine's grants to all work inside the block.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.using_host`
2. `analysis_compatibility.comparison_scope`
3. `knowledge_validators.using_validators`
4. `knowledge_kinds.using_kinds`
5. `pack_interfaces.using_pack`
6. `integrations.using_integrations`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [engine](../modules/engine.md)
- [host](../modules/host.md)
- [integrations](../modules/integrations.md)
- [knowledge_kinds](../modules/knowledge_kinds.md)
- [knowledge_validators](../modules/knowledge_validators.md)
- [pack_interfaces](../modules/pack_interfaces.md)

## Behavior

This workflow starts at `engine.Engine.operation`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
