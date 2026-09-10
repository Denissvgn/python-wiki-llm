# validate_builder_link

**Entry point:** `knowledge_index._validate_builder_link`
**Modules involved:** [knowledge_index](../modules/knowledge_index.md), [knowledge_links](../modules/knowledge_links.md), [knowledge_model](../modules/knowledge_model.md), [wiki_media](../modules/wiki_media.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_model.KnowledgeModelError`
2. `knowledge_model.KnowledgeModelError`
3. `knowledge_model.KnowledgeModelError`
4. `knowledge_model.KnowledgeModelError`
5. `knowledge_model.KnowledgeModelError`
6. `wiki_media.contains_uri_authority_userinfo`
7. `knowledge_model.KnowledgeModelError`
8. `wiki_media.normalize_markdown_link_target`
9. `knowledge_model.KnowledgeModelError`
10. `knowledge_model.KnowledgeModelError`
11. `knowledge_links.LinkObservation`
12. `knowledge_model.RelationshipLocation`
13. `knowledge_links.LinkSyntax`
14. `knowledge_model.KnowledgeModelError`
15. `knowledge_model.KnowledgeModelError`
16. `knowledge_model.KnowledgeModelError`
17. `knowledge_model.KnowledgeModelError`
18. `knowledge_model.KnowledgeModelError`
19. `knowledge_model.KnowledgeModelError`
20. `knowledge_model.KnowledgeModelError`
21. `knowledge_model.KnowledgeModelError`
22. `knowledge_model.KnowledgeModelError`

## Touches

- [knowledge_index](../modules/knowledge_index.md)
- [knowledge_links](../modules/knowledge_links.md)
- [knowledge_model](../modules/knowledge_model.md)
- [wiki_media](../modules/wiki_media.md)

## Behavior

This workflow starts at `knowledge_index._validate_builder_link`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
