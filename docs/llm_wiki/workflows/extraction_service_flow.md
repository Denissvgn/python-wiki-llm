# extraction_service_flow

**Entry point:** `extraction_service.run`
**Modules involved:** [extraction_service](../modules/extraction_service.md), [host](../modules/host.md), [io](../modules/io.md), [source_snapshot](../modules/source_snapshot.md)

## Sequence

<!-- Auto-generated static call-chain projection. Reviewed runtime ordering, branching, and side effects belong in Behavior. -->
1. `host.emit`
2. `host.emit`
3. `host.emit`
4. `host.emit`
5. `host.emit`
6. `host.emit`
7. `host.emit`
8. `host.emit`
9. `host.emit`
10. `io.write_text_output`
11. `host.emit`
12. `host.emit`
13. `host.emit`
14. `source_snapshot.format_unsupported_source_summary`
15. `host.emit`
16. `host.emit`
17. `host.emit`
18. `host.emit`

## Touches

- [extraction_service](../modules/extraction_service.md)
- [host](../modules/host.md)
- [io](../modules/io.md)
- [source_snapshot](../modules/source_snapshot.md)

## Behavior

This workflow starts at `extraction_service.run`. The generated sequence is a bounded static projection; runtime ordering, branching, and side effects require source-level confirmation.
