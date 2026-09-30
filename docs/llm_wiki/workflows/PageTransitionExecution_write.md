# PageTransitionExecution_write

**Entry point:** `sync_transition_execution.PageTransitionExecution.write`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [markdown_sections](../modules/markdown_sections.md), [sync_transition_execution](../modules/sync_transition_execution.md), [sync_transitions](../modules/sync_transitions.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `markdown_sections.normalize_markdown`
2. `markdown_sections.normalize_markdown`
3. `filesystem_guard.ensure_guarded_directory`
4. `filesystem_guard.atomic_write_guarded_bytes`
5. `sync_transitions.PageTransitionError`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [markdown_sections](../modules/markdown_sections.md)
- [sync_transition_execution](../modules/sync_transition_execution.md)
- [sync_transitions](../modules/sync_transitions.md)

## Behavior

This workflow starts at `sync_transition_execution.PageTransitionExecution.write`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
