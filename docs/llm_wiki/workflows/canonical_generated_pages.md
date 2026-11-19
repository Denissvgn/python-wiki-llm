# canonical_generated_pages

**Entry point:** `canonical_pages.canonical_generated_pages`
**Modules involved:** [bootstrap_runtime](../modules/bootstrap_runtime.md), [canonical_pages](../modules/canonical_pages.md), [infrastructure_state](../modules/infrastructure_state.md), [infrastructure_sync](../modules/infrastructure_sync.md)

> Use the generator's mappers; only known removal records extend live names.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `bootstrap_runtime.build_module_page_map`
2. `bootstrap_runtime.build_entity_occurrence_page_map`
3. `infrastructure_sync.build_infrastructure_page_map`
4. `infrastructure_state.infrastructure_evidence_by_page`

## Touches

- [bootstrap_runtime](../modules/bootstrap_runtime.md)
- [canonical_pages](../modules/canonical_pages.md)
- [infrastructure_state](../modules/infrastructure_state.md)
- [infrastructure_sync](../modules/infrastructure_sync.md)

## Behavior

This workflow starts at `canonical_pages.canonical_generated_pages`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
