---
name: wiki-reference
description: Route an LLM Wiki task to one bounded managed contract for maintenance, canonical surfaces, handoff, knowledge, queries, governance, extraction, publishing, or resource-aware execution.
---

# wiki-reference

Open only the topic that matches the task. Each route is one hop from this
file, owns its stated contract, and cannot grant authority that the user,
repository policy, or calling application did not provide.

- [Maintenance and validation](references/maintenance.md) — use after relevant
  code or source changes for owning sync, semantic pass, final re-anchor,
  strict validation, recovery, and handoff ordering.
- [Canonical surfaces and naming](references/surfaces-naming.md) — use before
  editing, naming, linking, or recovering canonical wiki pages and generated
  structures.
- [Repository handoff](references/repository-handoff.md) — use before the first
  wiki write and delivery to classify local-only, conditionally Git-eligible,
  mixed, or indeterminate repository state.
- [Qualified knowledge consumption](references/knowledge-consumption.md) — use
  before interpreting availability, freshness, evidence, ambiguity, bounds, or
  a negative native-knowledge result.
- [Context and query selection](references/context-query.md) — use to choose a
  broad packet, exact query, supplied-path/diff impact, or full-inventory route.
- [Durable knowledge governance](references/governance.md) — use only for an
  explicit adoption, durable identity, alias, lifecycle, review, verification,
  conflict, loss, or recovery operation.
- [Extractors and dependencies](references/extractors-dependencies.md) — use
  for prepared helpers, language analyzers, API/flow observations, dependency
  reconciliation, cache behavior, or unsupported coverage.
- [Publishing projections](references/publishing.md) — use for Site or Obsidian
  export/check, projection profiles, receipts, privacy, or publication review.
- [Resource-aware execution](references/resources-context.md) — use before a
  heavy gate or when diagnosing job concurrency and host-capacity failures.

Claude follows the native installed route at
`.claude/skills/wiki-reference/SKILL.md`. A configured non-Claude agent reads
ordinary Markdown at `.llm-wiki/skills/wiki-reference/SKILL.md`; resolve the
relative links above directly from that installed directory.

`reference.md` is a compatibility index for legacy anchors, not an active
task route. If a required topic is missing or modified, stop only the affected
mutation workflow and restore the complete managed tree. Supported read-only
knowledge/context interfaces may continue with their explicit availability,
bounds, and fallback disclosures.
