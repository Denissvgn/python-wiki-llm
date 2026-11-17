# clean_old_schema

**Entry point:** `upgrade_runtime._clean_old_schema`
**Modules involved:** [filesystem_guard](../modules/filesystem_guard.md), [host](../modules/host.md), [services_schema](../modules/services_schema.md), [upgrade_runtime](../modules/upgrade_runtime.md)

> Clean the source schema and return a receipt for guarded rollback.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `services_schema.classify_managed_schema_block`
2. `services_schema.strip_wiki_block`
3. `services_schema.classify_managed_schema_block`
4. `services_schema.ManagedSchemaBlockError`
5. `services_schema.require_safe_schema_path`
6. `services_schema.encode_managed_document_text`
7. `filesystem_guard.atomic_write_guarded_bytes`
8. `host.emit`
9. `filesystem_guard.unlink_guarded_bytes`
10. `host.emit`
11. `services_schema.ManagedSchemaPathError`

## Touches

- [filesystem_guard](../modules/filesystem_guard.md)
- [host](../modules/host.md)
- [services_schema](../modules/services_schema.md)
- [upgrade_runtime](../modules/upgrade_runtime.md)

## Behavior

This workflow starts at `upgrade_runtime._clean_old_schema`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
