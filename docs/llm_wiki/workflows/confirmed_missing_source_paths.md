# confirmed_missing_source_paths

**Entry point:** `source_snapshot.confirmed_missing_source_paths`
**Modules involved:** [common](../modules/common.md), [gitignore](../modules/gitignore.md), [path_policy](../modules/path_policy.md), [source_snapshot](../modules/source_snapshot.md)

> Confirm requested absence without converting omitted sources to deletion.

Only selected paths are eligible. Parent directories are inspected without
following links, and their identities are rechecked before returning. The
owning captured read still performs its normal final source recheck.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `gitignore.GitIgnoreMatcher`
2. `path_policy.is_agent_worktree_path`
3. `common.is_bundled_helper_implementation_path`
4. `gitignore.GitIgnoreMatcher.is_ignored`

## Touches

- [common](../modules/common.md)
- [gitignore](../modules/gitignore.md)
- [path_policy](../modules/path_policy.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `source_snapshot.confirmed_missing_source_paths`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
