# validate_source_root

**Entry point:** `path_policy.validate_source_root`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [host](../modules/host.md), [io](../modules/io.md), [path_policy](../modules/path_policy.md)

> Validate a source root according to the CLI source-read policy.

By default this preserves :func:`validate_path` behaviour and rejects paths
outside the current working directory.  When ``allow_external`` is true, the
path may live outside cwd but must resolve to an existing directory.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.current_host`
2. `filesystem_guard.windows_current_user_sid`
3. `io.first_unsafe_path_component`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [host](../modules/host.md)
- [io](../modules/io.md)
- [path_policy](../modules/path_policy.md)

## Behavior

This workflow starts at `path_policy.validate_source_root`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
