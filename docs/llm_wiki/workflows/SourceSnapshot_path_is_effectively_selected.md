# SourceSnapshot_path_is_effectively_selected

**Entry point:** `source_snapshot.SourceSnapshot.path_is_effectively_selected`
**Modules involved:** [common](../modules/common.md), [config](../modules/config.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

> Evaluate configured selection rules for an existing or missing path.

``selected_regular_paths`` is the finite, readable boundary for live
reads.  This predicate intentionally omits the existence requirement so
Git deletions can still be classified without re-admitting ignored,
globally excluded, agent-worktree, or bundled-helper paths.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.path_is_selected`
2. `config.is_agent_worktree_path`
3. `common.is_bundled_helper_implementation_path`
4. `config.GitIgnoreMatcher`

## Touches

- [common](../modules/common.md)
- [config](../modules/config.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `source_snapshot.SourceSnapshot.path_is_effectively_selected`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
