# query_documentation

**Entry point:** `api.query_documentation`
**Modules involved:** [api](../modules/api.md), [config](../modules/config.md), [documentation_query_builder](../modules/documentation_query_builder.md), [evidence_explanation](../modules/evidence_explanation.md), [wiki_surface](../modules/wiki_surface.md)

> Dispatch one exact bounded read-only documentation query.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `documentation_query_builder.normalize_supplied_paths`
2. `documentation_query_builder.normalize_concept_coordinate`
3. `config.validate_source_root`
4. `evidence_explanation.explain_source`
5. `evidence_explanation.explanation_provenance`
6. `documentation_query_builder.normalize_concept_coordinate`
7. `wiki_surface.validate_exact_page_coordinate`
8. `documentation_query_builder.normalize_supplied_paths`
9. `documentation_query_builder.normalize_documentation_query_text`

## Touches

- [api](../modules/api.md)
- [config](../modules/config.md)
- [documentation_query_builder](../modules/documentation_query_builder.md)
- [evidence_explanation](../modules/evidence_explanation.md)
- [wiki_surface](../modules/wiki_surface.md)

## Behavior

This workflow starts at `api.query_documentation`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
