---
name: native-coding
description: Gather qualified source and wiki evidence for an explicitly adopted native coding workflow, then support an authorized source change, bounded follow-ups, durable explanations, and a validated handoff for later resume.
---

# Native coding workflow

Use this recipe when the caller has chosen the native workflow. Loading this
skill does not activate a profile or grant source, command, network, or publication
permissions. The host chooses the profile, workspace roots and context inclusion.

Claude reads `.claude/skills/wiki-reference/references/context-query.md`; other
configured agents read `.llm-wiki/skills/wiki-reference/references/context-query.md`.
Use that installed route for the shared context and query contract.

1. Discover relevant pages with `search_wiki`, then choose exact source, owner,
   occurrence or concept coordinates. Lexical matches are candidates.
2. Use `build_task_context` with observable evidence requirements and the explicit
   profile. Read each requirement's coverage, qualifications and omissions. Use
   `query_documentation` for a bounded exact follow-up. A proposed wider scan still
   needs permission from the host's configured policy.
3. Inspect the relevant source before making the authorized edit. The host owns
   source changes and behavioral verification. Captured structure does not prove
   runtime behavior or that a proposed patch satisfies the task.
4. Read again after saved changes. Session events are hints; request-time source,
   wiki and configuration validation remains necessary. Save or defer unsaved
   buffers. Close sessions on task/workspace changes or cancellation.
5. Preserve the durable reason for the change in an appropriate authored section.
   Use the installed `wiki-reference` maintenance route for an authorized refresh,
   semantic review and re-anchor. `get_maintenance_queue` is advisory.
6. Hand off the explicit request, canonical context identity, known gaps and a
   concise explanation. On resume, validate the retained envelope and rebuild or
   reconcile its on-disk basis before treating it as current.

Use [profile.json](profile.json) as an explicit starting profile. Exact counting
requires a trusted host counter. Count the canonical context text once; MCP,
session metadata and host framing have separate costs. `required` native mode
requires availability; it does not demand positive currentness or approve prose.

Existing context and packet routes remain available. Turn sessions off to use
the same task features through cold reads. No automatic sync, agent configuration,
governance adoption, source execution or publication is part of a provider read.
