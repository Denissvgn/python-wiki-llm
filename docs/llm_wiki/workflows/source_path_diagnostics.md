# source_path_diagnostics

**Entry point:** `source_path_diagnostics.source_path_diagnostics`
**Modules involved:** [common](../modules/common.md), [config](../modules/config.md), [source_path_diagnostics](../modules/source_path_diagnostics.md), [source_selection](../modules/source_selection.md), [source_snapshot](../modules/source_snapshot.md)

> Observe selected path metadata without following links or reading content.

Inventory absence proves none of these facts. Selection exclusions prevent
even a metadata read; ignore decisions use the snapshot's captured rules.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.GitIgnoreMatcher`
2. `source_selection.path_is_selected`
3. `config.PathValidationError`
4. `source_snapshot._language_selection_for_path`
5. `config.is_agent_worktree_path`
6. `common.is_bundled_helper_implementation_path`
7. `config.GitIgnoreMatcher.is_ignored`
8. `source_snapshot._is_rescuable_typescript_src_lib_file`
9. `common.is_generated_javascript_bundle_path`

## Touches

- [common](../modules/common.md)
- [config](../modules/config.md)
- [source_path_diagnostics](../modules/source_path_diagnostics.md)
- [source_selection](../modules/source_selection.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `source_path_diagnostics.source_path_diagnostics`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
