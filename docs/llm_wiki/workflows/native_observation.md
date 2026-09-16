# native_observation

**Entry point:** `task_context_v2._native_observation`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md), [task_context_v2](../modules/task_context_v2.md), [workflow_profile](../modules/workflow_profile.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_storage._concept_aliases`
2. `section_ownership.observe_page_sections`
3. `markdown_sections.parse_markdown_document`
4. `workflow_profile.content_id`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)
- [task_context_v2](../modules/task_context_v2.md)
- [workflow_profile](../modules/workflow_profile.md)

## Behavior

Resolves an exact selected concept and emits its concept, semantic-section or related graph observation with snapshot qualifications. Source comparisons can mark stale evidence, but preserved prose is not a semantic approval. Empty or truncated observations cannot prove complete runtime behavior.
