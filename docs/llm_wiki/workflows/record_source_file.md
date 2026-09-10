# record_source_file

**Entry point:** `source_snapshot._record_source_file`
**Modules involved:** [common](../modules/common.md), [config](../modules/config.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `common.is_bundled_helper_implementation_path`
2. `source_selection.path_is_selected`
3. `source_selection.path_is_link_or_reparse`
4. `common.is_bundled_helper_implementation_path`
5. `config.is_agent_worktree_path`

## Touches

- [common](../modules/common.md)
- [config](../modules/config.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `source_snapshot._record_source_file`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
