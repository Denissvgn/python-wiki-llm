# wiki-sync compatibility reference

The correctness-critical contracts formerly repeated here now live in the
installed `wiki-reference/references/` topics routed directly from
`SKILL.md`: maintenance, surfaces/naming, governance, extractor/dependency
exceptions, knowledge consumption, resource-aware execution, and repository
handoff. Those managed topics are authoritative and complete; this companion
cannot substitute for a missing or modified dependency.

## Sync output and unattended callers

Plain `sync` emits fixed action prefixes rather than a JSON summary. Use
`CREATE`, `UPDATE`, `METADATA`, `SKIP`, `DEPRECATE`, `RENAME`, `MOVE`, and
`REMOVE` plus the final tally and mechanical `APPEND log.md` row to build the
changed-page inventory. Never parse prose or assume an empty Git diff describes
an ignored wiki.

Plain `sync` also has no lock. An authorized unattended application uses
`llm-wiki trigger-agent` for its lock, timeout, diff/prompt bounds, and circuit
breaker instead of recreating that machinery. `--allow-external-src` and the
configured source-selection profile remain consistent across the entire owning
workflow; the managed maintenance and repository-handoff topics still govern
validation and delivery.

This file remains packaged for compatibility with older installed skill
inventories. It is not an active route and intentionally contains no semantic
surface table, rename procedure, initialization recipe, validation matrix, or
handoff decision table.
