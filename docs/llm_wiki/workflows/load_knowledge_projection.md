# load_knowledge_projection

**Entry point:** `site_cmd._load_knowledge_projection`
**Modules involved:** [knowledge_consumption](../modules/knowledge_consumption.md), [knowledge_projection](../modules/knowledge_projection.md), [site_cmd](../modules/site_cmd.md), [site_export](../modules/site_export.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_consumption.load_knowledge_read_view`
2. `knowledge_projection.project_knowledge`
3. `site_export.SiteExportError`

## Touches

- [knowledge_consumption](../modules/knowledge_consumption.md)
- [knowledge_projection](../modules/knowledge_projection.md)
- [site_cmd](../modules/site_cmd.md)
- [site_export](../modules/site_export.md)

## Behavior

This workflow starts at `site_cmd._load_knowledge_projection`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
