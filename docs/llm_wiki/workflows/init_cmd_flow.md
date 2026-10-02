# init_cmd_flow

**Entry point:** `init_cmd.run`
**Modules involved:** [config](../modules/config.md), [extractor_helpers](../modules/extractor_helpers.md), [filesystem_guard](../modules/filesystem_guard.md), [helper_preparation](../modules/helper_preparation.md), [init_cmd](../modules/init_cmd.md), [rendering_lifecycle](../modules/rendering_lifecycle.md), [services_schema](../modules/services_schema.md), [skills](../modules/skills.md), [source_selection](../modules/source_selection.md), [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_path`
2. `wiki_lifecycle.require_safe_wiki_scaffold`
3. `config.require_safe_config_path`
4. `config.inspect_config`
5. `config.get_agent_config_path`
6. `config.config_requires_manual_recovery`
7. `source_selection.resolve_source_selection`
8. `services_schema.require_safe_schema_path`
9. `services_schema.decode_managed_document_bytes`
10. `services_schema.ManagedSchemaPathError`
11. `services_schema.require_replaceable_managed_schema`
12. `services_schema.ManagedSchemaBlockError`
13. `helper_preparation.ensure_source_helpers`
14. `extractor_helpers.helper_preparation_failure_hint`
15. `wiki_lifecycle.provision_wiki_scaffold`
16. `config.require_config_inspection_unchanged`
17. `skills._provision_reference_skill_guarded`
18. `rendering_lifecycle.reference_recovery_command`
19. `skills.skills_install_dir`
20. `skills.list_bundled_skills`
21. `skills.verify_reference_skill`
22. `rendering_lifecycle.select_render_profile`
23. `filesystem_guard.ensure_guarded_directory`
24. `services_schema.require_safe_schema_path`
25. `services_schema.decode_managed_document_bytes`
26. `services_schema.ManagedSchemaPathError`
27. `services_schema.require_replaceable_managed_schema`
28. `services_schema.build_schema_content`
29. `services_schema.replace_schema_block_content`
30. `services_schema.require_managed_schema_profile`
31. `services_schema.encode_managed_document_text`
32. `filesystem_guard.atomic_write_guarded_bytes`
33. `services_schema.require_safe_schema_path`
34. `config.write_config`
35. `config.get_agent_config_path`
36. `filesystem_guard.unlink_guarded_bytes`
37. `skills.verify_reference_skill`
38. `services_schema.ManagedSchemaBlockError`
39. `services_schema.ManagedSchemaBlockError`
40. `services_schema.require_safe_schema_path`
41. `services_schema.ManagedSchemaPathError`
42. `services_schema.ManagedSchemaPathError`
43. `services_schema.classify_managed_schema_block`
44. `services_schema.decode_managed_document_bytes`
45. `services_schema.ManagedSchemaBlockError`
46. `config.require_committed_config`

## Touches

- [config](../modules/config.md)
- [extractor_helpers](../modules/extractor_helpers.md)
- [filesystem_guard](../modules/filesystem_guard.md)
- [helper_preparation](../modules/helper_preparation.md)
- [init_cmd](../modules/init_cmd.md)
- [rendering_lifecycle](../modules/rendering_lifecycle.md)
- [services_schema](../modules/services_schema.md)
- [skills](../modules/skills.md)
- [source_selection](../modules/source_selection.md)
- [wiki_lifecycle](../modules/wiki_lifecycle.md)

## Behavior

This workflow starts at `init_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
