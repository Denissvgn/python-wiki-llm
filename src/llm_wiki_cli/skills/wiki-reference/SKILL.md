---
name: wiki-reference
description: Deep reference for llm-wiki extraction contracts, helper toolchains and caches, native availability/freshness, typed graph queries, durable governance and review, safe verification, bounded context/API/MCP consumption, projection-aware Site and Obsidian export, dependency reconciliation, resource-aware execution, and context budgeting. Read only the section that matches the command or diagnostic in front of you.
---

# wiki-reference

Contract-level detail intentionally kept out of the injected agent
instructions (`AGENTS.md` / `CLAUDE.md` / …). Nothing here is part of the
routine sync-then-lint loop; open [reference.md](reference.md) at the section
a task actually needs:

- **Extractor helpers and toolchains** — missing prepared helpers,
  `LLM_WIKI_GO` / `LLM_WIKI_GHC` fallbacks, helper vs inventory cache
  separation, Go test-file inclusion.
- **Haskell extraction contract** — supported GHC toolchain, syntax-only
  guarantees, Cabal reconciliation, the `llm-wiki-extract/v1` inventory schema.
- **Dependency reconciliation** — monorepo manifest scoping, import aliases,
  Go `// indirect`, lockfile-backed `versions` metadata.
- **Knowledge observations and freshness** — the normative native preflight,
  persisted evidence versus read-time freshness, availability/degraded states,
  snapshot-only status, legacy fallback, and authority boundaries.
- **Knowledge lint and context** — strict failure policy, concept refinements,
  typed-relationship refinements, deterministic ranking, warnings, and
  filtered/truncated counts.
- **Knowledge query/API/MCP contract** — exact UID/current-locator/canonical-path/
  persisted-alias lookups, core relationships, typed traversal, analyzer and
  evidence bounds, response envelopes, and service reuse.
- **Durable governance, review, and verification** — opt-in initialization,
  moves and aliases, lifecycle and successors, section-scoped human review,
  explicit machine checks, dry-run/conflict behavior, and ledger recovery.
- **JavaScript and TypeScript flows** — `.js`/`.jsx` extraction, raw Node
  `createServer` entry points, `javascript_flow_unsupported` scope.
- **Static-site and Obsidian export** — ordinary output plus opt-in native
  `summary`, `public-portable`/`internal` privacy profiles, snapshot-only
  freshness, identity corroboration, and the separate body/media review
  boundary.
- **Resource-aware execution** — interactive, isolated-terminal, and controlled
  CI scheduling plus requested/resolved/effective extractor-job semantics.
- **Repository-aware Git handoff** — effective ignore-policy checks,
  conditional commit eligibility, local-only delivery, and fail-closed mixed
  or indeterminate state.
- **`llm-wiki context` for large codebases** — token-budgeted snapshots and
  flag semantics, including the full-inventory cost boundary.
