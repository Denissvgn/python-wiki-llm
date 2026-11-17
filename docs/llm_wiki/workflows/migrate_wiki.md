# migrate_wiki

**Entry point:** `api.migrate_wiki`
**Modules involved:** [api](../modules/api.md), [host](../modules/host.md), [migrate_runtime](../modules/migrate_runtime.md), [migrate_service](../modules/migrate_service.md)

> Bring a wiki written by an older llm-wiki to the current page naming.

Runs the same migration as ``llm-wiki migrate`` without its console
output. ``chunk_size`` splits the work into reviewable chunks and
``chunk`` applies one of them. Project plugins load only when
``trust_source_plugins`` is true. A wiki the migration cannot read raises
:class:`WorkspaceStateError`; invalid options raise
:class:`InvalidRequestError`.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `migrate_service.MigrateRequest`
2. `host.discarding_output`
3. `migrate_runtime.execute_migrate`

## Touches

- [api](../modules/api.md)
- [host](../modules/host.md)
- [migrate_runtime](../modules/migrate_runtime.md)
- [migrate_service](../modules/migrate_service.md)

## Behavior

This workflow starts at `api.migrate_wiki`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
