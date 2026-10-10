# observe_requirement

**Entry point:** `task_evidence.observe_requirement`
**Modules involved:** [context_packet](../modules/context_packet.md), [implementation_evidence](../modules/implementation_evidence.md), [markdown_sections](../modules/markdown_sections.md), [task_evidence](../modules/task_evidence.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `implementation_evidence.select_implementation_comparison`
2. `markdown_sections.parse_markdown_document`
3. `context_packet._thaw_json`
4. `workflow_profile.content_id`

## Touches

- [context_packet](../modules/context_packet.md)
- [implementation_evidence](../modules/implementation_evidence.md)
- [markdown_sections](../modules/markdown_sections.md)
- [task_evidence](../modules/task_evidence.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

This workflow starts at `task_evidence.observe_requirement`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
