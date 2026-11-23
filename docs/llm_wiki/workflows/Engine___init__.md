# Engine___init__

**Entry point:** `engine.Engine.__init__`
**Modules involved:** [analysis_compatibility](../modules/analysis_compatibility.md), [engine](../modules/engine.md), [host](../modules/host.md), [integrations](../modules/integrations.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.Host`
2. `analysis_compatibility.selected_policy`
3. `integrations.IntegrationSet.merged`

## Touches

- [analysis_compatibility](../modules/analysis_compatibility.md)
- [engine](../modules/engine.md)
- [host](../modules/host.md)
- [integrations](../modules/integrations.md)

## Behavior

This workflow starts at `engine.Engine.__init__`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
