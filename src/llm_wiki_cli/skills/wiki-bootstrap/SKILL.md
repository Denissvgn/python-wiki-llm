---
name: wiki-bootstrap
description: Bootstrap an LLM Wiki for an existing codebase — prepare extractor helpers, run deterministic `llm-wiki bootstrap --format json`, perform a centrality-ranked semantic pass, write an explicit remainder backlog for deferred pages, validate with lint/ci-check, and commit the wiki. Use for first-time wiki creation or an intentional full re-bootstrap; use wiki-sync for incremental post-change updates.
---

# wiki-bootstrap

Create a first useful wiki without pretending every generated page can be hand-polished in one session. The default output is reference-oriented: a complete generated wiki surface for agents, maintainers, and future documentation work, not finished user-facing product docs. The loop is: **prepare helpers → bootstrap → review summary → P0 semantic pages → centrality-ranked P1 pages → remainder backlog → lint/ci-check → commit**. Finish the central pages first, then record the long-tail remainder in a format another agent or human can resume. For user docs, follow this skill with `onboarding-guide` and then `publish-docs` / `site export --profile user --site-name <project>`. See [reference.md](reference.md) for the ranking policy, the remainder-backlog artifact format, validation expectations, and failure modes.

In an `external_agent_docs` run, this skill supplies the deterministic
`bootstrap-source` baseline only. Write the wiki inside the explicit
documentation workspace, leave the source read-only, and hand the worklist to
`wiki-semantic-enhance`; do not perform the target-repository commit steps.
Managed knowledge-base behavior remains the default outside that explicit mode.

## Preconditions

- This is a first bootstrap or an intentional full re-bootstrap. If `<wiki-dir>/.llm-wiki-manifest.json` already exists and the user did not ask for a full regenerate, stop — use the wiki-sync skill instead.
- The target repository is readable and the selected wiki directory (default `docs/llm_wiki`; substitute the project's configured `--wiki-dir` everywhere below) is writable.
- If `--src-dir` points outside the current repository, the run uses `--allow-external-src` for source-reading commands: `prepare-extractors`, `bootstrap`, `lint`, `sync`, `ci-check`, and `team check`. The `--wiki-dir` remains project-root guarded.
- Helper toolchain overrides are captured before preparation (for example `LLM_WIKI_GO=/usr/local/go/bin/go` or `LLM_WIKI_GHC=/path/to/ghc`) when the default executable on `PATH` is broken.
- For `external_agent_docs`, consume the workspace packet/policy rather than
  target instruction files. The packet supplies the workspace wiki path,
  forbidden source root, helper cache, plugin trust, and supervisor-owned gates.

## Steps

1. **Inspect the target shape.** Confirm the repo root, candidate wiki path, source languages, and whether a previous wiki manifest exists. Read the current `index.md` if present so existing custom sections are not destroyed by an accidental overwrite.

2. **Prepare helpers through the CLI.**

   ```bash
   llm-wiki prepare-extractors --src-dir .
   ```

   For an external source root:

   ```bash
   llm-wiki prepare-extractors --src-dir <repo> --allow-external-src
   ```

   Add `--cache-dir` when the project keeps helper binaries separate from the inventory cache. Use documented `LLM_WIKI_GO` / `LLM_WIKI_GHC` overrides when the default toolchain is broken. Do not run npm/go/cargo/ghc helper setup manually. If preparation reports unsupported sources, carry them into the final report/backlog as coverage notices rather than silently treating the wiki as complete for those languages.

3. **Run the deterministic bootstrap.**

   ```bash
   llm-wiki bootstrap --src-dir . --wiki-dir docs/llm_wiki --depth full --format json
   ```

   For FastAPI projects, add `--api-contracts`; when the project already
   exports OpenAPI, add `--openapi-file <source-relative json|yaml>` so the
   declared wire contract is authoritative without importing the application.

   Add `--source-adapter --allow-external-src` only for documented external-source source-adapter workflows. Capture stdout to a log file when practical so the JSON summary can be cited from the remainder backlog.

4. **Triage the JSON summary before semantic editing.** If the summary has `skipped_files`, helper warnings, unsupported-source summaries, or surprising generated counts, resolve those first. `flow_evidence` and `dependency_evidence` preserve bounded detector, route, call/data-flow, boundary-confidence, gap, and topology facts for the supervisor's priority-blind census. They are evidence, not calibrated priorities: do not infer semantic equivalence from preliminary family hints or change the v1 worklist from these fields. Do not spend the semantic budget polishing a wiki that is structurally incomplete because pages were skipped by collisions or helpers failed.

5. **Finish P0 semantic pages first**: the `index.md` introduction, `flows/*` `## Behavior` sections (ordered by entry-point category, then boundary-effect count, then page path), `api-contracts.md`, `dependencies.md`, and `load-order.md` `## Notes`, and obvious high-signal infrastructure/runtime prose. Contract unknowns and reconciliation diagnostics must stay explicit rather than being rewritten as confirmed facts.

6. **Rank remaining module/entity pages by dependency centrality.**

   ```text
   fan_in * 100 + cycle_bonus * 25 + fan_out * 5 + entrypoint_bonus * 20
   ```

   Use `dependencies.metrics.most_depended_on` from the bootstrap summary, or `dependency_neighborhood(<source path>)` when working through MCP/API — do not invent a separate graph. Complete the top 30 by default unless the user gave another budget, and record the exact budget selected for this run.

7. **Edit semantic surfaces only**: entity/module `## Description` prose, flow `## Behavior`, `## Notes`, custom index prose, and backlog/log prose. Never hand-edit generated tables, Mermaid diagrams, `.llm-wiki-manifest.json`, `.llm-wiki-surface.json`, `.llm-wiki-knowledge.json`, extracted row shapes, or `<!-- Auto-generated ... Do not edit by hand. -->` blocks.

8. **Write the remainder backlog.** For every page that still has a placeholder or copied-docstring-only semantic surface after the budget is exhausted, create or update `<wiki-dir>/bootstrap-remainder.md` using the artifact format in [reference.md](reference.md) — stable `WB-YYYYMMDD-NNNN` IDs, status, priority, page, source, rank, reason deferred, suggested context, and acceptance criteria. Link it from a custom trailing `## Bootstrap Remainder` section in `index.md`. The backlog is an explicit deferral, not a failure.

9. **Validate to convergence.**

   ```bash
   llm-wiki lint --strict --profile --src-dir . --wiki-dir docs/llm_wiki
   llm-wiki ci-check --src-dir . --wiki-dir docs/llm_wiki --format json
   llm-wiki team check --src-dir . --wiki-dir docs/llm_wiki   # if team policy is configured
   ```

   Fix broken links, orphan pages, stale manifests, and team-policy failures, then re-run until clean. Dependency cycle/undeclared/unused warnings and unsupported-source notices are diagnostics to document or backlog, not structural lint failures — do not chase every warning (that is the dep-audit workflow).

   For external-source validation, pass `--allow-external-src` to the source
   reader and keep `--wiki-dir` inside the project:

   ```bash
   llm-wiki team check --src-dir <repo> --allow-external-src --wiki-dir docs/llm_wiki
   ```

10. **Review the diff, then commit in managed mode only.** Confirm the final diff contains only generated wiki pages, semantic edits, the remainder backlog, and optional report/log artifacts. Commit the wiki separately from unrelated code changes with a `docs(wiki): bootstrap <project>` style message. Never reuse the hook path's literal `auto-update [bot]` message and never set `LLM_WIKI_AUTO_COMMIT` — both are reserved for the post-commit hook path so it can detect its own commits. In `external_agent_docs`, return the workspace paths and result to the supervisor; never stage or commit the source or adopted input wiki.

## Context budget

Prefer the bootstrap JSON summary, `index.md`, and the surface index (`.llm-wiki-surface.json`) for sizing the pass and mapping source files and symbols to page paths. Use `dependency_neighborhood` only for the page currently being ranked or edited — never query every source path when `dependencies.metrics` already contains the ranking. Reach for `llm-wiki context --budget 8000-12000 --focus all --format json` only after the deterministic bootstrap, when top central pages need more source context than their generated pages provide. Do not use full source dumps for the long tail — backlog those pages with the minimum context needed for a later focused pass.
