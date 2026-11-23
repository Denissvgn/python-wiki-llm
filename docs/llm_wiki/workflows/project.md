# project

**Entry point:** `historical_release._project`
**Modules involved:** [historical_release](../modules/historical_release.md), [infrastructure_state](../modules/infrastructure_state.md), [knowledge_artifacts](../modules/knowledge_artifacts.md), [knowledge_envelope](../modules/knowledge_envelope.md), [knowledge_index](../modules/knowledge_index.md), [knowledge_links](../modules/knowledge_links.md), [section_ownership](../modules/section_ownership.md), [wiki_media](../modules/wiki_media.md)

> Refresh Markdown-derived index facts only. Keep the evaluated source snapshot.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_envelope.hash_markdown_snapshot`
2. `section_ownership.observe_page_sections`
3. `knowledge_artifacts.validated_artifact_bytes`
4. `wiki_media.build_asset_index`
5. `knowledge_index._assemble_knowledge_index`
6. `knowledge_index.KnowledgeIndexInputs`
7. `knowledge_envelope.EvaluatedEnvelope`
8. `infrastructure_state.infrastructure_evidence_by_page`
9. `knowledge_links.collect_link_observations`

## Touches

- [historical_release](../modules/historical_release.md)
- [infrastructure_state](../modules/infrastructure_state.md)
- [knowledge_artifacts](../modules/knowledge_artifacts.md)
- [knowledge_envelope](../modules/knowledge_envelope.md)
- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [section_ownership](../modules/section_ownership.md)
- [wiki_media](../modules/wiki_media.md)

## Behavior

This workflow starts at `historical_release._project`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
