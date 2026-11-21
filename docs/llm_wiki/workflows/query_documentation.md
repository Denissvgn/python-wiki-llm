# query_documentation

**Entry point:** `api.query_documentation`
**Modules involved:** [api](../modules/api.md), [evidence_explanation](../modules/evidence_explanation.md), [path_policy](../modules/path_policy.md), [query_request_format](../modules/query_request_format.md)

> Dispatch one exact bounded read-only documentation query.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `query_request_format.normalize_supplied_paths`
2. `query_request_format.normalize_concept_coordinate`
3. `path_policy.validate_source_root`
4. `evidence_explanation.explain_source`
5. `evidence_explanation.explanation_provenance`
6. `query_request_format.normalize_concept_coordinate`
7. `query_request_format.normalize_supplied_paths`
8. `query_request_format.normalize_documentation_query_text`

## Touches

- [api](../modules/api.md)
- [evidence_explanation](../modules/evidence_explanation.md)
- [path_policy](../modules/path_policy.md)
- [query_request_format](../modules/query_request_format.md)

## Behavior

This workflow starts at `api.query_documentation`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
