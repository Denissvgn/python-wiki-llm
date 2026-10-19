# maintenance_cmd_flow

**Entry point:** `maintenance_cmd.run`
**Modules involved:** [api](../modules/api.md), [config](../modules/config.md), [maintenance_cmd](../modules/maintenance_cmd.md), [request_json](../modules/request_json.md), [sync_recovery](../modules/sync_recovery.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `api.adopt_maintenance`
2. `api.get_maintenance_status`
3. `api.acknowledge_maintenance`
4. `request_json.load_request`
5. `sync_recovery.recover_new_sync_pages`
6. `config.validate_path`
7. `api.recover_maintenance`

## Touches

- [api](../modules/api.md)
- [config](../modules/config.md)
- [maintenance_cmd](../modules/maintenance_cmd.md)
- [request_json](../modules/request_json.md)
- [sync_recovery](../modules/sync_recovery.md)

## Behavior

Dispatches the requested maintenance action and renders its result or structured
error. New-page recovery first enforces the CLI's current-project wiki boundary,
then calls the explicit recovery service with the supplied rejection hash and
dry-run flag. Other actions keep their existing public maintenance API routes.
The generated sequence is a bounded static projection of possible calls, not a
claim that one invocation performs every maintenance operation.
