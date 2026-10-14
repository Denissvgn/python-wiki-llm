# upgrade_cmd_flow

**Entry point:** `upgrade_cmd.run`
**Modules involved:** [config](../modules/config.md), [current_contracts](../modules/current_contracts.md), [filesystem_guard](../modules/filesystem_guard.md), [knowledge_evidence](../modules/knowledge_evidence.md), [legacy_hooks](../modules/legacy_hooks.md), [rendering_lifecycle](../modules/rendering_lifecycle.md), [skills](../modules/skills.md), [source_selection](../modules/source_selection.md), [upgrade_cmd](../modules/upgrade_cmd.md), [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_path`
2. `wiki_lifecycle.require_safe_wiki_scaffold`
3. `config.require_safe_config_path`
4. `legacy_hooks.remove_legacy_hooks`
5. `legacy_hooks.inspect_legacy_hooks`
6. `config.inspect_config`
7. `config.get_agent_config_path`
8. `config.config_requires_manual_recovery`
9. `source_selection.resolve_source_selection`
10. `skills.verify_reference_skill`
11. `skills.skills_install_dir`
12. `skills.skills_install_dir`
13. `current_contracts.upgrade_current_knowledge`
14. `config.require_config_inspection_unchanged`
15. `skills._provision_reference_skill_guarded`
16. `rendering_lifecycle.reference_recovery_command`
17. `skills.skills_install_dir`
18. `skills.verify_reference_skill`
19. `rendering_lifecycle.select_render_profile`
20. `current_contracts.current_contract_defaults`
21. `knowledge_evidence.formatted_json_bytes`
22. `config.write_config`
23. `filesystem_guard.unlink_guarded_bytes`
24. `config.require_committed_config`
25. `config.write_config`
26. `config.require_committed_config`
27. `config.require_committed_config`

## Touches

- [config](../modules/config.md)
- [current_contracts](../modules/current_contracts.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [knowledge_evidence](../modules/knowledge_evidence.md)
- [legacy_hooks](../modules/legacy_hooks.md)
- [rendering_lifecycle](../modules/rendering_lifecycle.md)
- [skills](../modules/skills.md)
- [source_selection](../modules/source_selection.md)
- [upgrade_cmd](../modules/upgrade_cmd.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Behavior

This workflow starts at `upgrade_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
