# build_sync_prompt

**Entry point:** `trigger_cmd._build_sync_prompt`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [generate_prompt_cmd](../modules/generate_prompt_cmd.md), [source_snapshot](../modules/source_snapshot.md), [team](../modules/team.md), [trigger_cmd](../modules/trigger_cmd.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `source_snapshot.build_source_snapshot`
2. `extraction_service.get_inventory_result`
3. `extraction_service.print_inventory_failures`
4. `extraction_service.get_call_graph`
5. `team.team_prompt_template_default`
6. `generate_prompt_cmd._build_prompt`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [generate_prompt_cmd](../modules/generate_prompt_cmd.md)
- [source_snapshot](../modules/source_snapshot.md)
- [team](../modules/team.md)
- [trigger_cmd](../modules/trigger_cmd.md)

## Behavior

This workflow starts at `trigger_cmd._build_sync_prompt`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
