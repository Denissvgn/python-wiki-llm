# generate_prompt_cmd_flow

**Entry point:** `generate_prompt_cmd.run`
**Modules involved:** [generate_prompt_cmd](../modules/generate_prompt_cmd.md), [metrics](../modules/metrics.md), [path_policy](../modules/path_policy.md), [paths](../modules/paths.md), [secure_file](../modules/secure_file.md), [team](../modules/team.md), [wiki_git_policy](../modules/wiki_git_policy.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `path_policy.validate_path`
2. `path_policy.validate_source_root`
3. `team.team_prompt_template_default`
4. `wiki_git_policy.classify_wiki_git_policy`
5. `metrics.resolve_agent`
6. `metrics.record_event`
7. `secure_file.write_private_text`
8. `metrics.record_event`
9. `paths.shell_quote`

## Touches

- [generate_prompt_cmd](../modules/generate_prompt_cmd.md)
- [metrics](../modules/metrics.md)
- [path_policy](../modules/path_policy.md)
- [paths](../modules/paths.md)
- [secure_file](../modules/secure_file.md)
- [team](../modules/team.md)
- [wiki_git_policy](../modules/wiki_git_policy.md)

## Behavior

This workflow starts at `generate_prompt_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
