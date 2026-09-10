# print_managed_lifecycle

**Entry point:** `status_cmd._print_managed_lifecycle`
**Modules involved:** [config](../modules/config.md), [io](../modules/io.md), [paths](../modules/paths.md), [rendering_lifecycle](../modules/rendering_lifecycle.md), [skills](../modules/skills.md), [status_cmd](../modules/status_cmd.md)

> Report live schema/reference state; persisted fields are evidence only.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `skills.skills_install_dir`
2. `skills.verify_reference_skill`
3. `config.config_requires_manual_recovery`
4. `rendering_lifecycle.classify_lifecycle_status`
5. `skills.skills_install_dir`
6. `skills.verify_reference_skill`
7. `io.first_unsafe_path_component`
8. `paths.display_project_path`
9. `paths.display_project_path`
10. `paths.display_project_path`
11. `paths.display_project_path`
12. `paths.display_project_path`
13. `paths.display_project_path`
14. `paths.display_project_path`
15. `paths.display_project_path`
16. `paths.display_project_path`
17. `paths.display_project_path`
18. `paths.display_project_path`
19. `config.config_requires_manual_recovery`
20. `skills.verify_reference_skill`

## Touches

- [config](../modules/config.md)
- [io](../modules/io.md)
- [paths](../modules/paths.md)
- [rendering_lifecycle](../modules/rendering_lifecycle.md)
- [skills](../modules/skills.md)
- [status_cmd](../modules/status_cmd.md)

## Behavior

This workflow starts at `status_cmd._print_managed_lifecycle`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
