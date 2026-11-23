# released_inputs

**Entry point:** `historical_retirement.released_inputs`
**Modules involved:** [historical_retirement](../modules/historical_retirement.md), [historical_sources](../modules/historical_sources.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [sync_transitions](../modules/sync_transitions.md)

> Associate ordinary revival with the current capture and the previous native page digest.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `historical_sources.latest_released_pages`
2. `knowledge_artifacts.require_validated_artifacts`
3. `sync_transitions.ReleasedPageInputs`

## Touches

- [historical_retirement](../modules/historical_retirement.md)
- [historical_sources](../modules/historical_sources.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [sync_transitions](../modules/sync_transitions.md)

## Behavior

This workflow starts at `historical_retirement.released_inputs`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
