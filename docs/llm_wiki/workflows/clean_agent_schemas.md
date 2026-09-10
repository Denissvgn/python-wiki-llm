# clean_agent_schemas

**Entry point:** `uninstall_cmd._clean_agent_schemas`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [paths](../modules/paths.md), [services_schema](../modules/services_schema.md), [uninstall_cmd](../modules/uninstall_cmd.md)

> Remove the LLM Wiki constraint block from agent schema files.

If the file becomes empty after block removal, delete it entirely.
If user content remains, preserve it.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `paths.display_project_path`
2. `paths.display_project_path`
3. `services_schema.require_safe_schema_path`
4. `filesystem_guard.atomic_write_guarded_bytes`
5. `services_schema.encode_managed_document_text`
6. `paths.display_project_path`
7. `filesystem_guard.unlink_guarded_bytes`
8. `paths.display_project_path`
9. `services_schema.ManagedSchemaPathError`
10. `paths.display_project_path`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [paths](../modules/paths.md)
- [services_schema](../modules/services_schema.md)
- [uninstall_cmd](../modules/uninstall_cmd.md)

## Behavior

This workflow starts at `uninstall_cmd._clean_agent_schemas`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
