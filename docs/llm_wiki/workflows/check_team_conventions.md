# check_team_conventions

**Entry point:** `team.check_team_conventions`
**Modules involved:** [canonical_pages](../modules/canonical_pages.md), [extraction_service](../modules/extraction_service.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), [io](../modules/io.md), [sync_manifest](../modules/sync_manifest.md), [team](../modules/team.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `sync_manifest.SyncManifest.load`
2. `extraction_service.get_docker_inventory`
3. `infrastructure_inventory.get_yaml_infrastructure_inventory`
4. `canonical_pages.canonical_generated_pages`
5. `io.read_md`

## Touches

- [canonical_pages](../modules/canonical_pages.md)
- [extraction_service](../modules/extraction_service.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [io](../modules/io.md)
- [sync_manifest](../modules/sync_manifest.md)
- [team](../modules/team.md)

## Behavior

This workflow starts at `team.check_team_conventions`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
