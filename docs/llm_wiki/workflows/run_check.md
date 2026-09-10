# run_check

**Entry point:** `team_cmd._run_check`
**Modules involved:** [config](../modules/config.md), [extraction_jobs](../modules/extraction_jobs.md), [extraction_service](../modules/extraction_service.md), [infrastructure_inventory](../modules/infrastructure_inventory.md), [team](../modules/team.md), [team_cmd](../modules/team_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `config.validate_path`
3. `team.resolve_team_policy`
4. `team.team_config_issue`
5. `config.validate_path`
6. `team.team_config_issue`
7. `team.TeamConfigError`
8. `extraction_service.get_inventory_result`
9. `extraction_jobs.extraction_job_request_from_args`
10. `extraction_service.get_docker_inventory`
11. `infrastructure_inventory.get_yaml_infrastructure_inventory`
12. `team.build_team_issues`

## Touches

- [config](../modules/config.md)
- [extraction_jobs](../modules/extraction_jobs.md)
- [extraction_service](../modules/extraction_service.md)
- [infrastructure_inventory](../modules/infrastructure_inventory.md)
- [team](../modules/team.md)
- [team_cmd](../modules/team_cmd.md)

## Behavior

This workflow starts at `team_cmd._run_check`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
