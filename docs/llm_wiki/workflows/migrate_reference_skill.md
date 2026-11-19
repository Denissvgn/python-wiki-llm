# migrate_reference_skill

**Entry point:** `upgrade_runtime._migrate_reference_skill`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [host](../modules/host.md), [skills](../modules/skills.md), [upgrade_runtime](../modules/upgrade_runtime.md)

> Remove only a verified-current source after a usable target commit.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `skills.skills_install_dir`
2. `skills.skills_install_dir`
3. `skills.verify_reference_skill`
4. `filesystem_guard.windows_object_identity`
5. `filesystem_guard.guarded_tree_manifest`
6. `skills.verify_reference_skill`
7. `host.emit`
8. `host.emit`
9. `host.emit`
10. `filesystem_guard.remove_guarded_tree`
11. `host.emit`
12. `host.emit`
13. `host.emit`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [host](../modules/host.md)
- [skills](../modules/skills.md)
- [upgrade_runtime](../modules/upgrade_runtime.md)

## Behavior

This workflow starts at `upgrade_runtime._migrate_reference_skill`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
