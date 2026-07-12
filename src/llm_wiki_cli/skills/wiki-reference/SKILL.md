---
name: wiki-reference
description: Deep reference for llm-wiki extraction contracts (Haskell/Go/Rust/TypeScript/JavaScript), helper toolchains and caches, dependency reconciliation and lockfile metadata, static-site export profiles, resource-aware execution, and `llm-wiki context` budgeting. Read the section that matches the command or diagnostic in front of you — not upfront.
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
- **JavaScript and TypeScript flows** — `.js`/`.jsx` extraction, raw Node
  `createServer` entry points, `javascript_flow_unsupported` scope.
- **Static-site export** — `reference`/`user` profiles, MkDocs and Docusaurus
  output, site checker modes and quality gates.
- **Resource-aware execution** — interactive, isolated-terminal, and controlled
  CI scheduling plus requested/resolved/effective extractor-job semantics.
- **`llm-wiki context` for large codebases** — token-budgeted snapshots and
  flag semantics, including the full-inventory cost boundary.
