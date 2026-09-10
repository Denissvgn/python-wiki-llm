# status_cmd_flow

**Entry point:** `status_cmd.run`
**Modules involved:** [circuit_breaker](../modules/circuit_breaker.md), [config](../modules/config.md), [io](../modules/io.md), [legacy_hooks](../modules/legacy_hooks.md), [paths](../modules/paths.md), [status_cmd](../modules/status_cmd.md), [wiki_lifecycle](../modules/wiki_lifecycle.md), [wiki_surface](../modules/wiki_surface.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_path`
2. `wiki_lifecycle.require_safe_wiki_scaffold`
3. `config.validate_source_root`
4. `paths.display_project_path`
5. `paths.display_project_path`
6. `wiki_surface.iter_page_kinds`
7. `paths.display_project_path`
8. `config.inspect_config`
9. `paths.display_project_path`
10. `paths.display_project_path`
11. `paths.display_project_path`
12. `paths.display_project_path`
13. `legacy_hooks.inspect_legacy_hooks`
14. `paths.shell_quote`
15. `io.first_unsafe_path_component`
16. `io.first_unsafe_path_component`
17. `paths.display_project_path`
18. `paths.display_project_path`
19. `circuit_breaker.load_state`
20. `circuit_breaker.breaker_ttl_seconds`
21. `circuit_breaker.breaker_ttl_seconds`

## Touches

- [circuit_breaker](../modules/circuit_breaker.md)
- [config](../modules/config.md)
- [io](../modules/io.md)
- [legacy_hooks](../modules/legacy_hooks.md)
- [paths](../modules/paths.md)
- [status_cmd](../modules/status_cmd.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `status_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
