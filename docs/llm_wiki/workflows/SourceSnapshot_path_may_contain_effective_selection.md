# SourceSnapshot_path_may_contain_effective_selection

**Entry point:** `source_snapshot.SourceSnapshot.path_may_contain_effective_selection`
**Modules involved:** [gitignore](../modules/gitignore.md), [path_policy](../modules/path_policy.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

> Return whether a directory remains reachable by the live rules.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_selection.selection_may_contain_path`
2. `path_policy.is_agent_worktree_path`
3. `gitignore.GitIgnoreMatcher`

## Touches

- [gitignore](../modules/gitignore.md)
- [path_policy](../modules/path_policy.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `source_snapshot.SourceSnapshot.path_may_contain_effective_selection`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
