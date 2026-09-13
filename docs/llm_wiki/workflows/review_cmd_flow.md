# review_cmd_flow

**Entry point:** `review_cmd.run`
**Modules involved:** [change_selection](../modules/change_selection.md), [config](../modules/config.md), [impact](../modules/impact.md), [io](../modules/io.md), [review_cmd](../modules/review_cmd.md), [review_service](../modules/review_service.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `config.validate_source_root`
2. `config.validate_path`
3. `review_service._preflight_review_source_selection`
4. `impact.build_impact`
5. `change_selection.changes_from_args`
6. `io.write_text_output`
7. `impact.render_summary`
8. `io.write_text_output`
9. `impact.render_github`
10. `impact.render_summary`
11. `review_service.build_findings`
12. `change_selection.changes_from_args`

## Touches

- [change_selection](../modules/change_selection.md)
- [config](../modules/config.md)
- [impact](../modules/impact.md)
- [io](../modules/io.md)
- [review_cmd](../modules/review_cmd.md)
- [review_service](../modules/review_service.md)

## Behavior

This workflow starts at `review_cmd.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
