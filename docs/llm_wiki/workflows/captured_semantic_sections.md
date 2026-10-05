# captured_semantic_sections

**Entry point:** `maintenance_evidence.captured_semantic_sections`
**Modules involved:** [knowledge_storage](../modules/knowledge_storage.md), [maintenance_evidence](../modules/maintenance_evidence.md), [maintenance_shapes](../modules/maintenance_shapes.md), [markdown_sections](../modules/markdown_sections.md), [section_ownership](../modules/section_ownership.md)

> Exact raw section bytes joined to existing normalized ownership locators.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `maintenance_shapes.MaintenanceError`
2. `maintenance_shapes.MaintenanceError`
3. `maintenance_shapes.MaintenanceError`
4. `section_ownership.observe_page_sections`
5. `markdown_sections.parse_markdown_document`
6. `knowledge_storage.digest`

## Touches

- [knowledge_storage](../modules/knowledge_storage.md)
- [maintenance_evidence](../modules/maintenance_evidence.md)
- [maintenance_shapes](../modules/maintenance_shapes.md)
- [markdown_sections](../modules/markdown_sections.md)
- [section_ownership](../modules/section_ownership.md)

## Behavior

This workflow starts at `maintenance_evidence.captured_semantic_sections`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
