# resolve_call

**Entry point:** `extraction_service._resolve_call`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [go_calls](../modules/go_calls.md), [python_calls](../modules/python_calls.md), [python_imports](../modules/python_imports.md)

> Return ``(to_file, to_symbol, kind)`` for a single call record.

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `go_calls.resolve_go_call`
2. `python_calls.resolve_python_call`
3. `python_imports.is_python_source`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [go_calls](../modules/go_calls.md)
- [python_calls](../modules/python_calls.md)
- [python_imports](../modules/python_imports.md)

## Behavior

This workflow starts at `extraction_service._resolve_call`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
