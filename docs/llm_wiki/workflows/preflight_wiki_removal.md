# preflight_wiki_removal

**Entry point:** `uninstall_cmd._preflight_wiki_removal`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [io](../modules/io.md), [paths](../modules/paths.md), [uninstall_cmd](../modules/uninstall_cmd.md)

> Classify the optional wiki root without opening redirected targets.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `io.first_unsafe_path_component`
2. `paths.display_project_path`
3. `filesystem_guard.windows_object_identity`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [io](../modules/io.md)
- [paths](../modules/paths.md)
- [uninstall_cmd](../modules/uninstall_cmd.md)

## Behavior

This workflow starts at `uninstall_cmd._preflight_wiki_removal`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
