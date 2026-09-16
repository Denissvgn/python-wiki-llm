# validate_selected_record

**Entry point:** `knowledge_storage._validate_selected_record`
**Modules involved:** [knowledge_graph](../modules/knowledge_graph.md), [knowledge_model](../modules/knowledge_model.md), [knowledge_storage](../modules/knowledge_storage.md), [section_ownership](../modules/section_ownership.md)

> Reuse semantic record owners without issuing a whole-bundle verdict.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `knowledge_model._parse_concept`
2. `knowledge_model._parse_relationship`
3. `knowledge_graph._normalise_edge`
4. `section_ownership.validate_section_ownership`
5. `knowledge_model._parse_extensions`

## Touches

- [knowledge_graph](../modules/knowledge_graph.md)
- [knowledge_model](../modules/knowledge_model.md)
- [knowledge_storage](../modules/knowledge_storage.md)
- [section_ownership](../modules/section_ownership.md)

## Behavior

Reuses the existing native record validators for consumed concepts, relationships, graph edges, ownership and extensions. Identity and owner bindings are checked without issuing full-bundle validation authority.
