# lint_wiki

**Entry point:** `api.lint_wiki`
**Modules involved:** [api](../modules/api.md), [host](../modules/host.md), [lint_request](../modules/lint_request.md), [lint_service](../modules/lint_service.md)

> Check a wiki against its source tree and return the lint report.

Runs the same checks as ``llm-wiki lint`` without its console output and
returns the JSON-ready report: ``ok``, ``issue_count``, ``issues`` and
``diagnostics``. A failing lint is a result, not an error. Project plugins
run only when ``trust_source_plugins`` is true. Paths outside the
workspace raise :class:`InvalidRequestError`.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `lint_request.LintRequest`
2. `host.discarding_output`
3. `lint_service.execute_lint`
4. `lint_service.report_to_dict`

## Touches

- [api](../modules/api.md)
- [host](../modules/host.md)
- [lint_request](../modules/lint_request.md)
- [lint_service](../modules/lint_service.md)

## Behavior

This workflow starts at `api.lint_wiki`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
